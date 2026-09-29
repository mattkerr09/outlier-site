#!/usr/bin/env python3
"""Does every Buy button on this site still reach a real checkout?

⚠️ 2026-09-29 — THE METHOD CHANGED. Every Buy button now goes through the counting link
(kerr-affiliate-hub /buy/outlier?src=<page>), and a GET of that link MINTS A REAL DODO
CHECKOUT SESSION each time, while a browser user agent is counted as a customer (CEO). So
this gate now sends ONE HEAD per distinct Buy link, redirect NOT followed, as
"kerr-ops/1.0 (checkout_link_gate)", and reads the 303's Location: this product's Dodo buy
link, the thank-you return, and the page's tag. A control (an unknown product → 404) runs
first. The history below explains why a FOLLOWED HEAD proved nothing on Polar; an unfollowed
HEAD reads the redirect itself, which is the thing being checked.

Written 2026-08-18. The site takes money through exactly two Polar links and
nothing checked either of them. A link checker cannot: Polar answers 200 for a
dead link too — see below — so "all links healthy" and "the customer can pay"
are unrelated statements.

WHY HEAD IS FORBIDDEN HERE, measured rather than assumed:

    curl -I  https://checkout.dodopayments.com/buy/polar_cl_jpQY...  ->  200, lands on https://polar.sh/
    curl -L  https://checkout.dodopayments.com/buy/polar_cl_jpQY...  ->  200, 48,436 bytes,
                                     lands on https://polar.sh/checkout/polar_c_NHp3...

HEAD follows the redirect to Polar's HOMEPAGE and reports 200. A retired,
archived or mistyped checkout link would pass a HEAD check exactly as a working
one does. Only GET reaches a checkout session. This gate uses GET.

WHY url_effective IS NOT COMPARED TO THE CONFIGURED LINK. The final URL carries a
per-session id (`polar_c_...`) minted on each request, so it differs every call
and never equals the `polar_cl_...` link id. Asserting equality would fail
permanently on a healthy checkout — a red gate for a correct reason, which is how
gates get switched off.

CONSOLIDATED 2026-08-18. Two overlapping checkout gates existed in this repo at once — both GET, both assert /checkout/, both refuse HEAD, both
refuse to compare url_effective. Two validators for one property is the failure
this repo keeps hitting: they drift, one rots, and the rotted one is the one
somebody trusts. The duplicate was deleted in favour of this file, and its one unique assertion merged in — see the price check below.

THE PRICE CHECK, AND WHY IT READS THE LABEL. This gate proved the door opens and
deferred the amount to ops/bin/checkout-price-gate.py, which lives OUTSIDE this
repo — so within outlier-site the price was unchecked. It now asserts the price
too, read out of EXPECTED's label rather than restated. A price typed twice is
the bug that started this night; the declared set already carried the number.

I MADE THIS GATE LIE, THEN CAUGHT IT. The first merge left the reachability
failure firing whenever `ok` went false, so a price-only mismatch printed
"A customer clicking Buy does not reach a card form" — false: the page loads,
the card form is right there, only the amount is wrong. A gate that misreports
its own finding is exactly the defect class it exists to catch. The two failures
are now distinguished and separately control-tested.

MY FIRST DEAD-LINK CONTROL PROVED NOTHING, which is worth recording because it
looked like it worked. I swapped the token inside this script's EXPECTED, so the
bogus URL appeared on no page and was never fetched. It reported zero card-form
claims and I nearly read that as the fix landing. A control has to exercise the
path it claims to: rebuilt with the dead link actually ON a page in a temp tree,
it then correctly reported unreachable (200, 157,875 bytes, landed on polar.sh/).

WHAT IT CHECKS
  1. the set of checkout links on the site is exactly the DECLARED set, so a
     rotated, removed or newly added link is noticed rather than assumed
  2. each one GETs to a real checkout page. The test that matters is that the
     final URL contains /checkout/ — control-tested, a bogus link id also
     returns 200 and is three times LARGER, because it lands on Polar's
     homepage. Status and size both pass for a dead link; only the path does not.
  3. every occurrence is a plain <a href>. A script-injected href is flagged: if
     the selector ever stops matching, the button silently becomes inert and the
     page still looks perfect. Crisp found exactly that class today.

WHAT IT CANNOT DO. It does not prove a card is charged, and it does not check the
PRICE — ops/bin/checkout-price-gate.py does that against the live Polar product.
Passing here means the door opens, not that the till is right.
"""
from __future__ import annotations

