#!/usr/bin/env python3
"""Offline checks for the three private AI articles, with failing controls."""
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess
import unittest
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parent.parent
BASE = "a576aa93f530ac049539e0943e5f3eac7c291477"
PAGES = (
    "learn/fireworks-ai-breach-notion-ai-chats/index.html",
    "learn/ai-chatbots-share-chats-with-trackers/index.html",
    "learn/check-an-ai-app-is-offline-on-mac/index.html",
)
ALLOWED = {*PAGES, "learn/index.html", "learn/is-local-ai-safe/index.html",
           "index.html", "sitemap.xml", "scripts/test_private_ai_pages_1120.py"}
# Four of the supplied URLs. The optional press comparison is not used.
SOURCES = {
    "https://www.bleepingcomputer.com/news/security/notion-says-fireworks-breach-exposed-customer-ai-chat-transcripts/",
    "https://gizmodo.com/hackers-stole-thousands-of-uber-drivers-data-through-an-ai-startup-2000839947",
    "https://arxiv.org/abs/2610.37467",
    "https://networks.imdea.org/your-conversations-with-ai-may-not-be-as-private-as-you-think/",
}
BANNED = ("can't leak", "cannot leak", "unhackable", "100% secure",
          "completely secure", "immune to prompt injection", "HIPAA",
          "GDPR compliant", "cloud AI leaks")
SENTENCE = "Your chats are never on our servers, because we never receive them."
HOME_ANCHOR = "Your prompts, files, code, and chat history stay on your disk, under your control."
COMMAND = "lsof -a -p $(pgrep -x outlier-cli) -i -n -P"
QUICK = re.compile(r'<div class="quick-answer">.*?</div>', re.S)
CAPTURE = re.compile(r'<div class="receipts" id="capture">.*?</div>', re.S)


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


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, check=True,
                          capture_output=True, text=True).stdout


def check_capture(raw, home):
    capture = CAPTURE.search(raw)
    assert capture, "missing dated capture"
    text = visible(capture.group()).text
    home_text = visible(home).text
    head = re.search(r"Captured (\d{4}-\d{2}-\d{2}) on Outlier ([\d.]+) while Core was answering, web search off\.", home_text)
    assert head, "home capture not found"
    date, version = head.groups()
    assert re.findall(r"Captured (\d{4}-\d{2}-\d{2}) on Outlier ([\d.]+)", text) == [(date, version)], \
        "capture date/version differ from home"
    assert "while Core was answering, web search off." in text, "missing capture conditions"
    assert "A past capture, not a live reading." in text, "missing past-capture limit"
    counts = re.search(r"sampled (\d+)× across a (\d+)s answer .*?sockets leaving this Mac: (\d+)", home_text)
    assert counts, "home capture counts not found"
    samples, seconds, sockets = counts.groups()
    assert (date, version, samples, seconds, sockets) == ("2026-11-04", "1.11.992", "22", "24", "0"), \
        "home measurement changed"
    actual = re.search(r"sampled (\d+) times across a (\d+)s answer\. Sockets leaving this Mac: (\d+)\.", text)
    assert actual and actual.groups() == counts.groups(), "capture counts differ from home"
    assert "127.0.0.1" in text, "missing local address"
    assert COMMAND in visible(raw).text, "missing exact lsof command"


