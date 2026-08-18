#!/usr/bin/env python3
"""The homepage must not get shorter. Nothing was checking that.

"Word floor ~2,617 — stop cutting" is a SETTLED decision for outlier.host,
carried in a handoff brief and nowhere else. A decision that lives only in prose
survives exactly as long as the next person who reads it, and the pressure on
this page is always downward: it is long, it reads long, and every review of it
produces a suggestion to trim.

WHAT THIS ENFORCES, and the distinction is the whole point:

  it fails on CUTS. It does not demand padding.

Measured with the repo's own `seo_lint.visible_text()` — not a second
implementation, because two ways of counting words is two answers — index.html
reads **2,607** today. The settled figure is ~2,617, so the page already sits ten
words under. That gap is 0.4% and it is NOT worth closing: adding ten words to
clear a round number is precisely the move seo_lint argues against for thin
pages, where its own comment reads "padding a nav index to 600 words makes it
worse to read and no better to rank".

So the baseline here is what the page ACTUALLY IS, not the remembered number. The
rule is that it does not go below that. If a future edit legitimately removes a
section, lower BASELINE in the same commit and say why — that makes shortening a
decision somebody signs, which is all "stop cutting" was ever asking for.

WHAT IT CANNOT DO. Word count is a proxy for substance and a bad one. A page can
hold its count and lose the paragraph that did the persuading. This catches the
blunt version — a section deleted — and nothing subtler.
"""
from __future__ import annotations

import sys
from pathlib import Path

#: What index.html measures today, by seo_lint.visible_text(). Not the ~2,617
#: from the brief: that number and this measurement disagree by ten words, and
#: the honest baseline is the artifact rather than the memory of it.
BASELINE = 2607

#: Anything under this is a cut. No upper bound — growing is not a failure.
TOLERANCE = 0


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    sys.path.insert(0, str(root / "scripts"))
    try:
        from seo_lint import visible_text
    except Exception as exc:
        print(f"FAIL: could not import seo_lint.visible_text ({exc}) — this gate must use "
              f"the SAME counter as the linter, so it does not fall back to its own.")
        return 1

    page = root / "index.html"
    if not page.exists():
        print(f"FAIL: {page} missing — nothing checked, which is not a pass")
        return 1

    words = len(visible_text(page.read_text(encoding="utf-8", errors="ignore")).split())
    delta = words - BASELINE
    print(f"  index.html   {words} words   baseline {BASELINE}   {delta:+d}")

    if words < BASELINE - TOLERANCE:
        print()
        print(f"FAIL: the homepage lost {BASELINE - words} word(s).")
        print(f"    'Stop cutting' is a settled decision for this page. If the removal was")
        print(f"    deliberate, lower BASELINE to {words} in the same commit and say what came")
        print(f"    out — that makes shortening something somebody signs rather than something")
        print(f"    that happens. If it was not deliberate, restore the section.")
        return 1

    print()
    print(f"OK: the homepage is not shorter than its baseline.")
    print("Word count is a poor proxy for substance: a page can hold its count and still lose")
    print("the paragraph that did the persuading. This catches a deleted section, nothing subtler.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