import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import parse_qs, urlparse

#: The checkout links this site is supposed to have. Declared, so that a link
#: quietly disappearing is a failure rather than a smaller number.
#
# MONTHLY REMOVED 2026-08-18. Matthew: "lets not do monthly and only do 249 for
# outlier." The Pro $9/mo tier and its checkout link are gone from the site, so the
# entry for polar_cl_jpQY... is deleted here rather than left to fail — the gate
# correctly caught its disappearance, which is what the "quietly disappearing is a
# failure" rule above is for.
#
# ⚠️ THE POLAR MONTHLY CHECKOUT ITSELF IS STILL LIVE AND STILL CHARGES $9/mo.
# Removing the offer from the site hides the link; it does not close the product.
# Closing it needs Polar access nobody on this machine has, and is with Matthew.

# 2026-08-21: Polar retired. The live Dodo checkout was READ IN A BROWSER before
# this moved -- curl alone would not have proved it, since the page is a JS app
# (the same blindness that made a sibling session report Crisp's Buy button dead).
# Observed rendered: "Kerr and Company LLC", "Outlier - Founders Lifetime $249.00",
# "Includes License Key", a tax-calculating form, and a "Continue to Payment" step.
# Not test mode.
EXPECTED = {
    "pdt_0Nlgdu1f0s30YekSmpGwA": "Lifetime, $249",
}

#: ⚠️ SIZE IS NOT A SIGNAL, and my first version of this gate assumed it was.
#: Control-tested with a bogus link id on 2026-08-18:
#:
#:   real   polar_cl_jpQY...  -> 200,  48,438 b, final https://polar.sh/checkout/polar_c_...
#:   bogus  pdt_thisDoesNotExist... -> 200, 157,875 b, final https://polar.sh/
#:
#: The DEAD link returns three times MORE bytes than the live one, because it
#: lands on Polar's marketing homepage. A `size >= 10_000` floor — which is what
#: this file shipped with for about four minutes — passes a dead checkout
#: happily. It is kept only as a sanity floor against a truncated response and
#: must never be the thing the verdict rests on.
#:
#: THE ONLY DISCRIMINATOR IS THE PATH: a live checkout lands on /checkout/, a
#: dead one lands on the homepage. Status code is 200 either way, so it is
#: useless too.
MIN_BYTES = 10_000


# Dodo lands on /session/cks_<id>; Polar landed on /checkout/polar_c_<id>. Both are
# per-request session urls, so the test is the SHAPE of the landing path, never
# equality with the configured link. Verified in a browser before this changed:
# the Dodo session page renders the order summary, the $249 total, "Includes
# License Key", and a "Continue to Payment" step.
CHECKOUT_PATH = re.compile(r"/(?:checkout|session)/")
LINK = re.compile(r"https://checkout\.dodopayments\.com/buy/(pdt_[A-Za-z0-9_]+)")
HREF = re.compile(r'href\s*=\s*["\']https://checkout\.dodopayments\.com/buy/(pdt_[A-Za-z0-9_]+)')
# 2026-09-29 (CEO): the Buy buttons go through the affiliate worker, which opens a Dodo
# checkout for this product with the founders code applied while seats remain (verified:
# GET lands on checkout.dodopayments.com/session/cks_…, the page names Outlier, shows
# $249 and $124.50, and FOUNDINGOUTLIER). A worker link IS the product's checkout link,
# and it is fetched THROUGH the worker, so a broken worker fails here too.
WORKER_PRODUCT = "pdt_0Nlgdu1f0s30YekSmpGwA"
WORKER = re.compile(r"https://kerr-affiliate-hub\.kerrco\.workers\.dev/buy/outlier\?src=[a-z0-9-]+")
WORKER_HREF = re.compile(r'href\s*=\s*["\'](https://kerr-affiliate-hub\.kerrco\.workers\.dev/buy/outlier\?src=[a-z0-9-]+)')

