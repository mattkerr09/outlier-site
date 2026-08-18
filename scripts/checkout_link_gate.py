#!/usr/bin/env python3
"""Does every Buy button on this site still reach a real checkout?

Written 2026-08-18. The site takes money through exactly two Polar links and
nothing checked either of them. A link checker cannot: Polar answers 200 for a
dead link too — see below — so "all links healthy" and "the customer can pay"
are unrelated statements.

WHY HEAD IS FORBIDDEN HERE, measured rather than assumed:

    curl -I  https://buy.polar.sh/polar_cl_jpQY...  ->  200, lands on https://polar.sh/
    curl -L  https://buy.polar.sh/polar_cl_jpQY...  ->  200, 48,436 bytes,
                                     lands on https://polar.sh/checkout/polar_c_NHp3...

HEAD follows the redirect to Polar's HOMEPAGE and reports 200. A retired,
archived or mistyped checkout link would pass a HEAD check exactly as a working
one does. Only GET reaches a checkout session. This gate uses GET.

WHY url_effective IS NOT COMPARED TO THE CONFIGURED LINK. The final URL carries a
per-session id (`polar_c_...`) minted on each request, so it differs every call
and never equals the `polar_cl_...` link id. Asserting equality would fail
permanently on a healthy checkout — a red gate for a correct reason, which is how
gates get switched off.

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
import urllib.request
from pathlib import Path

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"}

#: The checkout links this site is supposed to have. Declared, so that a link
#: quietly disappearing is a failure rather than a smaller number.
EXPECTED = {
    "polar_cl_jpQYwPwQEvX2zBw10oD2KfKP9yYTcn59JShy82GiJom": "Pro, $9/mo",
    "polar_cl_9tPoCY5d2jVaRY7aU7DOH9pd3lV5kelZatIzJ2tZH6h": "Lifetime, $249",
}

#: ⚠️ SIZE IS NOT A SIGNAL, and my first version of this gate assumed it was.
#: Control-tested with a bogus link id on 2026-08-18:
#:
#:   real   polar_cl_jpQY...  -> 200,  48,438 b, final https://polar.sh/checkout/polar_c_...
#:   bogus  polar_cl_thisDoesNotExist... -> 200, 157,875 b, final https://polar.sh/
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

LINK = re.compile(r"https://buy\.polar\.sh/(polar_cl_[A-Za-z0-9_]+)")
HREF = re.compile(r'href\s*=\s*["\']https://buy\.polar\.sh/(polar_cl_[A-Za-z0-9_]+)')


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
    for f in pages(root):
        text = f.read_text(encoding="utf-8", errors="replace")
        for m in LINK.finditer(text):
            found.setdefault(m.group(1), []).append(f.name)
        for m in HREF.finditer(text):
            as_href.add(m.group(1))

    print(f"  {len(found)} distinct checkout link(s) across {len(list(pages(root)))} page(s)\n")

    for link_id, where in sorted(found.items()):
        label = EXPECTED.get(link_id, "UNDECLARED")
        # 3. plain href, not script-injected
        injected = "" if link_id in as_href else "  <-- NOT a plain <a href>"
        if link_id not in as_href:
            failures.append(
                f"    {link_id[:26]}... appears but never as a plain <a href>. If it is "
                f"injected by a selector, the button goes inert the moment the selector "
                f"stops matching and the page still looks perfect.")
        # 2. GET to a real checkout
        try:
            r = urllib.request.urlopen(
                urllib.request.Request(f"https://buy.polar.sh/{link_id}", headers=UA), timeout=30)
            body = r.read()
            final, status, size = r.geturl(), r.status, len(body)
        except Exception as exc:
            print(f"  {label:16s} {link_id[:26]}...  GET FAILED: {exc}")
            failures.append(f"    {label} ({link_id[:26]}...): checkout unreachable — {exc}")
            continue

        ok = 200 <= status < 300 and "/checkout/" in final and size >= MIN_BYTES
        print(f"  {label:16s} {link_id[:26]}...  {status}  {size:,}b  "
              f"{'checkout' if '/checkout/' in final else 'NOT a checkout page'}"
              f"  x{len(where)}{injected}")
        if not ok:
            failures.append(
                f"    {label} ({link_id[:26]}...): GET returned {status}, {size} bytes, "
                f"landed on {final}. A customer clicking Buy does not reach a card form.")

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
        print("\n  Test with GET, never HEAD: HEAD follows to polar.sh/ and answers 200 for a")
        print("  dead link. And never assert the final URL equals the configured one — the")
        print("  checkout session id is minted per request.")
        return 1

    print(f"OK: {len(found)} checkout link(s), each reaching a real Polar checkout page.")
    print("This proves the door opens, not that the till is right — ops/bin/checkout-price-gate.py")
    print("checks the amount against the live product.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