def check_page(raw, home):
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
    assert SENTENCE in answer, "missing first-screen server statement"
    article = re.search(r"<article>.*?</article>", raw, re.S)
    assert article and len(visible(article.group()).text.split()) > 300, "article needs substance"
    text = visible(raw).text.replace("’", "'").casefold()
    # Check raw text too, including descriptions and structured data.
    from html import unescape
    all_text = text + " " + unescape(raw).replace("’", "'").casefold()
    for phrase in BANNED:
        assert phrase.casefold() not in all_text, f"forbidden phrase: {phrase}"
    page = visible(raw)
    for href in page.links:
        url = urlsplit(href)
        assert not url.query, f"link has query parameters: {href}"
        if url.scheme or url.netloc:
            assert url.scheme == "https" and (url.hostname == "outlier.host" or href in SOURCES), \
                f"unknown external URL: {href}"
    paths = {urlsplit(href).path for href in page.links}
    assert {"/download/", "/privacy.html"} <= paths, "missing download/privacy link"
    assert "Last updated 2026-11-20" in page.text, "missing visible update date"
    assert 'name="last-modified" content="2026-11-20"' in raw, "missing meta date"
    schemas = [json.loads(s) for s in re.findall(r'<script type="application/ld\+json">(.*?)</script>', raw, re.S)]
    articles = [s for s in schemas if s.get("@type") == "Article"]
    assert len(articles) == 1, "expected Article schema"
    article = articles[0]
    assert article["dateModified"] == article["datePublished"] == "2026-11-20", "schema date mismatch"
    assert article["author"] == {"@type": "Person", "name": "Matthew Kerr", "url": "https://outlier.host/about/"}, \
        "author must match existing form"
    assert any(s.get("@type") == "BreadcrumbList" for s in schemas), "missing breadcrumbs"
    check_capture(raw, home)
    return quick


def check_home(before, after):
    assert before.count(HOME_ANCHOR) == 1, "home insertion anchor changed"
    assert SENTENCE not in before, "sentence already existed in base"
    assert after == before.replace(HOME_ANCHOR, HOME_ANCHOR + " " + SENTENCE, 1), \
        "home must gain exactly the one sentence"
    section = re.search(r'<section id="why">.*?</section>', after, re.S).group()
    assert SENTENCE in section, "sentence must be in Private by default"


class PrivateAIPages(unittest.TestCase):
    def test_pages(self):
        home = (ROOT / "index.html").read_text()
        for rel in PAGES:
            with self.subTest(page=rel):
                check_page((ROOT / rel).read_text(), home)
                print(f"{rel}: answer, sources, dates and capture pass", flush=True)

    def test_controls(self):
        home = (ROOT / "index.html").read_text()
        for rel in PAGES:
            with self.subTest(page=rel):
                raw = (ROOT / rel).read_text()
                for plant, error in (
                    ("<p>This can't leak.</p>", "forbidden phrase"),
                    ('<a href="https://example.invalid/unknown">Unknown source</a>', "unknown external URL"),
                ):
                    planted = raw.replace("</article>", plant + "</article>", 1)
                    self.assertNotEqual(raw, planted, "control plant did not land")
                    with self.assertRaisesRegex(AssertionError, error):
                        check_page(planted, home)
                quick = QUICK.search(raw).group()
                moved = raw.replace(quick, "", 1).replace("</article>", quick + "</article>", 1)
                with self.assertRaisesRegex(AssertionError, "precede the first h2"):
                    check_page(moved, home)
                for original, wrong in (("2026-11-04", "2026-11-05"), ("1.11.992", "1.11.993"),
                                        ("sampled 22 times", "sampled 23 times"),
                                        ("24s answer", "25s answer"),
                                        ("Sockets leaving this Mac: 0.", "Sockets leaving this Mac: 1.")):
                    self.assertIn(original, raw)
                    with self.assertRaisesRegex(AssertionError, "capture (date/version|counts)"):
                        check_page(raw.replace(original, wrong), home)
                print(f"CONTROLS {rel}: banned claim, unknown URL, moved answer and five altered capture facts fail", flush=True)

    def test_home_only_sentence(self):
        before = git("show", f"{BASE}:index.html")
        after = (ROOT / "index.html").read_text()
        check_home(before, after)
        with self.assertRaisesRegex(AssertionError, "exactly the one sentence"):
            check_home(before, after.replace("</body>", "<p>Extra copy.</p></body>"))

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

    def test_changed_paths(self):
        changed = set(git("diff", "--name-only", BASE, "--").splitlines())
        changed.update(git("ls-files", "--others", "--exclude-standard").splitlines())
        self.assertFalse(changed - ALLOWED, f"out-of-scope changes: {changed - ALLOWED}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
