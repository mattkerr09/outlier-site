#!/usr/bin/env python3
"""rel="nofollow" on every link to the hub's /dl/ and /buy/ redirects.

    python3 scripts/hub_nofollow.py [--check]

WHY (CEO, 2026-09-29). The hub counted ~600 downloads and ~600 buys an hour from robots.
Every page carries hub links with their own src tag (about a thousand distinct URLs), the
hub's robots.txt said nothing, and the links said nothing either, so crawlers walked them.
The hub now disallows /dl/ and /buy/ and answers them with X-Robots-Tag: noindex, nofollow
(its 2e81ea33); this is the site's half. nofollow only, not sponsored or ugc.

ONE IMPLEMENTATION. add_nofollow() is what this script applies to the site, what
wrap_counting_links.py applies after it wraps a link, and the shape product_box.py and the
/seo/ template write themselves: rel="nofollow" right after href, or "nofollow" added to a
rel the tag already has. Idempotent; --check writes nothing. The attribute is invisible,
so no dateline moves.
"""
from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
HUB = "https://kerr-affiliate-hub.kerrco.workers.dev"

_TAG_RE = re.compile(r'<a\b[^>]*\bhref="' + re.escape(HUB) + r'/(?:dl|buy)/[^"]*"[^>]*>', re.S)
_HREF_RE = re.compile(r'\bhref="[^"]*"')
_REL_RE = re.compile(r'\brel="([^"]*)"')


def _fix(tag: str) -> str:
    rel = _REL_RE.search(tag)
    if rel:
        tokens = rel.group(1).split()
        if "nofollow" in tokens:
            return tag
        return tag[:rel.start(1)] + " ".join(tokens + ["nofollow"]) + tag[rel.end(1):]
    href = _HREF_RE.search(tag)
    return tag[:href.end()] + ' rel="nofollow"' + tag[href.end():]


def add_nofollow(text: str) -> tuple[str, int]:
    """Every hub /dl/ or /buy/ anchor in `text` carries rel nofollow. -> (text, tags changed)."""
    changed = 0

    def _sub(m: re.Match) -> str:
        nonlocal changed
        new = _fix(m.group(0))
        if new != m.group(0):
            changed += 1
        return new
    return _TAG_RE.sub(_sub, text), changed


def targets() -> list[pathlib.Path]:
    out = [p for p in ROOT.rglob("*.html") if ".git" not in p.parts and "node_modules" not in p.parts]
    return sorted(out)


def main(argv: list[str]) -> int:
    check = "--check" in argv
    files = tags = 0
    for p in targets():
        s = p.read_text(encoding="utf-8")
        new, n = add_nofollow(s)
        if n:
            files += 1
            tags += n
            if not check:
                p.write_text(new, encoding="utf-8")
    print(f"  {tags} hub link(s) in {files} file(s) {'would get' if check else 'now carry'} rel nofollow")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
