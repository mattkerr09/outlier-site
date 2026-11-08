#!/usr/bin/env python3
"""Offline checks for first-party Outlier links and unchanged raw query strings.

The fixture was computed from the base commit's HTML, including templates.
Queries keep their source bytes, including HTML entities, order and escapes.
They are compared per file and route so moving or swapping links also fails.
"""
from __future__ import annotations

from collections import Counter
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys

HUB_HOST = "kerr-affiliate-hub.kerrco.workers.dev"
OLD_LINK = re.compile(re.escape(HUB_HOST) + r'/(?:dl|buy)/outlier(?:[?/#\s\"\']|$)')
LINK = re.compile(r'https://(?:' + re.escape(HUB_HOST)
                  + r'|outlier\.host)(/(?:dl|buy)/outlier)(?:\?([^#]*))?(?:#.*)?$')
RAW_ATTR = re.compile(r'''([^\s=/>]+)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+)))?''')
SKIP = {".git", "node_modules", "__pycache__"}


class Links(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.queries: Counter[tuple[str, str]] = Counter()
        self.missing_nofollow: list[int] = []

    def handle_starttag(self, tag, attrs):
        if tag != "a":
            return
        raw = next((m for m in RAW_ATTR.finditer(self.get_starttag_text()[2:])
                    if m.group(1).lower() == "href"), None)
        if not raw or all(v is None for v in raw.groups()[1:]):
            return
        href = next(v for v in raw.groups()[1:] if v is not None)
        match = LINK.fullmatch(href)
        if not match:
            return
        route, query = match.groups()
        self.queries[route, query or ""] += 1
        if href.startswith("https://outlier.host/"):
            rel = dict(attrs).get("rel") or ""
            if "nofollow" not in rel.lower().split():
                self.missing_nofollow.append(self.getpos()[0])

    handle_startendtag = handle_starttag


def query_multiset(text: str) -> tuple[dict, list[int]]:
    parser = Links()
    parser.feed(text)
    result: dict[str, dict[str, int]] = {}
    for (route, query), count in sorted(parser.queries.items()):
        result.setdefault(route, {})[query] = count
    return result, parser.missing_nofollow


def robots_groups(text: str) -> list[tuple[list[str], set[str]]]:
    groups = []
    agents: list[str] = []
    disallows: set[str] = set()
    rules = False
    for line in text.splitlines():
        key, sep, value = line.split("#", 1)[0].partition(":")
        if not sep:
            continue
        key, value = key.strip().lower(), value.strip()
        if key == "user-agent":
            if agents and rules:
                groups.append((agents, disallows))
                agents, disallows, rules = [], set(), False
            agents.append(value)
        elif agents and key in {"allow", "disallow", "crawl-delay"}:
            rules = True
            if key == "disallow":
                disallows.add(value)
    if agents:
        groups.append((agents, disallows))
    return groups


def check(root: Path) -> int:
    failures = []
    html = sorted(p for p in root.rglob("*.html") if not SKIP.intersection(p.relative_to(root).parts))
    if not html:
        print("FIRST-PARTY LINKS: FAIL (no HTML pages found)")
        return 1
    files = set(html)
    for directory in ("scripts", "_seo_build", "seo"):
        files.update(p for p in (root / directory).rglob("*")
                     if p.is_file() and p.suffix != ".env" and not p.name.startswith(".env")
                     and not SKIP.intersection(p.relative_to(root).parts))
    for p in sorted(files):
        if OLD_LINK.search(p.read_text(encoding="utf-8", errors="replace")):
            failures.append(f"{p.relative_to(root)}: old Outlier hub link")

    current = {}
    pages = links = 0
    for p in html:
        queries, missing = query_multiset(p.read_text(encoding="utf-8"))
        name = p.relative_to(root).as_posix()
        if queries:
            current[name] = queries
            if not name.startswith(("_seo_build/", "scripts/")):
                pages += 1
            links += sum(sum(counts.values()) for counts in queries.values())
        failures.extend(f"{name}:{line}: Outlier link lacks rel nofollow" for line in missing)
    try:
        fixture = json.loads((root / "scripts/fixtures/first_party_links_before.json").read_text(encoding="utf-8"))
        before = fixture["queries"]
        if not before:
            raise ValueError("empty query multiset")
        for name in sorted(set(before) | set(current)):
            if before.get(name) != current.get(name):
                failures.append(f"{name}: query multiset differs from base {fixture['base_commit']}")
    except (OSError, ValueError, KeyError) as e:
        failures.append(f"before fixture missing or invalid: {e}")
    try:
        groups = robots_groups((root / "robots.txt").read_text(encoding="utf-8"))
        if not groups:
            failures.append("robots.txt: no User-agent groups")
        for agents, disallows in groups:
            for route in ("/dl/", "/buy/"):
                if route not in disallows:
                    failures.append(f"robots.txt: {', '.join(agents)} lacks Disallow: {route}")
    except OSError as e:
        groups = []
        failures.append(f"robots.txt missing or unreadable: {e}")
    if failures:
        print("FIRST-PARTY LINKS: FAIL")
        for failure in failures:
            print(f"  {failure}")
        return 1
    print(f"FIRST-PARTY LINKS: PASS ({links} links, {pages} pages, {len(groups)} robots groups)")
    return 0


if __name__ == "__main__":
    raise SystemExit(check(Path(sys.argv[1] if len(sys.argv) > 1 else ".")))
