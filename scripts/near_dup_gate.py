#!/usr/bin/env python3
"""No two indexable pages share half their wording.

WHY. Scaled near-duplicate pages are, with link schemes, one of Bing's two big spam
signals, and outlier.host's Bing impressions went to 0 on 2026-09-15. On 10-13 the
/seo/run and /seo/vs matrix had 39 page pairs at a 5-word-shingle Jaccard of 0.5 or
more, in 6 groups covering 33 pages (seo/run/run-compact-on-m4-pro-mac-mini against
run-quick-on-m4-pro-mac-mini at 0.73, for one). Each group now keeps one indexable
page; the rest are noindex (seo/_data/noindex.json).

seo_lint's DUP check did not stop this: it is a ratchet over 8-word shingles with a
171-pair allowance, and it skips class="related" blocks by design. This gate is
absolute: any pair of INDEXABLE pages at >= THRESHOLD fails, so a new page that
copies an existing one cannot ship, whichever section it lands in.

WHAT IS COMPARED. The body text of every index.html that is indexable (no robots
noindex, no meta refresh), without script/style/nav/header/footer and without the
class="related" and byline rows, lower-cased into word tokens, as 5-word shingles.

Refuses (exit 1) on a tree with fewer than MIN_PAGES indexable pages: an empty scan
is not a clean one (meta_gate checks this).

    python3 scripts/near_dup_gate.py .
"""
from __future__ import annotations

import itertools
import re
import sys
from pathlib import Path

THRESHOLD = 0.5
SHINGLE = 5
MIN_PAGES = 50
_DROP = re.compile(r"<(script|style|nav|header|footer|noscript)\b.*?</\1>", re.S | re.I)
_ROWS = re.compile(r'<div class="(?:related|byline-row)".*?</div>', re.S)
_NOINDEX = re.compile(r"""<meta\s+name=["']robots["']\s+content=["'][^"']*noindex""", re.I)


def words(html: str) -> list[str] | None:
    """The page's body words, or None when the page is not indexable."""
    if _NOINDEX.search(html) or 'http-equiv="refresh"' in html:
        return None
    m = re.search(r"<body\b.*?</body>", html, re.S | re.I)
    body = _ROWS.sub(" ", _DROP.sub(" ", m.group(0) if m else html))
    text = re.sub(r"&[a-z#0-9]+;", " ", re.sub(r"<[^>]+>", " ", body))
    return re.findall(r"[a-z0-9$.%]+", text.lower())


def shingles(w: list[str]) -> set[str]:
    return {" ".join(w[i:i + SHINGLE]) for i in range(len(w) - SHINGLE + 1)}


def main(root: str = ".") -> int:
    base = Path(root)
    pages: dict[str, set[str]] = {}
    for p in sorted(base.rglob("index.html")):
        if ".git" in p.parts or "node_modules" in p.parts or "_seo_build" in p.parts:
            continue
        w = words(p.read_text(encoding="utf-8", errors="replace"))
        if w and len(w) >= SHINGLE:
            pages[p.parent.relative_to(base).as_posix() + "/"] = shingles(w)
    print(f"near_dup_gate: {len(pages)} indexable pages under {root}, threshold {THRESHOLD}")
    if len(pages) < MIN_PAGES:
        print(f"FAIL: only {len(pages)} indexable pages (expected >= {MIN_PAGES}); not reporting clean.")
        return 1
    bad = []
    for a, b in itertools.combinations(sorted(pages), 2):
        A, B = pages[a], pages[b]
        if not A or not B:
            continue
        j = len(A & B) / len(A | B)
        if j >= THRESHOLD:
            bad.append((j, a, b))
    if bad:
        print(f"FAIL: {len(bad)} indexable page pair(s) share >= {THRESHOLD:.0%} of their {SHINGLE}-word shingles.")
        print("      Merge the pair into one page, or noindex the weaker one (seo/_data/noindex.json for /seo/).")
        for j, a, b in sorted(bad, reverse=True)[:40]:
            print(f"  {j:.3f}  {a}  ~  {b}")
        return 1
    print(f"PASS: no two indexable pages share >= {THRESHOLD:.0%} of their wording")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "."))
