#!/usr/bin/env python3
"""No page outside /about/ links to one of our other domains.

WHY. On 2026-09-15 a "From the same builder" block went onto 171 pages and the byline
linked to builtbykerr.com on 116 more; on 09-17 every footer got a six-link list of
the sister sites. Bing impressions for outlier.host went from 45-89 a day to 8 on
09-15 and to 0 (1 on three days) every day after, while Bing kept crawling and
reported no errors. Sitewide links between commonly owned sites are a textbook link
scheme, and Bing feeds ChatGPT search, Copilot and DuckDuckGo, which is where the
first buyers came from. The block even reused class="related" so that seo_lint's
duplicate check would skip it.

THE RULE, as a class rather than this one instance:
  - crispvideo.app, docketseo.app, adplaybook.app, bookbreaker.bet and builtbykerr.com
    may be linked only from about/index.html, where naming the sister apps once reads
    naturally;
  - kerrandcompanyholdings.com (the footer's "Made by Kerr & Company") at most once
    a page;
  - llms.txt and every other tracked text file may NAME the sister products but not
    carry their URLs.
Hosts are matched by HOST (www. and subdomains included), never by substring, so
"crispvideo.app.example" is not ours and "www.crispvideo.app" is.

Refuses (exit 1) on a tree with fewer than MIN_PAGES pages: an empty scan is not a
clean one (meta_gate checks this).

    python3 scripts/sister_link_gate.py .
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import urlparse

SISTERS = ("crispvideo.app", "docketseo.app", "adplaybook.app", "bookbreaker.bet", "builtbykerr.com")
PARENT = "kerrandcompanyholdings.com"
SISTER_PAGES = {"about/index.html"}
TEXT_EXT = (".txt", ".md", ".xml", ".json")
MIN_PAGES = 50
HREF = re.compile(r"""href\s*=\s*["']([^"']+)["']""", re.I)
URL = re.compile(r"""https?://[^\s"'<>)\]]+""", re.I)


def ours(url: str) -> str | None:
    """The domain of ours this URL points at, or None."""
    try:
        host = (urlparse(url.strip()).hostname or "").lower().rstrip(".")
    except ValueError:
        return None
    for d in SISTERS + (PARENT,):
        if host == d or host.endswith("." + d):
            return d
    return None


def main(root: str = ".") -> int:
    base = Path(root)
    pages = sorted(p for p in base.rglob("*.html") if ".git" not in p.parts and "node_modules" not in p.parts)
    texts = sorted(p for p in base.rglob("*") if p.suffix in TEXT_EXT and p.is_file()
                   and ".git" not in p.parts and "node_modules" not in p.parts and "scripts" not in p.parts)
    print(f"sister_link_gate: {len(pages)} pages, {len(texts)} text files under {root}")
    if len(pages) < MIN_PAGES:
        print(f"FAIL: only {len(pages)} pages found (expected >= {MIN_PAGES}); not reporting clean.")
        return 1
    bad: list[str] = []
    for p in pages:
        rel = p.relative_to(base).as_posix()
        html = p.read_text(encoding="utf-8", errors="replace")
        hits = [d for d in (ours(h) for h in HREF.findall(html)) if d]
        sis = sorted({d for d in hits if d in SISTERS})
        if sis and rel not in SISTER_PAGES:
            bad.append(f"{rel}: links {', '.join(sis)}")
        if hits.count(PARENT) > 1:
            bad.append(f"{rel}: links {PARENT} {hits.count(PARENT)} times (at most once)")
    for p in texts:
        rel = p.relative_to(base).as_posix()
        if rel == "sitemap.xml" or rel.endswith("baseline.json"):
            continue
        sis = sorted({d for d in (ours(u) for u in URL.findall(p.read_text(encoding="utf-8", errors="replace")))
                      if d in SISTERS})
        if sis:
            bad.append(f"{rel}: carries URLs of {', '.join(sis)} (name the products in text instead)")
    if bad:
        print(f"FAIL: {len(bad)} cross-site link problem(s):")
        for b in bad[:60]:
            print("  " + b)
        return 1
    print("PASS: no page outside about/ links to a sister domain; Kerr & Company at most once a page")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "."))
