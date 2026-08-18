#!/usr/bin/env python3
"""Performance figures on the page must match seo/_data/models.csv.

The page and its own data file drifted apart without anyone noticing, and the
drift ran in the flattering direction on the one that matters:

    tier     models.csv        index.html
    plus     1.59 tok/s        2.1 tok/s      <- page is 32% FASTER than the data
    quick    14.6 tok/s        "Not measured" <- page is more conservative
    vision   (blank)           16.31 tok/s    <- page has a figure the data lacks

Plus is the serious one. benchmarks.csv records K_SWEEP_RESULTS at 1.31/1.55/
1.59/1.61 tok/s across K=4/20/32/48, models.csv carries 1.59, and
docs/v11_engine_modes.md reports 1.67 for the V9 stable default. Nothing measured
is 2.1. The page is publishing the best of several conflicting runs, which is the
failure this site exists to argue against — a figure a reader cannot reproduce.

WHY THIS IS A GATE AND NOT A CORRECTION. Which run is authoritative is not mine
to decide: 1.59, 1.67 and 2.1 all claim M1 Ultra and V9, so picking one silently
would replace an unsourced number with a differently-unsourced number. The
conflict is recorded in CONFLICTS below, where it is visible in code and in CI
output, until someone who owns the measurement resolves it.

    python3 scripts/figure_provenance_gate.py
"""
from __future__ import annotations

import csv
import html
import re
import sys
from pathlib import Path

#: Known, deliberate divergences. Each needs a reason and, where it exists, the
#: conflicting sources — so an exception cannot be added without stating its case.
CONFLICTS = {
    ("plus", "toks"): (
        "page says 2.1, models.csv 1.59, benchmarks.csv 1.31-1.61 (K_SWEEP_RESULTS), "
        "v11_engine_modes.md 1.67. UNRESOLVED — needs whoever owns the measurement. "
        "The page currently publishes the fastest of the four."),
    ("quick", "toks"): (
        "models.csv has 14.6; the page says 'Not measured'. The page is the more "
        "conservative claim, so it is safe to leave while the provenance of 14.6 "
        "is confirmed."),
    ("vision", "toks"): (
        "models.csv is blank; the page says 16.31, which IS sourced — "
        "docs/v11_engine_modes.md lists 16.31 for the V9 stable default. "
        "The data file is the one with the gap."),
}

MIN_TIERS = 5


def page_figures(root: Path):
    s = (root / "index.html").read_text(encoding="utf-8", errors="ignore")
    m = re.search(r'<section id="benchmarks".*?</section>', s, re.S)
    if not m:
        return {}
    out = {}
    for row in re.findall(r"<tr>(.*?)</tr>", m.group(1) if m.lastindex else m.group(0), re.S):
        cells = [html.unescape(re.sub(r"<[^>]+>", " ", c)).strip()
                 for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, re.S)]
        if len(cells) < 4 or "Outlier" not in cells[0]:
            continue
        name = cells[0].lower()
        tier = next((t for t in ("nano", "lite", "quick", "core", "code", "plus", "vision")
                     if t in name), None)
        if not tier:
            continue
        tier = "compact" if tier == "core" else tier
        tok = re.search(r"([\d.]+)\s*tok/s", cells[3])
        out[tier] = tok.group(1) if tok else None
    return out


def main(root_arg: str = ".") -> int:
    root = Path(root_arg)
    csv_path = root / "seo" / "_data" / "models.csv"
    if not csv_path.is_file():
        print(f"FAIL: {csv_path} not found — cannot compare anything.")
        return 1
    data = {r["tier_id"]: r for r in csv.DictReader(csv_path.open())}
    page = page_figures(root)

    print(f"tiers in models.csv: {len(data)} | tiers found on the page: {len(page)}")
    if len(page) < MIN_TIERS:
        print(f"\nFAIL: only {len(page)} tiers parsed from the page, expected >= {MIN_TIERS}.")
        print("      The scan is likelier broken than the page. Not reporting clean.")
        return 1

    fails, noted = [], []
    for tier, shown in page.items():
        want = (data.get(tier, {}).get("m1_ultra_toks") or "").strip()
        same = (shown or "") == want
        if same:
            continue
        key = (tier, "toks")
        if key in CONFLICTS:
            noted.append(f"  [known] {tier:<8} page={shown!s:<8} csv={want or '(blank)':<8} {CONFLICTS[key]}")
        else:
            fails.append(f"  {tier}: page says {shown!s}, models.csv says {want or '(blank)'} — "
                         f"undeclared divergence")
    for n in noted:
        print(n)
    if fails:
        print(f"\nFAIL ({len(fails)}):")
        for f in fails:
            print(f)
        print("\n  Either correct one side, or add an entry to CONFLICTS stating which "
              "sources disagree and why the page keeps its value.")
        return 1
    print(f"\nPASS — every page figure matches models.csv, or is a declared conflict.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "."))
