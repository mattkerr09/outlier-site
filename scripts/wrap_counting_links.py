#!/usr/bin/env python3
"""Route every Download and Buy button through the counting links.

    python3 scripts/wrap_counting_links.py [--check]

WHY (CEO, 2026-09-28). GitHub's download counts are mostly our own checks and crawlers
(739 releases, 5-20 downloads each), so nobody could say how many PEOPLE downloaded. The
worker at kerr-affiliate-hub counts people, not robots, stores no IP or user agent, and
302s to the file:

    https://kerr-affiliate-hub.kerrco.workers.dev/dl/outlier?src=<page-tag>&to=<GitHub DMG URL>

It accepts Outlier-host/outlier-app-releases URLs only (anything else goes to
outlier.host/#pricing). Buy buttons go to /buy/outlier?src=<page-tag>, which opens a Dodo
checkout with the founders code applied while seats remain.

THREE THINGS KEEP THIS COMPATIBLE WITH EVERYTHING ELSE:
- `to=` is LAST and NOT percent-encoded, so bump_site_version.py (which rewrites the
  substring releases/download/vX/Outlier-X-arm64.dmg) and download_version_gate.py keep
  finding the version, and the href still ENDS in .dmg — which is what the homepage's
  Plausible "Download" handler (a[href$=".dmg"]) and Plausible's own file-download
  detection key on.
- The page tag is the page's path (index.html → home, vs/x/index.html → vs-x,
  seo/<category>/<slug>/index.html → seo-<category>-<slug>) — the SAME tag
  _seo_build/scripts/render.py passes the template, so a re-render changes nothing.
- Idempotent: an href already wrapped is left alone; --check writes nothing.
"""
from __future__ import annotations

import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import hub_nofollow  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
DL_WORKER = "https://kerr-affiliate-hub.kerrco.workers.dev/dl/outlier"
BUY_WORKER = "https://kerr-affiliate-hub.kerrco.workers.dev/buy/outlier"
GH_DMG = r"https://github\.com/Outlier-host/outlier-app-releases/releases/download/v\d+\.\d+\.\d+/Outlier-\d+\.\d+\.\d+-arm64\.dmg"
# A bare GitHub DMG href (not already inside a wrapper, whose href starts with the worker).
BARE_DL_RE = re.compile(r'href="(' + GH_DMG + r')"')
BARE_BUY_RE = re.compile(r'href="https://checkout\.dodopayments\.com/buy/pdt_[A-Za-z0-9_]+\?redirect_url=[^"]*"')


def page_tag(path: pathlib.Path) -> str:
    rel = path.relative_to(ROOT).as_posix()
    if rel == "index.html":
        return "home"
    rel = re.sub(r"/index\.html$", "", rel)
    rel = re.sub(r"\.html$", "", rel)
    return re.sub(r"[^a-z0-9-]+", "-", rel.lower()).strip("-")[:80] or "page"


def pages():
    for p in sorted(ROOT.rglob("*.html")):
        parts = p.relative_to(ROOT).parts
        if any(x.startswith(".") for x in parts) or parts[0] == "_seo_build" or ".pre" in p.name:
            continue
        yield p


def wrap(text: str, tag: str) -> str:
    text = BARE_DL_RE.sub(lambda m: f'href="{DL_WORKER}?src={tag}&amp;to={m.group(1)}"', text)
    text = BARE_BUY_RE.sub(f'href="{BUY_WORKER}?src={tag}"', text)
    # 2026-09-29: a hub link is a counting redirect, not a page to crawl (hub_nofollow.py).
    text, _ = hub_nofollow.add_nofollow(text)
    return text


def main(argv: list[str]) -> int:
    check = "--check" in argv
    changed = 0
    for p in pages():
        s = p.read_text(encoding="utf-8")
        t = wrap(s, page_tag(p))
        if t != s:
            changed += 1
            n_dl = len(BARE_DL_RE.findall(s))
            n_buy = len(BARE_BUY_RE.findall(s))
            print(f"  {p.relative_to(ROOT)} [{page_tag(p)}]: {n_dl} download, {n_buy} buy")
            if not check:
                p.write_text(t, encoding="utf-8")
    left = sum(len(BARE_DL_RE.findall(p.read_text(encoding="utf-8"))) + len(BARE_BUY_RE.findall(p.read_text(encoding="utf-8")))
               for p in pages()) if not check else None
    print(f"  {changed} page(s) {'would change' if check else 'written'}"
          + ("" if check else f"; bare links left: {left}"))
    return 0 if (check or left == 0) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
