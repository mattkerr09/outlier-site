#!/usr/bin/env python3
"""Offline regression checks for the seven unranked comparison pages."""
from functools import lru_cache
from html import unescape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess
import unittest
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parent.parent
BASE = "2fa7aa899"
PAGES = (
    "best/index.html",
    "best/local-llm-for-coding/index.html",
    "best/free-local-ai-mac/index.html",
    "best/private-ai-no-cloud/index.html",
    "best/local-ai-for-mac/index.html",
    "best/local-llm-2026/index.html",
    "best/best-ai-assistant-mac-2026/index.html",
)
METHOD = "How this page compares them"
DATE = "2026-11-20"
CLAIMS = re.compile(r'<span\b[^>]*data-claims-checked="[^"]+"[^>]*>.*?</span>', re.S)


@lru_cache(maxsize=None)
def base_text(path):
    return subprocess.run(
        ["git", "show", f"{BASE}:{path}"], cwd=ROOT, check=True,
        capture_output=True, text=True,
    ).stdout


def text(raw):
    return " ".join(unescape(re.sub(r"<[^>]+>", "", raw)).split())


def schemas(raw):
    result = []
    for script in re.findall(r'<script type="application/ld\+json">(.*?)</script>', raw, re.S):
        data = json.loads(script)
        result.extend(data.get("@graph", [data]))
    return result


class Page(HTMLParser):
    def __init__(self, raw):
        super().__init__(convert_charrefs=True)
        self.meta = {}
        self.canonical = []
        self.links = []
        self.feed(raw)
        self.close()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "meta":
            self.meta[attrs.get("name", attrs.get("property"))] = attrs.get("content")
        if tag == "link" and attrs.get("rel") == "canonical":
            self.canonical.append(attrs["href"])
        if "href" in attrs:
            self.links.append(attrs["href"])


def check_unranked(raw):
    page = Page(raw)
    headings = [text(s) for s in re.findall(r'<h[1-6]\b[^>]*>(.*?)</h[1-6]>', raw, re.S)]
    title = re.findall(r'<title>(.*?)</title>', raw, re.S)
    h1 = re.findall(r'<h1\b[^>]*>(.*?)</h1>', raw, re.S)
    assert len(title) == len(h1) == 1, "expected one title and H1"
    for label in title + h1 + [page.meta.get("og:title", ""), page.meta.get("twitter:title", "")]:
        assert label, "missing title"
        assert not re.search(r"\b(?:best|picks?|top|winner)\b", text(label), re.I), "ranked title"
    assert not any(re.match(r"\s*\d+\s*[.)]\s*", h) for h in headings), "numbered option heading"
    prose = unescape(re.sub(r'<(script|style)\b.*?</\1>', '', raw, flags=re.S | re.I))
    assert not re.search(r"\bwinners?\b|\bour pick\b|\bbest overall\b|#1\b", unescape(raw), re.I), "ranking label"
    assert not re.search(r"\bbest\s+(?:for|all-in-one|bundled|polished|open-source|simple)\b", text(prose), re.I), "ranked feature label"
    assert METHOD in headings, "missing comparison method"
    section = re.search(r'<h2>'+METHOD+r'</h2>\s*<p>(.*?)</p>', raw, re.S)
    assert section, "missing comparison method paragraph"
    method = text(section[1])
    assert "M1 Ultra" in method and "64 GB" in method and "Outlier" in method, "missing measured hardware"
    assert '/data/' in section[1], "missing measurement source"
    assert "own" in method and "pages" in method and "date" in method, "missing vendor source limits"
    assert "We have not run the other apps on the same Mac" in method, "missing test limit"
    assert "there is no speed ranking" in method, "missing speed limit"
    assert raw.index('<h1') < section.start(), "method must follow title"
    first_options = re.search(r'<(?:table|div class="cards")', raw)
    if first_options:
        assert section.end() < first_options.start(), "method must precede options"
    assert 'All tools were run on my own Mac' not in raw, "unsupported testing claim"
    assert 'All tools in this roundup have been run' not in raw, "unsupported testing notes"


