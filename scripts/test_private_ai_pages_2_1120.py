#!/usr/bin/env python3
"""Offline checks for the second three private AI articles, with failing controls."""
from html import unescape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import unittest
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parent.parent
PAGES = (
    "learn/paste-passwords-or-api-keys-into-chatgpt/index.html",
    "learn/can-chrome-extensions-read-chatgpt-chats/index.html",
    "learn/is-local-ai-safe-from-prompt-injection/index.html",
)
SOURCES = {
    "https://thehackernews.com/2026/01/two-chrome-extensions-caught-stealing.html",
    "https://www.bleepingcomputer.com/news/security/notion-says-fireworks-breach-exposed-customer-ai-chat-transcripts/",
}
BANNED = ("can't leak", "cannot leak", "unhackable", "100% secure", "100% safe",
          "immune", "can't be hijacked", "HIPAA", "GDPR compliant",
          "removed from the Chrome Web Store")
QUICK = re.compile(r'<div class="quick-answer">.*?</div>', re.S)


class Visible(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.links = []
        self.skip = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        for key in ("href", "src", "action"):
            if key in attrs:
                self.links.append(attrs[key])
        if tag in {"script", "style", "template"}:
            self.skip.append(tag)
        if tag in {"p", "li", "td", "th", "div", "br", "h1", "h2", "pre"}:
            self.parts.append(" ")

    def handle_endtag(self, tag):
        if self.skip and tag == self.skip[-1]:
            self.skip.pop()
        if tag in {"p", "li", "td", "th", "div", "h1", "h2", "pre"}:
            self.parts.append(" ")

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)

    @property
    def text(self):
        return " ".join("".join(self.parts).split())


def visible(raw):
    page = Visible()
    page.feed(raw)
    page.close()
    return page


def check_page(raw, rel):
    matches = list(QUICK.finditer(raw))
    assert len(matches) == 1, "expected one quick answer"
    quick = matches[0]
    assert raw.index("<h1") < quick.start() < quick.end() < raw.index("<h2"), \
        "quick answer must precede the first h2"
    paragraphs = re.findall(r"<p>(.*?)</p>", quick.group(), re.S)
    assert len(paragraphs) == 1, "expected one answer paragraph"
    answer = visible(paragraphs[0]).text
    assert 2 <= len(re.split(r"(?<=[.!?])\s+(?=[A-Z])", answer)) <= 4, \
        "expected two to four answer sentences"
    article = re.search(r"<article>.*?</article>", raw, re.S)
    assert article and len(visible(article.group()).text.split()) > 300, "article needs substance"
    page = visible(raw)
    # Include metadata and structured data as well as visible prose.
    all_text = (page.text + " " + unescape(raw)).replace("’", "'").casefold()
    for phrase in BANNED:
        assert phrase.casefold() not in all_text, f"forbidden phrase: {phrase}"
    for href in page.links:
        url = urlsplit(href)
        assert not url.query, f"link has query parameters: {href}"
        if url.scheme or url.netloc:
            assert url.scheme == "https" and (url.hostname == "outlier.host" or href in SOURCES), \
                f"unknown external URL: {href}"
    for paragraph in re.findall(r"<p\b[^>]*>.*?</p>", raw, re.S):
        if SOURCES.intersection(visible(paragraph).links):
            assert "read 2026-11-20 by our reviewer" in visible(paragraph).text, \
                "external source needs reviewer read date"
    paths = {urlsplit(href).path for href in page.links}
    assert {"/download/", "/privacy.html"} <= paths, "missing download/privacy link"
    assert "Last updated 2026-11-20" in page.text, "missing visible update date"
    assert 'name="last-modified" content="2026-11-20"' in raw, "missing meta date"
    schemas = [json.loads(s) for s in re.findall(r'<script type="application/ld\+json">(.*?)</script>', raw, re.S)]
    articles = [s for s in schemas if s.get("@type") == "Article"]
    assert len(articles) == 1, "expected Article schema"
    schema = articles[0]
    assert schema["dateModified"] == schema["datePublished"] == "2026-11-20", "schema date mismatch"
    assert schema["author"] == {"@type": "Person", "name": "Matthew Kerr", "url": "https://outlier.host/about/"}, \
        "author must match existing form"
    title = visible(re.search(r"<h1>(.*?)</h1>", raw, re.S).group(1)).text
    assert schema["headline"] == title, "schema headline mismatch"
    url = "https://outlier.host/" + rel.removesuffix("index.html")
    assert schema["mainEntityOfPage"]["@id"] == url, "schema URL mismatch"
    breadcrumbs = [s for s in schemas if s.get("@type") == "BreadcrumbList"]
    assert len(breadcrumbs) == 1 and breadcrumbs[0]["itemListElement"][-1]["item"] == url, \
        "missing matching breadcrumbs"
    return answer


