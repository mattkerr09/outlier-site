#!/usr/bin/env python3
"""A table that prices someone else must cite where that price came from.

Measured 2026-09-08: 45 pages put a money figure in a comparison table attributed to
someone other than Outlier, and 24 of them cite no vendor pricing page anywhere on the
page. What that looks like:

    learn/cloud-ai-vs-local-ai-cost/   ChatGPT Plus | $20 | $480
                                       Claude Pro   | $20 | $480
                                       ChatGPT Pro  | from $100 | from $2,400
    vs/outlier-vs-notebooklm/          Gemini Notebook Paid | $4.99 / $19.99 / $99.99+

Those are other companies' prices, stated as fact, sourced to nothing. They are the
figures most likely to go quietly wrong -- a rival changes its price and our page keeps
asserting the old one with no link a reader (or we) can check it against.

ATTRIBUTION IS STRUCTURAL, NOT PROXIMITY. A first attempt looked for a vendor's name
within 160 characters of a money figure. It produced 571 findings across 146 pages and
was worthless: "Apple silicon" sits near a price on nearly every page of this site, and
x.ai's domain label is the single letter "x". Being NEAR a name is not being ABOUT it.
A table cell is different -- the row header and column header ARE the claim about what
the number means, written by us, in markup. So this gate reads tables and nothing else.

Both orientations count, because the site uses both. cloud-ai-vs-local-ai-cost puts the
vendor in the ROW ("ChatGPT Plus | $20 | $480", columns are Monthly / 24-month total)
while outlier-vs-notebooklm puts it in the COLUMN. Assuming one orientation would have
missed 21 cells on the worst page and read its "Monthly" header as a vendor.

WHY THE REQUIREMENT IS PAGE-LEVEL. The honest check would be per-vendor: ChatGPT's
price cites openai.com. That needs a product-name -> domain table ("ChatGPT" ->
openai.com, "Grok" -> x.ai, "Copilot" -> two different companies), and a table like
that is typed by hand, silently rots, and cannot be derived from anything here. So the
requirement is the one that can be checked without inventing data: a page pricing
someone else must cite at least one vendor pricing URL. It is weaker per-figure and
still catches every page sourcing rival prices to nothing.

The site already carries 25 vendor pricing URLs across its better pages, so a fix never
needs a URL anyone invents -- take the one another page already vetted.

RATCHET. The 24 pages are baselined; only NEW ones fail. Edit BY REMOVAL ONLY.

    python3 scripts/rival_price_source_gate.py              # check
    python3 scripts/rival_price_source_gate.py <root>       # aim it
    python3 scripts/rival_price_source_gate.py --self-check # prove it can fail
"""
from __future__ import annotations

import html
import json
import os
import re
import sys

BASELINE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "rival_price_source_baseline.json")
MIN_TABLES = 20          # vacuity guard

MONEY = re.compile(r"\$\d[\d,]*(?:\.\d\d)?")
OURS = re.compile(r"(?i)\boutlier\b")
PRICING_URL = re.compile(r"(?i)/(pricing|plans?|buy|subscribe|upgrade|billing)")
#: Header words that name a FIELD rather than a vendor. A header like "Monthly" means
#: the vendor is on the other axis; treating it as a vendor is how a first pass read
#: "24-month total" as a company.
FIELD = re.compile(r"(?i)^\s*(monthly|yearly|annual|price|cost|per month|per year|"
                   r"\d+-month total|total|plan|subscription|tier|cloud plan|what|"
                   r"feature|limit|notes?)\b")


def _cells(row: str) -> list[str]:
    return [html.unescape(re.sub(r"<[^>]+>", " ", c)).strip()
            for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, re.S | re.I)]


def survey(site_root: str = "."):
    """(page, [(entity, cell)]) for every money cell attributed to a non-Outlier entity."""
    out, tables = {}, 0
    for root, _d, files in os.walk(site_root):
        if any(x in root for x in (".git", "_seo_build", "scripts", "node_modules")):
            continue
        for f in sorted(files):
            if not f.endswith(".html") or ".pre" in f:
                continue
            path = os.path.join(root, f)
            rel = os.path.relpath(path, site_root)
            raw = open(path, encoding="utf-8", errors="replace").read()
            cited = [u for u in re.findall(r'href="(https?://[^"]+)"', raw)
                     if "outlier.host" not in u and PRICING_URL.search(u)]
            found = []
            for tbl in re.findall(r"<table.*?</table>", raw, re.S | re.I):
                rows = re.findall(r"<tr.*?</tr>", tbl, re.S | re.I)
                if not rows:
                    continue
                tables += 1
                head = _cells(rows[0])
                for r in rows[1:]:
                    cs = _cells(r)
                    if not cs:
                        continue
                    for i, c in enumerate(cs):
                        if not MONEY.search(c):
                            continue
                        col = head[i] if i < len(head) else ""
                        row_h = cs[0]
                        # the vendor is whichever header is not a field name
                        entity = col if (col and not FIELD.match(col)) else row_h
                        if not entity or OURS.search(entity) or FIELD.match(entity):
                            continue
                        found.append((entity[:40], c[:40]))
            if found:
                out[rel] = (found, cited)
    return out, tables


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    site_root = args[0] if args else "."

    if "--self-check" in sys.argv:
        assert FIELD.match("24-month total") and FIELD.match("Monthly"), \
            "self-check: a field header reads as a vendor"
        assert not FIELD.match("ChatGPT Plus") and not FIELD.match("Gemini Notebook Paid"), \
            "self-check: a vendor header reads as a field"
        assert OURS.search("Outlier Pro") and not OURS.search("Claude Pro"), \
            "self-check: cannot tell our column from theirs"
        assert PRICING_URL.search("https://openai.com/chatgpt/pricing") and \
            not PRICING_URL.search("https://openai.com/index/hello-gpt-4o/"), \
            "self-check: pricing-URL test does not discriminate"
        print("self-check: vendor headers, field headers, our column and a pricing URL "
              "are each told apart. OK")

    found, tables = survey(site_root)
    if tables < MIN_TABLES:
        print(f"FAIL: only {tables} table(s) under {site_root!r}, expected at least "
              f"{MIN_TABLES}.")
        print("      A gate that read no tables prints the same word as a clean one.")
        return 1

    bare = {p: v for p, (v, cited) in found.items() if not cited}
    baseline = json.load(open(BASELINE)) if os.path.exists(BASELINE) else {}
    new = {p: v for p, v in bare.items() if p not in baseline}

    print(f"rival_price_source_gate: {tables} tables; {len(found)} page(s) price a "
          f"non-Outlier entity; {len(bare)} cite no vendor pricing URL")
    print(f"rival_price_source_gate: {len(baseline)} baselined, not enforced")

    if new:
        print(f"\nFAIL ({len(new)} new):")
        for p, v in sorted(new.items())[:8]:
            ex = "; ".join(f"{e} = {c}" for e, c in v[:2])
            print(f"  {p}: prices {len(v)} non-Outlier cell(s) — {ex}")
            print("       and cites no vendor pricing page. That is another company's")
            print("       price stated as fact with nothing to check it against. Take a")
            print("       URL another page here already vetted rather than inventing one.")
        return 1
    print("\nPASS — every page pricing someone else cites where the price came from.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
