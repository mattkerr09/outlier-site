#!/usr/bin/env python3
"""Every checkout link on the site must reach a real checkout, at the real price.

Written 2026-08-18 after Crisp shipped five buttons pointing at the free DMG
while its paywall was live — the paid button charged nobody. outlier-site does
NOT have Crisp's worst failure mode: its hrefs are literal in the anchor, not
injected by a script selecting on a data- attribute (an injector whose selector
matches nothing yields an empty NodeList, no error, no console output, and a
dead button). Keeping the href literal is the safer wiring and this gate is the
cheaper guard, so the links were deliberately NOT consolidated behind a script.

WHY STATUS CODES ARE USELESS HERE — verified, not assumed:

    curl -sL https://buy.polar.sh/polar_cl_totallyNotARealCheckoutToken123
    -> HTTP 200

A completely invented checkout token returns 200. Polar redirects an unknown
token to its marketing homepage, which is a perfectly healthy 200 page. Any gate
asserting "the checkout link returns 200" passes on a link that charges nobody.

Worse, that homepage contains "$20" — a RETIRED Outlier price. So a naive
"does our price appear" check passes on the dead page too, and a naive
"no retired price appears" check FAILS on it for the wrong reason.

THE TWO CONDITIONS THAT ACTUALLY DISCRIMINATE:
  1. after following redirects, url_effective is on the /checkout/ path
     (a dead token lands on https://polar.sh/ instead), AND
  2. the expected price appears on that checkout page.

Note (1) is NOT "url_effective equals the configured link" — buy.polar.sh/
polar_cl_… legitimately resolves to polar.sh/checkout/polar_c_…, a different
token entirely. Asserting equality would fail on every healthy checkout.

Use GET, never HEAD: `curl -I` on these 302s to the Polar homepage.

    python3 scripts/checkout_gate.py
"""
from __future__ import annotations

import re
import sys
import urllib.request
from pathlib import Path

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120"
LINK_RE = re.compile(r"https://buy\.polar\.sh/[A-Za-z0-9_]+")

#: What the site sells. A checkout must carry exactly one of these.
EXPECTED_PRICES = {"$9", "$249"}
#: Prices we no longer charge. Only meaningful ON a real checkout page.
RETIRED = ("$20", "$149", "$99", "$39", "$200")

#: Below this, assume the scan broke rather than that the site stopped selling.
MIN_LINKS = 2


def fetch(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=45) as r:
        return r.geturl(), r.read().decode("utf-8", "replace")


def main(root_arg: str = ".") -> int:
    root = Path(root_arg)
    links = sorted({
        m for p in root.rglob("*.html") if ".git" not in p.parts
        for m in LINK_RE.findall(p.read_text(encoding="utf-8", errors="ignore"))
    })
    print(f"distinct checkout links found: {len(links)}")

    if len(links) < MIN_LINKS:
        print(f"\nFAIL: found {len(links)} checkout links, expected >= {MIN_LINKS}.")
        print("      The scan is more likely broken than the site. Not reporting clean.")
        return 1

    fails, seen_prices = [], set()
    for url in links:
        try:
            effective, body = fetch(url)
        except Exception as e:
            fails.append(f"{url}\n       could not be fetched: {e}")
            continue

        on_checkout = "/checkout/" in effective
        prices = {p for p in EXPECTED_PRICES if re.search(rf"{re.escape(p)}(?!\d)", body)}
        retired = [r for r in RETIRED if on_checkout and re.search(rf"{re.escape(r)}(?!\d)", body)]

        status = "ok" if (on_checkout and len(prices) == 1 and not retired) else "FAIL"
        print(f"  [{status}] {url}")
        print(f"         -> {effective}")
        print(f"         price on page: {sorted(prices) or 'NONE'}")

        if not on_checkout:
            fails.append(f"{url}\n       redirected OFF the checkout path to {effective}\n"
                         f"       (this is what a dead/unknown checkout token does — and it still returns 200)")
        elif len(prices) != 1:
            fails.append(f"{url}\n       expected exactly one of {sorted(EXPECTED_PRICES)} "
                         f"on the checkout page, found {sorted(prices) or 'none'}")
        else:
            seen_prices |= prices
        if retired:
            fails.append(f"{url}\n       RETIRED price {retired} is on the live checkout page")

    if not fails and seen_prices != EXPECTED_PRICES:
        fails.append(f"the site's checkouts cover {sorted(seen_prices)} but should cover "
                     f"{sorted(EXPECTED_PRICES)} — a plan is missing or mispriced")

    if fails:
        print(f"\nFAIL ({len(fails)}):")
        for f in fails:
            print(f"  {f}")
        return 1
    print(f"\nPASS — {len(links)} checkouts reach a real checkout page, covering {sorted(seen_prices)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "."))
