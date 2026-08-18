#!/usr/bin/env python3
"""Every internal link must point at something that exists.

Found by hand: five dead links on a live page, including a button reading
"Download Outlier" that went to /app/ and returned 404. A visitor who clicked the
primary call to action on that page got an error, and had done for as long as the
page existed. Nine gates were green throughout — they check versions, prices,
checkouts, proof text, styling and what is served, and not one of them asks
whether a link on page A reaches a file that exists.

WHY IT CHECKS THE FILESYSTEM AND NOT THE NETWORK. A crawl of 1,400 links would be
slow, would need the deploy to have happened, and would answer a different
question — "is it live now" rather than "is it right in the repo". The four dead
targets were absent from the tree AND 404 on the site, confirmed both ways. The
filesystem answer is available before the commit, which is where the check
belongs.

RESOLUTION MIRRORS A STATIC HOST: /a/b/ matches a/b/index.html, /a/b matches
a/b.html or a/b/index.html. Anchors and query strings are stripped before
resolving, so /#pricing is a link to the homepage, not to a file called "#".

External links, mailto: and tel: are out of scope — this cannot know whether a
third party is up, and a gate that fails when someone else's site is down is a
gate that gets switched off.

    python3 scripts/internal_link_gate.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

HREF = re.compile(r'href="([^"]+)"')
SKIP = ("http://", "https://", "mailto:", "tel:", "#", "data:", "javascript:")
MIN_LINKS = 500


def resolves(root: Path, page: Path, target: str) -> bool:
    base = root if target.startswith("/") else page.parent
    f = base / target.lstrip("/")
    return f.is_file() or (f / "index.html").is_file() or f.with_suffix(".html").is_file()


def main(root_arg: str = ".") -> int:
    root = Path(root_arg)
    # Vacuity control: resolution must reject something that is not there.
    if resolves(root, root / "index.html", "definitely-not-a-real-path-xyz/"):
        print("FAIL: resolver accepts a nonexistent path. Instrument broken.")
        return 1

    checked, broken = 0, []
    for p in sorted(root.rglob("*.html")):
        if ".git" in p.parts or "_seo_build" in p.parts:
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for href in HREF.findall(text):
            if href.startswith(SKIP):
                continue
            target = href.split("#")[0].split("?")[0]
            if not target:
                continue
            checked += 1
            if not resolves(root, p, target):
                broken.append((str(p.relative_to(root)), target))

    print(f"internal links checked: {checked}")
    if checked < MIN_LINKS:
        print(f"\nFAIL: only {checked} links checked, expected >= {MIN_LINKS}.")
        print("      A scan that found almost nothing prints the same word as a clean one.")
        return 1

    if broken:
        print(f"\nFAIL: {len(broken)} internal link(s) point at nothing:")
        for page, target in broken[:20]:
            print(f"  {page}  ->  {target}")
        print("\n  These 404 for a visitor. Check whether the destination moved or never")
        print("  existed; the rest of the site's canonical targets are the guide.")
        return 1

    print(f"\nPASS — all {checked} internal links resolve.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "."))
