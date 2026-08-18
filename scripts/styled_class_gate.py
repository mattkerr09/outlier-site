#!/usr/bin/env python3
"""Every class in the markup must be styled by something.

Adopted from a sibling project, which had four instances of it. This site has
none — 251 pages, zero unstyled classes, measured before the gate was written
rather than claimed after. It is here as a regression guard, and the regression
it guards is one this repo nearly shipped.

THE FAILURE IT CATCHES. A class renamed in the markup but not in the stylesheet
(or added to markup that never got a rule) renders as unstyled text: the element
is present, the words are correct, every existing gate reads the page and finds
exactly what it expects. Nothing here asks whether anything makes it LOOK like
anything, so the page can be simultaneously correct and visibly broken.

WHY IT IS NOT HYPOTHETICAL HERE. A pulsing status dot was renamed .live -> .dot
in one pass that edited the markup and the CSS together. Earlier the same day, a
paired edit in this repo half-landed because one of its two anchors did not match
the file's bytes — the markup changed and its counterpart did not. That is
precisely this bug, and it survived only because a different gate happened to pin
both halves of that particular change. This one does not depend on happening to
have thought of it.

WHAT IT DELIBERATELY TOLERATES: a class that IS styled but never used. Dead CSS
is untidy, not broken, and failing on it would make the gate noisy enough to
switch off. Only the direction that produces a visibly wrong page is an error.

    python3 scripts/styled_class_gate.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

MIN_PAGES = 50
CLASS_ATTR = re.compile(r'class="([^"]+)"')
STYLE_BLOCK = re.compile(r"<style[^>]*>(.*?)</style>", re.S | re.I)
CSS_LINK = re.compile(r'<link[^>]+href="([^"]+\.css)"')
SELECTOR = re.compile(r"\.([A-Za-z_][\w-]*)")


def css_for(page: Path, text: str, root: Path) -> str:
    css = "\n".join(STYLE_BLOCK.findall(text))
    for href in CSS_LINK.findall(text):
        target = (root / href.lstrip("/")) if href.startswith("/") else (page.parent / href)
        try:
            css += "\n" + target.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            pass
    return css


def main(root_arg: str = ".") -> int:
    root = Path(root_arg)

    # Vacuity control: the detector must flag a known-bad page every run.
    probe_used = {"styled", "orphan"}
    probe_defined = set(SELECTOR.findall(".styled{color:red}"))
    if not (probe_used - probe_defined) == {"orphan"}:
        print("FAIL: detector cannot distinguish styled from unstyled. Instrument broken.")
        return 1

    pages, bad = 0, []
    for p in sorted(root.rglob("*.html")):
        if ".git" in p.parts or "_seo_build" in p.parts:
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        pages += 1
        used = {c for m in CLASS_ATTR.finditer(text) for c in m.group(1).split() if c}
        defined = set(SELECTOR.findall(css_for(p, text, root)))
        missing = sorted(used - defined)
        if missing:
            bad.append((str(p.relative_to(root)), missing))

    print(f"pages scanned: {pages}")
    if pages < MIN_PAGES:
        print(f"\nFAIL: only {pages} pages scanned, expected >= {MIN_PAGES}.")
        print("      A scan that looked at nothing prints the same word as a clean one.")
        return 1

    if bad:
        print(f"\nFAIL: {len(bad)} page(s) use a class no stylesheet defines:")
        for path, missing in bad[:15]:
            print(f"  {path}: {', '.join('.' + m for m in missing[:8])}")
        print("\n  These render as unstyled text. The markup is right, the words are right,")
        print("  and every other gate here will pass — usually a rename that landed on one")
        print("  side only. Fix the stylesheet or the markup; do not silence this.")
        return 1

    print(f"\nPASS — every class used across {pages} pages is styled somewhere.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "."))