# 2026-09-29 (CEO): link checks were being COUNTED as customers, and a GET of a /buy link
# mints a real Dodo checkout session every time. So a hub link is checked with HEAD, WITHOUT
# following the redirect, under a user agent that says what we are. The worker answers a
# HEAD with a 303 whose Location is the product's own Dodo buy link, and that Location is
# the whole door: the right product, the thank-you return, and the page's src tag carried
# through. Nothing is minted and nothing is counted. The PRICE is no longer read here (that
# would take a GET); a separate price check reads it from the live product.
HUB_UA = {"User-Agent": "kerr-ops/1.0 (checkout_link_gate)"}
THANK_YOU = "https://outlier.host/thank-you.html"
CONTROL_URL = "https://kerr-affiliate-hub.kerrco.workers.dev/buy/nosuchproduct-control?src=ops-gate-control"


class _NoFollow(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


_OPENER = urllib.request.build_opener(_NoFollow)


def head_no_follow(url: str) -> tuple[int, str]:
    """(status, Location) for one HEAD, redirects NOT followed. (0, '') if it could not be made."""
    req = urllib.request.Request(url, method="HEAD", headers=HUB_UA)
    try:
        with _OPENER.open(req, timeout=30) as r:
            return r.status, r.headers.get("Location", "") or ""
    except urllib.error.HTTPError as e:
        return e.code, (e.headers.get("Location", "") if e.headers else "") or ""
    except Exception:
        return 0, ""


def pages(root: Path):
    for f in sorted(root.rglob("*.html")):
        if ".pre" in f.name or "_seo_build" in f.parts:
            continue
        yield f


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    failures: list[str] = []

    found: dict[str, list[str]] = {}
    as_href: set[str] = set()
    bare: dict[str, list[str]] = {}
    worker_urls: dict[str, set[str]] = {}
    for f in pages(root):
        text = f.read_text(encoding="utf-8", errors="replace")
        rel = f.relative_to(root).as_posix()
        for m in LINK.finditer(text):
            found.setdefault(m.group(1), []).append(f.name)
            bare.setdefault(m.group(1), []).append(rel)
        for m in HREF.finditer(text):
            as_href.add(m.group(1))
        for m in WORKER.finditer(text):
            found.setdefault(WORKER_PRODUCT, []).append(f.name)
        for m in WORKER_HREF.finditer(text):
            as_href.add(WORKER_PRODUCT)
            worker_urls.setdefault(WORKER_PRODUCT, set()).add(m.group(1))

    print(f"  {len(found)} distinct checkout link(s) across {len(list(pages(root)))} page(s)\n")

    # THE CONTROL FIRST: a product the worker does not sell must NOT come back as a door to
    # Dodo, or a 303 below proves nothing.
    c_status, c_loc = head_no_follow(CONTROL_URL)
    if c_status == 0:
        print("FAIL: the control HEAD could not be made at all — network or worker problem.")
        return 1
    if c_status in (301, 302, 303, 307, 308) and "checkout.dodopayments.com" in c_loc:
        print(f"FAIL: the control (an unknown product) answered {c_status} → {c_loc}.")
        print("      The worker sends anything to a checkout, so a 303 cannot prove a Buy link works.")
        return 1
    print(f"  control (unknown product) -> {c_status}  ✓ a wrong link really does fail\n")

    for link_id, where in sorted(found.items()):
        label = EXPECTED.get(link_id, "UNDECLARED")
        # 3. plain href, not script-injected
        injected = "" if link_id in as_href else "  <-- NOT a plain <a href>"
        if link_id not in as_href:
            failures.append(
                f"    {link_id[:26]}... appears but never as a plain <a href>. If it is "
                f"injected by a selector, the button goes inert the moment the selector "
                f"stops matching and the page still looks perfect.")
        # 2. Every Buy button goes through the counting link (CEO 2026-09-28): a bare Dodo
        #    link is a Buy button nobody counts, and fetching one would mint a session.
        if bare.get(link_id):
            where_bare = ", ".join(sorted(set(bare[link_id]))[:5])
            failures.append(
                f"    {label} ({link_id[:26]}...): a bare Dodo link on {where_bare} — route it "
                f"through /buy/outlier?src=<page> (python3 scripts/wrap_counting_links.py).")
        urls = sorted(worker_urls.get(link_id, set()))
        if not urls:
            print(f"  {label:16s} {link_id[:26]}...  no counting Buy link  x{len(where)}{injected}")
            failures.append(f"    {label} ({link_id[:26]}...): no counting Buy link carries it.")
            continue
        # 3. HEAD each distinct counting link; the 303's Location is the door.
        for url in urls:
            status, loc = head_no_follow(url)
            src = parse_qs(urlparse(url).query).get("src", [""])[0]
            lu = urlparse(loc) if loc else None
            lq = parse_qs(lu.query) if lu else {}
            door = (status == 303 and lu is not None and lu.netloc == "checkout.dodopayments.com"
                    and lu.path == f"/buy/{link_id}")
            back = lq.get("redirect_url", [""])[0] == THANK_YOU
            tag = lq.get("metadata_src", [""])[0] == src
            print(f"  {label:16s} src={src:10s} HEAD {status} -> "
                  f"{(lu.netloc + lu.path) if lu else 'no Location'}  "
                  f"return={'thank-you' if back else 'WRONG'}  tag={'kept' if tag else 'LOST'}"
                  f"  x{len(where)}{injected}")
            if not door:
                failures.append(
                    f"    {label} (src={src}): HEAD answered {status} -> {loc or 'no Location'}. "
                    f"A customer clicking Buy does not reach this product's Dodo checkout.")
                continue
            if not back:
                failures.append(
                    f"    {label} (src={src}): the checkout returns to "
                    f"{lq.get('redirect_url', ['nothing'])[0]}, not {THANK_YOU} — the buyer "
                    f"dead-ends after paying.")
            if not tag:
                failures.append(
                    f"    {label} (src={src}): the page tag did not reach the checkout "
                    f"(metadata_src={lq.get('metadata_src', [''])[0]!r}) — the sale cannot be "
                    f"traced to the page.")

    # 1. declared set
    for missing in sorted(set(EXPECTED) - set(found)):
        print(f"  MISSING          {missing[:26]}...  ({EXPECTED[missing]})")
        failures.append(
            f"    {EXPECTED[missing]} ({missing[:26]}...) is declared but appears on NO page. "
            f"Either it was removed on purpose — update EXPECTED — or a Buy button vanished.")
    for extra in sorted(set(found) - set(EXPECTED)):
        failures.append(
            f"    {extra[:26]}... is on the site but not declared here. A checkout nobody "
            f"declared is a checkout nobody is checking the price of.")

    print()
    if failures:
        print(f"FAIL: {len(failures)} checkout problem(s).")
        for f in failures:
            print(f)
        print("\n  Hub links are checked with HEAD and the redirect NOT followed: a GET of /buy")
        print("  mints a real Dodo checkout session, and a browser user agent is counted as a")
        print("  customer. The 303's Location names the product, the return page and the tag.")
        return 1

    print(f"OK: {len(found)} checkout link(s); every Buy button goes through the counting link,")
    print("and the worker's 303 lands on this product's Dodo checkout, returns to the thank-you")
    print("page and carries the page's tag. Nothing was minted or counted (HEAD, kerr-ops UA).")
    print("The price is checked separately, against the live product.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
