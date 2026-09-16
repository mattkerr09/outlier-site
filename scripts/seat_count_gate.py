#!/usr/bin/env python3
"""No page may name a licence machine count that disagrees with Dodo.

WHY. Every Dodo product's customer-facing activation message said "up to 5
machines" while the product field and the governing entitlement both said 3 —
two machines promised that nobody had bought. A number typed into HTML is a
copy that cannot be re-read, which is how it got there and how it would come
back. The count lives in data/product-facts.json, synced from Dodo by
scripts/sync_product_facts.py; this gate makes the pages agree with it.

⚠️ IT MATCHES THE PROMISE SHAPE, NOT EVERY NUMBER NEAR THE WORD "MAC".
outlier.host says "five Macs instead of five seats" and "Outlier is a one-time
per-Mac tool" — a PRICING comparison (five purchases vs five SaaS seats), not a
claim about one licence. A naive `\\d+ Macs` matcher flags it and teaches the
next person to delete a true sentence to silence a gate. So this looks for:

  * "up to N <machines|Macs|devices|computers>" — the promise shape, and
  * a bare count within CONTEXT_CHARS of "licence"/"license"/"activat"

    python3 scripts/seat_count_gate.py [root]
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
         "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}
DEVICE = r"(?:macs?|machines?|devices?|computers?)"
UP_TO = re.compile(rf"up\s+to\s+(\d+|{'|'.join(WORDS)})\s+{DEVICE}\b", re.I)
BARE = re.compile(rf"\b(\d+|{'|'.join(WORDS)})\s+{DEVICE}\b", re.I)
LICENCE_CTX = re.compile(r"licen[cs]e|activat", re.I)
CONTEXT_CHARS = 90
#: ⚠️ A COUNT ON A COMPARISON PAGE IS USUALLY THE RIVAL'S. The first version of
#: this gate flagged vs/outlier-vs-msty for "Paid licenses cover two devices" —
#: a true sentence about MSTY's licensing, on a page about Msty. A gate that
#: fails on a true statement about someone else teaches people to delete true
#: statements to silence it, which is worse than the drift it guards.
#: So inside the comparison trees a count must be attributable to US: the word
#: Outlier has to appear in the same window. Everywhere else — terms, pricing,
#: FAQ, the home page — an unqualified licence count can only be ours.
COMPARISON_TREES = ("vs/", "best/", "alternatives/")
OURS = re.compile(r"outlier", re.I)
TAGS = re.compile(r"<[^>]+>")


def _n(tok: str) -> int:
    return int(tok) if tok.isdigit() else WORDS[tok.lower()]


def main(root_arg: str = ".") -> int:
    root = pathlib.Path(root_arg).resolve()
    facts_p = root / "data" / "product-facts.json"
    if not facts_p.is_file():
        print(f"FAIL: no {facts_p.relative_to(root)} — run scripts/sync_product_facts.py")
        return 1
    facts = json.loads(facts_p.read_text(encoding="utf-8"))
    seats = facts.get("seats")
    if not isinstance(seats, int) or seats < 1:
        print(f"FAIL: fact file has no usable seat count ({seats!r})")
        return 1
    print(f"seat count from Dodo: {seats}  (read_at {facts.get('read_at')})")

    scanned = wrong = 0
    bad: list[str] = []
    for f in sorted(root.rglob("*.html")):
        text = TAGS.sub(" ", f.read_text(encoding="utf-8", errors="ignore"))
        scanned += 1
        rel = str(f.relative_to(root))
        comparison = rel.startswith(COMPARISON_TREES)

        def ours(m: re.Match) -> bool:
            """On a comparison page the count must be attributable to Outlier."""
            if not comparison:
                return True
            w = text[max(0, m.start() - CONTEXT_CHARS): m.end() + CONTEXT_CHARS]
            return bool(OURS.search(w))

        hits = [(m, True) for m in UP_TO.finditer(text) if ours(m)]
        for m in BARE.finditer(text):
            window = text[max(0, m.start() - CONTEXT_CHARS): m.end() + CONTEXT_CHARS]
            if (LICENCE_CTX.search(window) and ours(m)
                    and not any(h.start() <= m.start() < h.end() for h, _ in hits)):
                hits.append((m, False))
        for m, _explicit in hits:
            got = _n(m.group(1))
            if got != seats:
                wrong += 1
                bad.append(f"  {f.relative_to(root)}: {m.group(0)!r} — Dodo says {seats}")

    # A scan that examined nothing prints exactly what a clean scan prints.
    if scanned < 5:
        print(f"FAIL: only {scanned} page(s) scanned — the gate is not reading the site")
        return 1
    if bad:
        print(f"\nFAIL: {wrong} page(s) name a licence machine count that disagrees with Dodo:")
        print("\n".join(bad))
        print("\n  Fix the PAGE, or fix Dodo and re-run scripts/sync_product_facts.py.")
        print("  Never hand-edit data/product-facts.json.")
        return 1
    print(f"PASS — {scanned} pages scanned, no page contradicts the Dodo seat count")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "."))