def rows(raw):
    result = []
    for body in re.findall(r'<tbody>(.*?)</tbody>', raw, re.S):
        table = []
        for row in re.findall(r'<tr>(.*?)</tr>', body, re.S):
            cells = re.findall(r'<td>(.*?)</td>', row, re.S)
            if cells and text(cells[0]).isdigit():
                cells = cells[1:]
            table.append(cells)
        result.append(table)
    return result


def visible_faq(raw):
    return [(text(q), text(a)) for q, a in re.findall(
        r'<div class="faq-item">\s*<h3>(.*?)</h3>\s*<p>(.*?)</p>\s*</div>', raw, re.S)]


def check_faq(raw):
    visible = visible_faq(raw)
    faq = [s for s in schemas(raw) if s.get("@type") == "FAQPage"]
    assert len(faq) == bool(visible), "FAQ schema count differs from visible FAQ"
    if faq:
        structured = [(q["name"], q["acceptedAnswer"]["text"]) for q in faq[0]["mainEntity"]]
        assert structured == visible, "FAQ schema differs from visible text"


class BestPagesUnranked(unittest.TestCase):
    def test_all_seven_pages_are_unranked(self):
        self.assertEqual(len(PAGES), 7)
        for path in PAGES:
            with self.subTest(page=path):
                check_unranked((ROOT / path).read_text())

    def test_original_claim_spans_byline_and_publication_dates(self):
        for path in PAGES:
            with self.subTest(page=path):
                before, after = base_text(path), (ROOT / path).read_text()
                self.assertEqual(CLAIMS.findall(before), CLAIMS.findall(after))
                for byline in re.findall(r'<span class="byline">.*?</span>', before):
                    self.assertIn(byline, after)
                old = [s for s in schemas(before) if "datePublished" in s]
                new = [s for s in schemas(after) if "datePublished" in s]
                self.assertEqual(len(old), len(new))
                for a, b in zip(old, new):
                    self.assertEqual(a["datePublished"], b["datePublished"])
                    self.assertEqual(a.get("author"), b.get("author"))

    def test_modified_dates_and_sitemap(self):
        sitemap = ET.fromstring((ROOT / "sitemap.xml").read_text())
        ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        dates = {u.findtext("s:loc", namespaces=ns): u.findtext("s:lastmod", namespaces=ns)
                 for u in sitemap.findall("s:url", ns)}
        for path in PAGES:
            with self.subTest(page=path):
                raw = (ROOT / path).read_text()
                page = Page(raw)
                self.assertEqual(page.meta["last-modified"], DATE)
                self.assertIn("Last updated " + DATE, text(raw))
                dated = [s for s in schemas(raw) if s.get("@type") in {"Article", "CollectionPage"}]
                self.assertEqual(len(dated), 1)
                self.assertEqual(dated[0]["dateModified"], DATE)
                self.assertEqual(dates[page.canonical[0]], DATE)

    def test_urls_unchanged(self):
        self.assertEqual(
            re.findall(r'<loc>(.*?)</loc>', base_text("sitemap.xml")),
            re.findall(r'<loc>(.*?)</loc>', (ROOT / "sitemap.xml").read_text()),
        )
        self.assertEqual(
            re.findall(r'https://[^\s)]+', base_text("llms.txt")),
            re.findall(r'https://[^\s)]+', (ROOT / "llms.txt").read_text()),
        )
        for path in PAGES:
            with self.subTest(page=path):
                before, after = Page(base_text(path)), Page((ROOT / path).read_text())
                self.assertEqual(before.canonical, after.canonical)
                self.assertEqual(before.meta["og:url"], after.meta["og:url"])
                self.assertTrue(set(before.links) <= set(after.links), "existing link removed")

    def test_tables_are_alphabetical_and_rival_cells_unchanged(self):
        for path in PAGES:
            with self.subTest(page=path):
                old_tables = rows(base_text(path))
                new_tables = rows((ROOT / path).read_text())
                self.assertEqual(len(old_tables), len(new_tables))
                for old, new in zip(old_tables, new_tables):
                    names = [text(row[0]) for row in new]
                    self.assertEqual(names, sorted(names, key=str.casefold))
                    old_cells = {text(row[0]): row for row in old if not text(row[0]).startswith("Outlier")}
                    new_cells = {text(row[0]): row for row in new if not text(row[0]).startswith("Outlier")}
                    self.assertEqual(old_cells, new_cells)

    def test_app_descriptions_are_alphabetical_and_rival_prose_unchanged(self):
        path = "best/local-ai-for-mac/index.html"
        raw = (ROOT / path).read_text()
        names = re.findall(r'<h2>(GPT4All|Jan|LM Studio|Ollama|Outlier):', raw)
        self.assertEqual(names, ["GPT4All", "Jan", "LM Studio", "Ollama", "Outlier"])
        assistant = (ROOT / "best/best-ai-assistant-mac-2026/index.html").read_text()
        self.assertEqual(re.findall(r'<h3>([^<]+)</h3>', assistant)[:-1], [
            "Apple Intelligence", "ChatGPT", "Claude", "Copilot", "Google AI Plus",
            "Jan", "LM Studio", "Ollama", "Outlier",
        ])
        for path, tag, rival in (
            (path, "h2", r'(?:\d+\. )?(?:GPT4All|Jan|LM Studio|Ollama):[^<]+'),
            ("best/best-ai-assistant-mac-2026/index.html", "h3", r'Jan|LM Studio|Ollama|Apple Intelligence|ChatGPT|Claude|Copilot|Google AI Plus'),
        ):
            before, after = base_text(path), (ROOT / path).read_text()
            blocks = re.findall(r'<'+tag+r'>(?:'+rival+r')</'+tag+r'>(.*?)(?=<h[23]>|\Z)', before, re.S)
            self.assertTrue(blocks)
            for block in blocks:
                for paragraph in re.findall(r'<p>.*?</p>', block, re.S):
                    self.assertIn(paragraph, after, "rival description changed")

    def test_sale_wording_unchanged(self):
        for path in PAGES:
            with self.subTest(page=path):
                before, after = base_text(path), (ROOT / path).read_text()
                pattern = r'<span data-pbox-(?:regular|founding)\b[^>]*>.*?</span>'
                self.assertEqual(re.findall(pattern, before), re.findall(pattern, after))
                self.assertEqual(
                    re.findall(r'<div data-founding\b[^>]*></div>', before),
                    re.findall(r'<div data-founding\b[^>]*></div>', after),
                )

    def test_faq_schema_matches_visible_text_exactly(self):
        for path in PAGES:
            with self.subTest(page=path):
                check_faq((ROOT / path).read_text())

    def test_controls_reject_rankings_and_missing_method(self):
        raw = (ROOT / "best/local-ai-for-mac/index.html").read_text()
        for plant in (
            raw.replace('<title>', '<title>Best '),
            raw.replace('<h1>', '<h1>Top picks: '),
            raw.replace('content="Local AI apps for Mac compared in 2026"', 'content="Our pick: best overall"'),
            raw.replace('<h2>GPT4All:', '<h2>1. GPT4All:'),
            raw.replace('GPT4All: simple', 'GPT4All: winner'),
            raw.replace('GPT4All: simple', 'GPT4All: our pick'),
            raw.replace('GPT4All: simple', 'GPT4All: best overall'),
            raw.replace('GPT4All: simple', 'GPT4All: #1'),
            raw.replace(METHOD, 'Method removed'),
            raw.replace('there is no speed ranking', 'speed details'),
        ):
            with self.assertRaises(AssertionError):
                check_unranked(plant)
        plant = raw.replace('<p>Yes. Ollama, Jan, and GPT4All', '<p>Changed. Ollama, Jan, and GPT4All')
        with self.assertRaises(AssertionError):
            check_faq(plant)


if __name__ == "__main__":
    unittest.main()
