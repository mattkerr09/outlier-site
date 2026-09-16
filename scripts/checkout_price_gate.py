#!/usr/bin/env python3
"""Does the live checkout charge what the site says?

Every price gate here compares one copy of our own number to another: the site
to the app, the app to the fact file. None of them asks the only question a
customer experiences — what the CHECKOUT charges. Docket found its app constant
stale at 19900 against a live 34900 because nothing on the shipped path read it.

This reads https://checkout.dodopayments.com/buy/<product id> with GET and
compares the amount on the page to data/product-facts.json.

⚠️ GET, NEVER HEAD. checkout_link_gate.py documents why with measurements: HEAD
follows the redirect to the provider's homepage and answers 200 for a dead link.
⚠️ GET ONLY, AND NOTHING ELSE. This opens a checkout session and reads it. It
never posts, never fills a field, never touches a payment method.

⚠️ THE MATCH IS ANCHORED, AND THAT IS THE WHOLE DESIGN. A bare-digit substring
once passed $99 against $199 on another product. "249" appears inside "1249",
"2490" and "24900"; "24900" appears inside "249000". Every pattern here is
bounded, and `python3 scripts/checkout_price_gate.py --break-test` runs the
matcher against inputs that MUST NOT match — a gate whose matcher is untested
is a gate that has never been shown capable of failing.

    python3 scripts/checkout_price_gate.py [root]
    python3 scripts/checkout_price_gate.py --break-test
"""
from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys

PRODUCT_ID = "pdt_0Nlgdu1f0s30YekSmpGwA"
CHECKOUT = f"https://checkout.dodopayments.com/buy/{PRODUCT_ID}"
UA = "kerr-ops-price-gate/1"
#: The product must be named on the page, or we are reading someone else's.
EXPECT_NAME = "Outlier"


def price_patterns(cents: int) -> list[re.Pattern]:
    """Anchored ways the same amount can legitimately appear."""
    dollars = cents // 100
    return [
        # (?![\d.]) not (?![\d]): the break-test caught "24900.50" matching,
        # because a trailing dot is not a digit. A gate that accepts 24900.50 as
        # 24900 accepts a hundredfold error.
        re.compile(rf"(?<![\d.]){cents}(?![\d.])"),             # 24900
        re.compile(rf"(?<![\d.])\$?{dollars}\.00(?![\d])"),      # 249.00 / $249.00
        re.compile(rf"(?<![\d.])\${dollars}(?![\d.])"),          # $249
    ]


def _break_test() -> int:
    """The matcher must REFUSE these. Each one is a real near-miss shape."""
    pats = price_patterns(24900)
    must_not = ["1249", "2490", "249000", "$1249", "249.99", "$2490",
                "1249.00", "24900.50", "x24900123"]
    must = ["24900", "249.00", "$249.00", "$249", " 24900 ", "amount:24900"]
    bad = [s for s in must_not if any(p.search(s) for p in pats)]
    missed = [s for s in must if not any(p.search(s) for p in pats)]
    for s in must_not:
        print(f"  must NOT match {s!r:14} -> {'MATCHED ✗' if s in bad else 'refused ok'}")
    for s in must:
        print(f"  must match     {s!r:14} -> {'missed ✗' if s in missed else 'matched ok'}")
    if bad or missed:
        print(f"\nFAIL: matcher wrong on {len(bad)} false positives, {len(missed)} misses")
        return 1
    print("\nPASS — the matcher refuses every near-miss and accepts every real form")
    return 0


def main(argv: list[str]) -> int:
    if "--break-test" in argv:
        return _break_test()
    root = pathlib.Path(argv[0] if argv and not argv[0].startswith("-") else ".").resolve()
    facts_p = root / "data" / "product-facts.json"
    if not facts_p.is_file():
        print(f"FAIL: no {facts_p} — run scripts/sync_product_facts.py")
        return 1
    cents = json.loads(facts_p.read_text(encoding="utf-8"))["price_cents"]

    try:
        out = subprocess.run(
            ["curl", "-sL", "--max-time", "45", "-A", UA, CHECKOUT],
            capture_output=True, text=True, timeout=60).stdout
    except Exception as e:  # noqa: BLE001
        print(f"FAIL: could not read the live checkout ({e}) — not a pass")
        return 1

    # A scan of an empty page prints what a clean scan prints.
    if len(out) < 2000:
        print(f"FAIL: checkout returned {len(out)} bytes — too small to contain a "
              f"price; the gate cannot check and must not report clean")
        return 1
    if EXPECT_NAME.lower() not in out.lower():
        print(f"FAIL: {EXPECT_NAME!r} not on the page — this is not our product")
        return 1

    hits = [p.pattern for p in price_patterns(cents) if p.search(out)]
    if not hits:
        found = sorted(set(re.findall(r"\$ ?\d[\d,]*(?:\.\d{2})?", out)))[:6]
        print(f"FAIL: the live checkout does not show {cents} cents "
              f"(site/fact file says ${cents//100}).")
        print(f"  price-shaped strings on the page: {found or '(none)'}")
        print("  Either the checkout changed and the fact file is stale, or we are "
              "advertising a price nobody is charged.")
        return 1
    print(f"PASS — live checkout charges ${cents//100} "
          f"({len(hits)} of {len(price_patterns(cents))} anchored forms matched)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
