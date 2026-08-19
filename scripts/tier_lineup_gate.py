#!/usr/bin/env python3
"""The product shot must show every tier that ships.

Shipped defect this exists for (2026-08-18): the hero's model list showed four
tiers -- Nano, Lite, Core, Plus -- while the app shipped seven. Quick 26B, Code
27B and Vision 35B were absent from the most-seen element on the site, and the
page's own pricing section two screens down said "Pro adds the other five tiers
-- Quick, Core, Code, Vision, and the 397B Plus tier". The page contradicted
itself and twelve gates were green, because no gate compared the DRAWING of the
product against the list of what exists.

Ground truth is seo/_data/models.csv, which is the same file the figure gate
uses for tok/s. The live backend's /health reports the identical seven ids, but
a gate may not depend on a running app, so the csv is authoritative here.
"""
import csv
import re
import sys
from pathlib import Path

# The hero chip says "Core", models.csv calls the row "compact". Same tier.
CSV_TO_LABEL = {
    "nano": "Nano", "lite": "Lite", "quick": "Quick", "compact": "Core",
    "code": "Code", "plus": "Plus", "vision": "Vision",
}
MIN_TIERS = 5   # vacuity guard: fewer than this and the csv scan is broken


def main(root_arg: str = ".") -> int:
    root = Path(root_arg)
    csv_path = root / "seo" / "_data" / "models.csv"
    page = root / "index.html"
    if not csv_path.is_file():
        print(f"FAIL: {csv_path} not found — nothing to compare against.")
        return 1
    if not page.is_file():
        print(f"FAIL: {page} not found.")
        return 1

    rows = [r for r in csv.DictReader(csv_path.open()) if (r.get("tier_id") or "").strip()]
    expected = {CSV_TO_LABEL.get(r["tier_id"].strip(), r["tier_id"].strip()) for r in rows}
    if len(expected) < MIN_TIERS:
        print(f"FAIL: only {len(expected)} tiers parsed from models.csv, expected >= {MIN_TIERS}.")
        print("      The scan is likelier broken than the product. Not reporting clean.")
        return 1

    html = page.read_text(errors="replace")
    # the hero's model list: <div class="tierchip"...><span>Nano · 4B</span>
    chips = re.findall(r'class="tierchip[^"]*"[^>]*>\s*<span>\s*([A-Za-z]+)', html)
    shown = {c.strip() for c in chips}
    if not shown:
        print("FAIL: no tier chips found in index.html. The hero product shot has no")
        print("      model list, or the markup changed and this gate went blind.")
        return 1

    missing = sorted(expected - shown)
    extra = sorted(shown - expected)

    print(f"tiers in models.csv: {len(expected)} | tiers drawn in the hero: {len(shown)}")
    if missing:
        print(f"\nFAIL: the hero omits {len(missing)} shipping tier(s): {', '.join(missing)}")
        print("      The product shot understates the product. Add them or, if a tier")
        print("      genuinely should not appear, say why here rather than dropping it.")
        return 1
    if extra:
        print(f"\nFAIL: the hero shows {len(extra)} tier(s) that are not in models.csv: "
              f"{', '.join(extra)}")
        print("      The product shot claims something that does not ship.")
        return 1

    print("\nPASS — the hero shows every tier in models.csv and nothing it does not.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "."))
