#!/usr/bin/env python3
"""Sync sitemap dates from page dateModified, then visible Last updated dates.

Pages with neither keep their lastmod. No filesystem or git timestamps are used.
--check writes nothing and exits 1 if a sitemap date lags its page.
"""
from __future__ import annotations

import datetime as dt
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
NS = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}


class Visible(HTMLParser):
    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag not in self.VOID:
            self.stack.append((tag, tag in {"script", "style", "template"} or "hidden" in dict(attrs)))

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break

    def handle_data(self, data):
        if not any(off for _, off in self.stack):
            self.parts.append(data)


def page_date(raw: str) -> str | None:
    def modified(value):
        if isinstance(value, dict):
            for key, child in value.items():
                if key == "dateModified" and isinstance(child, str):
                    yield dt.date.fromisoformat(child[:10]).isoformat()
                else:
                    yield from modified(child)
        elif isinstance(value, list):
            for child in value:
                yield from modified(child)

    dates = []
    for block in re.findall(r'<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', raw, re.S):
        dates.extend(modified(json.loads(block)))
    if dates:
        return max(dates)
    visible = Visible()
    visible.feed(raw)
    text = " ".join(" ".join(visible.parts).split())
    match = re.search(r"Last updated\s*:?\s*(\d{4}-\d{2}-\d{2})", text, re.I)
    return dt.date.fromisoformat(match[1]).isoformat() if match else None


def page_path(root: Path, url: str) -> Path:
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.netloc != "outlier.host":
        raise ValueError(f"not a site URL: {url}")
    path = unquote(parsed.path).lstrip("/")
    target = root / path
    if not path or path.endswith("/"):
        target /= "index.html"
    if not target.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"URL leaves site root: {url}")
    return target


def sync(root: Path, check: bool = False) -> tuple[str, int, int]:
    raw = (root / "sitemap.xml").read_text(encoding="utf-8")
    entries = ET.fromstring(raw).findall("s:url", NS)
    if not entries:
        raise ValueError("sitemap has no URLs")
    changed = lagging = 0
    for entry in entries:
        url = entry.findtext("s:loc", namespaces=NS)
        old = entry.findtext("s:lastmod", namespaces=NS)
        date = page_date(page_path(root, url).read_text(encoding="utf-8"))
        if date is None or old == date:
            continue
        changed += 1
        if old is None or old[:10] < date:
            lagging += 1
        if not check:
            # Preserve the sitemap's existing whitespace and element order.
            pattern = r'(<url>\s*<loc>\s*' + re.escape(url) + r'\s*</loc>)(.*?)(</url>)'
            def replace(match):
                middle = match[2]
                if old is None:
                    middle = '\n    <lastmod>' + date + '</lastmod>' + middle
                else:
                    middle = re.sub(r'(<lastmod>).*?(</lastmod>)',
                                    lambda m: m[1] + date + m[2], middle, count=1)
                return match[1] + middle + match[3]
            raw, count = re.subn(pattern, replace, raw, count=1, flags=re.S)
            if count != 1:
                raise ValueError(f"could not update {url}")
    return raw, changed, lagging


def main(argv: list[str]) -> int:
    check = "--check" in argv
    root = Path(next((a for a in argv if a != "--check"), ROOT))
    raw, changed, lagging = sync(root, check)
    if not check and changed:
        (root / "sitemap.xml").write_text(raw, encoding="utf-8")
    print(f"sitemap_lastmod: {changed} date(s) {'differ' if check else 'updated'}; {lagging} lagging")
    return 1 if check and lagging else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
