#!/usr/bin/env python3
"""Does the live checkout charge what the site says?

Every price gate here compares one copy of our own number to another: the site
to the app, the app to the fact file. None of them asks the only question a
customer experiences — what the CHECKOUT charges. Docket found its app constant
stale at 19900 against a live 34900 because nothing on the shipped path read it.

This reads https://checkout.dodopayments.com/buy/<product id> with GET and
compares the amount on the page to data/product-facts.json and the dated
FOUNDINGOUTLIER offer in data/founding_offer.json. Before the offer ends, the
fact-file price and sale price are allowed. From the end on, only the stated
post-sale price is allowed.

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

import datetime as dt
import json
import pathlib
import re
import subprocess
import sys
import time

PRODUCT_ID = "pdt_0Nlgdu1f0s30YekSmpGwA"
CHECKOUT = f"https://checkout.dodopayments.com/buy/{PRODUCT_ID}"
UA = "kerr-ops-price-gate/1"
#: The product must be named on the page, or we are reading someone else's.
EXPECT_NAME = "Outlier"


def price_patterns(cents: int) -> list[re.Pattern]:
    """Anchored ways the same amount can legitimately appear."""
    dollars, fraction = divmod(cents, 100)
    patterns = [
        # (?![\d.]) not (?![\d]): the break-test caught "24900.50" matching,
        # because a trailing dot is not a digit. A gate that accepts 24900.50 as
        # 24900 accepts a hundredfold error.
        re.compile(rf"(?<![\d.]){cents}(?![\d.])"),             # 24900
        re.compile(rf"(?<![\d.])\$?{dollars}\.{fraction:02d}(?![\d.])"),  # 16.99 / $16.99
    ]
    if fraction == 0:
        patterns.append(re.compile(rf"(?<![\d.])\${dollars}(?![\d.])"))  # $249
    return patterns


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


def accepted_prices(root: pathlib.Path, cents: int, now: float) -> dict[int, str]:
    """Read the offer strictly: missing price data must never widen the check."""
    offer_p = root / "data" / "founding_offer.json"
    try:
        data = json.loads(offer_p.read_text(encoding="utf-8"))
        ends = dt.datetime.fromisoformat(data["ends"].replace("Z", "+00:00"))
        if ends.tzinfo is None:
            raise ValueError("ends must include a timezone")
        offer = next(o for o in data["offers"] if o["code"] == "FOUNDINGOUTLIER")
        prices = offer["prices"]
        if not isinstance(prices, list) or not all(isinstance(p, str) for p in prices):
            raise ValueError("FOUNDINGOUTLIER prices must be a list of strings")
        sale = re.search(r"\$(\d+)\.(\d{2})(?![\d.])", " ".join(prices))
        if not sale:
            raise ValueError("FOUNDINGOUTLIER prices has no $N.NN sale price")
        after = re.search(r"\bThen\s+\$(\d+)(?:\.(\d{2}))?(?!\d|\.\d)", offer["what"])
        if not after:
            raise ValueError("FOUNDINGOUTLIER what has no parseable Then $N price")
        sale_cents = int(sale[1]) * 100 + int(sale[2])
        after_cents = int(after[1]) * 100 + int(after[2] or "0")
    except (OSError, ValueError, KeyError, TypeError, AttributeError, StopIteration) as e:
        raise ValueError(f"cannot read FOUNDINGOUTLIER offer in {offer_p}: {str(e) or 'offer missing'}") from e
    if now < ends.timestamp():
        return {cents: "product-facts price before the offer ends",
                sale_cents: "FOUNDINGOUTLIER sale price before the offer ends"}
    return {after_cents: "FOUNDINGOUTLIER stated post-sale price from the offer end on"}


def fetch_checkout() -> str:
    """GET only: read the checkout without submitting anything."""
    return subprocess.run(
        ["curl", "-sL", "--max-time", "45", "-A", UA, CHECKOUT],
        capture_output=True, text=True, timeout=60).stdout


def main(argv: list[str], *, now: float | None = None) -> int:
    """Use the real clock unless a test supplies an epoch timestamp as now."""
    if "--break-test" in argv:
        return _break_test()
    root = pathlib.Path(argv[0] if argv and not argv[0].startswith("-") else ".").resolve()
    facts_p = root / "data" / "product-facts.json"
    if not facts_p.is_file():
        print(f"FAIL: no {facts_p} — run scripts/sync_product_facts.py")
        return 1
    cents = json.loads(facts_p.read_text(encoding="utf-8"))["price_cents"]
    try:
        amounts = accepted_prices(root, cents, time.time() if now is None else now)
    except ValueError as e:
        print(f"FAIL: {e}")
        return 1

    try:
        out = fetch_checkout()
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

    for amount, reason in amounts.items():
        patterns = price_patterns(amount)
        hits = [p.pattern for p in patterns if p.search(out)]
        if hits:
            print(f"PASS: live checkout charges ${amount//100}.{amount%100:02d}, "
                  f"{amount} cents: {reason}; "
                  f"{len(hits)} of {len(patterns)} anchored forms matched")
            return 0
    found = sorted(set(re.findall(r"\$ ?\d[\d,]*(?:\.\d{2})?", out)))[:6]
    print(f"FAIL: the live checkout does not show an accepted amount: {amounts}")
    print(f"  price-shaped strings on the page: {found or '(none)'}")
    print("  The checkout must charge a price the site states for this time.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