def check_extensions(raw):
    text = visible(re.search(r"<article>.*?</article>", raw, re.S).group()).text
    assert set(re.findall(r"([\d,]+) users\b", text)) == {"600,000", "300,000", "900,000"}, \
        "extension user figures must be exactly 600,000 / 300,000 / 900,000"
    for name, count in (
        ("Chat GPT for Chrome with GPT-5, Claude Sonnet & DeepSeek AI", "600,000"),
        ("AI Sidebar with Deepseek, ChatGPT, Claude, and more", "300,000"),
    ):
        assert f"{name}: {count} users." in text, "extension name/count mismatch"
    assert re.findall(r"every \d+ minutes", text) == ["every 30 minutes"], \
        "extension cadence must be every 30 minutes"
    assert next(url for url in SOURCES if "thehackernews.com" in url) in visible(raw).links, \
        "missing extension source"


class PrivateAIPages2(unittest.TestCase):
    def test_pages(self):
        for rel in PAGES:
            with self.subTest(page=rel):
                raw = (ROOT / rel).read_text()
                check_page(raw, rel)
                print(f"{rel}: answer, substance, sources, dates and schema pass", flush=True)
        check_extensions((ROOT / PAGES[1]).read_text())
        self.assertIn(next(url for url in SOURCES if "bleepingcomputer.com" in url),
                      visible((ROOT / PAGES[0]).read_text()).links)

    def test_controls(self):
        for rel in PAGES:
            with self.subTest(page=rel):
                raw = (ROOT / rel).read_text()
                plants = [(f"<p>{phrase}.</p>", "forbidden phrase") for phrase in BANNED]
                plants += [
                    ('<a href="https://example.invalid/unknown">Unknown source</a>', "unknown external URL"),
                    ('<a href="https://outlier.host/?utm_source=test">Tracked link</a>', "query parameters"),
                    ('<meta name="description" content="100% safe">', "forbidden phrase"),
                    ('<p>It can&#39;t leak.</p>', "forbidden phrase"),
                ]
                for plant, error in plants:
                    planted = raw.replace("</article>", plant + "</article>", 1)
                    self.assertNotEqual(raw, planted, "control plant did not land")
                    with self.assertRaisesRegex(AssertionError, error):
                        check_page(planted, rel)
                quick = QUICK.search(raw).group()
                moved = raw.replace(quick, "", 1).replace("</article>", quick + "</article>", 1)
                with self.assertRaisesRegex(AssertionError, "precede the first h2"):
                    check_page(moved, rel)
                short = re.sub(r"<p>.*?</p>", "<p>Yes.</p>", quick, flags=re.S)
                with self.assertRaisesRegex(AssertionError, "two to four"):
                    check_page(raw.replace(quick, short, 1), rel)
                wrong_date = raw.replace('"dateModified": "2026-11-20"', '"dateModified": "2026-11-19"')
                self.assertNotEqual(raw, wrong_date, "date control did not land")
                with self.assertRaisesRegex(AssertionError, "schema date mismatch"):
                    check_page(wrong_date, rel)
                print(f"CONTROLS {rel}: all banned phrases, unknown URL, tracked link, metadata, encoded claim, moved/short answer and wrong date fail", flush=True)
        raw = (ROOT / PAGES[1]).read_text()
        for original, wrong in (("600,000", "600,001"), ("300,000", "300,001"),
                                ("900,000", "900,001"), ("every 30 minutes", "every 31 minutes")):
            self.assertIn(original, raw)
            with self.assertRaisesRegex(AssertionError, "figures|cadence"):
                check_extensions(raw.replace(original, wrong))
        for rel in PAGES[:2]:
            raw = (ROOT / rel).read_text()
            wrong_date = raw.replace("read 2026-11-20 by our reviewer", "read 2026-11-19 by our reviewer")
            self.assertNotEqual(raw, wrong_date, "source-date control did not land")
            with self.assertRaisesRegex(AssertionError, "reviewer read date"):
                check_page(wrong_date, rel)
        print("CONTROLS: three altered extension figures, altered cadence and stale source read dates fail", flush=True)

    def test_discovery(self):
        from xml.etree import ElementTree
        sitemap = ElementTree.fromstring((ROOT / "sitemap.xml").read_text())
        ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        for rel in PAGES:
            path = "/" + rel.removesuffix("index.html")
            for hub in ("learn/index.html", "learn/is-local-ai-safe/index.html"):
                links = visible((ROOT / hub).read_text()).links
                self.assertIn(path, {urlsplit(href).path for href in links}, hub)
            entries = [node for node in sitemap.findall("s:url", ns)
                       if node.findtext("s:loc", namespaces=ns) == "https://outlier.host" + path]
            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0].findtext("s:lastmod", namespaces=ns), "2026-11-20")


if __name__ == "__main__":
    unittest.main(verbosity=2)
