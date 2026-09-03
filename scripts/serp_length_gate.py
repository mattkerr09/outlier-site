#!/usr/bin/env python3
"""The homepage's search snippet must fit in the search snippet.

Google renders roughly 60 characters of <title> and roughly 155 of the meta
description. The homepage carried 103 and 246, so the title cut mid-word --

    Outlier — A private, offline alternative to cloud AI like Cl

-- and the description stopped before both of the strongest things it had to
say: that nothing leaves your device, and that the price is one-time.

WHY THIS GATE COVERS ONE PAGE AND NOT 248, WHICH IS THE ONLY INTERESTING
DECISION IN THE FILE.

Measured across the site: 129 of 248 titles are over 60 and 152 of 248
descriptions are over 155. A gate at those limits would be red on more than
half the site from the moment it was written, and a permanently red gate is
one nobody reads -- which is exactly how twelve false competitor prices sat on
this site for eighteen days underneath a price gate that was always red.

The homepage is different in kind, not degree. It earns about 82 Google
visitors a month, an order of magnitude more than any other page here, so a
truncated snippet there costs click-through on traffic already earned rather
than traffic that might arrive. Rewriting the other 129 titles is a content
project with per-page judgement in it, not a lint fix, and doing it as a sweep
is precisely the thing that went wrong on this site once already.

So: hold the line where the traffic is, and leave the rest recorded rather than
enforced. If the other pages are ever rewritten, widen the ONLY_PAGES list.

Not checked here, deliberately: og: and twitter: fields. They have different
consumers and different limits -- a social card is not a search result -- and
shortening them to a SERP budget would lose information for no gain.

Run: python3 scripts/serp_length_gate.py <site-root>
"""
import html
import re
import sys
from pathlib import Path

TITLE_MAX = 60
DESC_MAX = 155
ONLY_PAGES = ["index.html"]

_TITLE = re.compile(r"<title>(.*?)</title>", re.S | re.I)
_DESC = re.compile(r'<meta\s+name="description"\s+content="(.*?)"', re.S | re.I)


def _field(pattern, src):
    """Decoded, because &amp; is one character to Google and five to a regex."""
    m = pattern.search(src)
    return html.unescape(m.group(1)).strip() if m else None


def main(root: str) -> int:
    base = Path(root)
    failures, checked = [], 0
    for rel in ONLY_PAGES:
        path = base / rel
        if not path.exists():
            print(f"serp_length_gate: {path} is missing — the check proved nothing",
                  file=sys.stderr)
            return 1
        src = path.read_text(encoding="utf-8", errors="replace")
        checked += 1
        title = _field(_TITLE, src)
        desc = _field(_DESC, src)
        if title is None:
            failures.append(f"{rel}: no <title>")
        elif len(title) > TITLE_MAX:
            failures.append(f"{rel}: title {len(title)} chars (max {TITLE_MAX}) — "
                            f"Google cuts it at {title[:TITLE_MAX]!r}")
        if desc is None:
            failures.append(f"{rel}: no meta description")
        elif len(desc) > DESC_MAX:
            failures.append(f"{rel}: description {len(desc)} chars (max {DESC_MAX}) — "
                            f"cut before {desc[DESC_MAX:][:40]!r}")

    print(f"serp_length_gate: checked {checked} page(s) "
          f"(title<={TITLE_MAX}, description<={DESC_MAX})")
    if failures:
        print(f"serp_length_gate: FAIL ({len(failures)})", file=sys.stderr)
        for f in failures:
            print("  " + f, file=sys.stderr)
        return 1
    print("serp_length_gate: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "."))
