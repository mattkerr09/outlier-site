#!/usr/bin/env python3
"""Every indexable page must be in sitemap.xml. Crawlers cannot guess.

/data/outlier-tier-benchmarks-2026-08/ — "MMLU for every shipping tier" — was
live, returned 200, carried no noindex, and appeared in no sitemap. Checked the
history: it was never there. Not a page that was dropped, a page that was never
added, which is why nothing noticed. On a site whose whole advantage is 250
indexed pages, an invisible one is a page that does not exist.

This is a different question from internal_link_gate's. That one asks whether a
READER following a link lands somewhere; this asks whether a CRAWLER is told the
page is there at all. A page can pass that gate perfectly and still be invisible.

NOINDEX PAGES ARE SKIPPED, and that exemption is not cosmetic. A peer's link
audit flagged three demo builds for fictional businesses as missing from a
sitemap; acting on it would have submitted three companies that do not exist to
Google. A page marked noindex is asserting it does not want to be found, and a
gate that argues with that is worse than no gate.

Deliberately NOT checked here: whether a sitemap URL still resolves. That is the
mirror of this question and it belongs with the link gate, which already walks
the tree resolving paths. One gate, one direction.

Run: python3 scripts/sitemap_coverage_gate.py <site-root>
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

SITE = "https://outlier.host"
SKIP_DIRS = {".git", "node_modules", "_seo_build", "fonts", "scripts"}

#: If the scan finds fewer than this, it is likelier broken than the site is
#: tiny. meta_gate.py requires every gate to refuse a clean report on nothing.
MIN_PAGES = 50

_NOINDEX = re.compile(r"\bnoindex\b", re.I)
_LOC = re.compile(r"<loc>\s*([^<\s]+)\s*</loc>", re.I)


def url_for(page: Path, root: Path) -> str:
    rel = page.parent.relative_to(root).as_posix()
    return f"{SITE}/" .rstrip("/") + ("" if rel == "." else "/" + rel)


def main(root_arg: str) -> int:
    root = Path(root_arg)
    sitemap = root / "sitemap.xml"
    if not sitemap.exists():
        print(f"sitemap_coverage_gate: no sitemap.xml under {root_arg} — "
              f"the check proved nothing", file=sys.stderr)
        return 1

    listed = {u.rstrip("/") for u in _LOC.findall(sitemap.read_text(
        encoding="utf-8", errors="replace"))}

    missing, skipped, checked = [], 0, 0
    for page in sorted(root.rglob("index.html")):
        if any(part in SKIP_DIRS for part in page.parts):
            continue
        raw = page.read_text(encoding="utf-8", errors="replace")
        checked += 1
        if _NOINDEX.search(raw):
            skipped += 1
            continue
        if url_for(page, root).rstrip("/") not in listed:
            title = re.search(r"<title>(.*?)</title>", raw, re.S)
            missing.append((page.parent.relative_to(root).as_posix(),
                            re.sub(r"\s+", " ", title.group(1))[:70] if title else ""))

    if checked < MIN_PAGES:
        print(f"sitemap_coverage_gate: only {checked} pages found under "
              f"{root_arg}, expected >= {MIN_PAGES}. The scan is likelier "
              f"broken than the site. Not reporting clean.", file=sys.stderr)
        return 1

    print(f"checked {checked} pages against {len(listed)} sitemap URLs")
    # Say what was exempted. A skip nobody prints reads exactly like a page
    # that passed.
    if skipped:
        print(f"{skipped} noindex page(s) skipped — they are asking not to be found")
    if not missing:
        print("PASS — every indexable page is in the sitemap")
        return 0
    print(f"\nFAIL ({len(missing)} indexable page(s) in no sitemap):", file=sys.stderr)
    for path, title in missing:
        print(f"  {path}\n    {title}", file=sys.stderr)
    print("\nA page crawlers are never told about is a page that does not exist.",
          file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "."))
