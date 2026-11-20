#!/usr/bin/env python3
"""Offline help and typed-URL checks, including planted failing controls."""
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET

import typed_url_pages

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://outlier.host"
ANCHORS = ("install", "activate", "refund", "contact", "privacy", "troubleshoot", "updates", "faq")
SAFETY = {"support": "contact", "faq": "faq", "docs": "install",
          "contact": "contact", "refund": "refund", "changelog": "updates"}
RELEASES = "https://github.com/Outlier-host/outlier-app-releases/releases"
GUIDES = ("fix-local-ai-wont-load-mac", "how-much-ram-for-local-ai",
          "free-up-disk-space-for-ai-models", "speed-up-local-ai-mac")


class Node:
    def __init__(self, tag, attrs=(), parent=None):
        self.tag, self.attrs, self.parent = tag, dict(attrs), parent
        self.children = []

    @property
    def hidden(self):
        style = re.sub(r"\s+", "", self.attrs.get("style", "")).lower()
        return (self.tag in {"head", "script", "style", "template"}
                or "hidden" in self.attrs or "display:none" in style or "visibility:hidden" in style
                or bool(self.parent and self.parent.hidden))

    def text(self, visible=True):
        if visible and self.hidden:
            return ""
        return " ".join(" ".join(child.text(visible) if isinstance(child, Node) else child
                                 for child in self.children).split())

    def find(self, tag):
        nodes = []
        for child in self.children:
            if isinstance(child, Node):
                if child.tag == tag:
                    nodes.append(child)
                nodes.extend(child.find(tag))
        return nodes


class Page(HTMLParser):
    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}

    def __init__(self, raw):
        super().__init__(convert_charrefs=True)
        self.root = self.current = Node("root")
        self.feed(raw)

    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs, self.current)
        self.current.children.append(node)
        if tag not in self.VOID:
            self.current = node

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in self.VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        node = self.current
        while node.parent:
            if node.tag == tag:
                self.current = node.parent
                break
            node = node.parent

    def handle_data(self, data):
        self.current.children.append(data)

    @property
    def noindex(self):
        return any(node.attrs.get("name", "").lower() in {"robots", "googlebot", "bingbot"}
                   and "noindex" in node.attrs.get("content", "").lower()
                   for node in self.root.find("meta"))

    @property
    def links(self):
        return [node.attrs.get("href", "") for node in self.root.find("a") if not node.hidden]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def sitemap_urls(raw):
    return [node.text.rstrip("/") for node in ET.fromstring(raw).iter()
            if node.tag == "{http://www.sitemaps.org/schemas/sitemap/0.9}loc"]


def canonical(page, slug):
    urls = [node.attrs.get("href") for node in page.root.find("link")
            if node.attrs.get("rel") == "canonical"]
    assert urls == [f"{SITE}/{slug}/"], f"/{slug}/ needs one self-canonical"


def check_help(raw, sitemap, home):
    page = Page(raw)
    assert not page.noindex, "help is noindex"
    assert not any(node.attrs.get("http-equiv", "").lower() == "refresh"
                   for node in page.root.find("meta")), "help redirects"
    canonical(page, "help")
    assert sitemap_urls(sitemap).count(f"{SITE}/help") == 1, "help missing or repeated in sitemap"
    articles = page.root.find("article")
    assert len(articles) == 1, "expected one help article"
    article = articles[0]
    words = len(article.text().split())
    assert words > 300, "help needs over 300 visible article words"
    for anchor in ANCHORS:
        assert sum(node.attrs.get("id") == anchor and bool(node.text())
                   for node in article.find("h2")) == 1, f"missing visible anchor: {anchor}"
    assert "By Matthew Kerr" in article.text(), "missing visible author"
    assert "Last updated 2026-11-20" in article.text(), "missing visible updated date"
    schemas = [json.loads(node.text(visible=False)) for node in page.root.find("script")
               if node.attrs.get("type") == "application/ld+json"]
    web = [s for s in schemas if s.get("@type") == "WebPage"]
    assert len(web) == 1 and web[0].get("dateModified") == "2026-11-20", "schema date differs"
    assert web[0].get("author", {}).get("name") == "Matthew Kerr", "schema author differs"
    faqs = [s for s in schemas if s.get("@type") == "FAQPage"]
    assert len(faqs) == 1 and 3 <= len(faqs[0]["mainEntity"]) <= 5, "expected 3-5 FAQ questions"
    children = [node for node in article.find("div")[0].children if isinstance(node, Node)]
    start = next(i for i, node in enumerate(children) if node.attrs.get("id") == "faq")
    faq_nodes = children[start + 1:]
    assert len(faq_nodes) == 2 * len(faqs[0]["mainEntity"]), "visible FAQ count differs"
    for i, question in enumerate(faqs[0]["mainEntity"]):
        heading, answer = faq_nodes[2 * i:2 * i + 2]
        assert heading.tag == "h3" and heading.text() == question["name"], "FAQ question differs or hidden"
        assert answer.tag == "p" and answer.text() == question["acceptedAnswer"]["text"], "FAQ answer differs or hidden"
    source_emails = {urlsplit(link).path for link in Page(home).links if link.startswith("mailto:")}
    help_emails = {urlsplit(link).path for link in page.links if link.startswith("mailto:")}
    visible_emails = set(re.findall(r"[\w.+-]+@[\w.-]+\.[a-z]+", article.text()))
    assert len(source_emails) == 1 and help_emails == visible_emails == source_emails, "support email differs from home"
    for link in ("/download/", "/pricing/", "/terms.html", "/privacy.html",
                 "/learn/check-an-ai-app-is-offline-on-mac/", RELEASES,
                 *(f"/how-to/{guide}/" for guide in GUIDES)):
        assert link in page.links, f"missing help link: {link}"
    return words


def check_safety(slug, raw, sitemap):
    page = Page(raw)
    assert page.noindex, f"/{slug}/ needs noindex"
    canonical(page, slug)
    assert f"{SITE}/{slug}" not in sitemap_urls(sitemap), "safety-net page is in sitemap"
    assert f"/help/#{SAFETY[slug]}" in page.links, f"/{slug}/ needs its help section link"
    assert len(page.root.find("h1")) == 1 and page.root.find("h1")[0].text(), "missing safety-net heading"
    assert len(page.root.find("nav")) == len(page.root.find("footer")) == 1, "missing site chrome"
    if slug == "changelog":
        assert RELEASES in page.links, "missing GitHub releases link"


class HelpPages(unittest.TestCase):
    def control(self, check, good, bad, error, label):
        check(good)
        self.assertNotEqual(good, bad, "CONTROL plant did not land")
        with self.assertRaisesRegex(AssertionError, error):
            check(bad)
        print(f"CONTROL {label}: planted error rejected", flush=True)

    def test_help_and_controls(self):
        raw, sitemap, home = read("help/index.html"), read("sitemap.xml"), read("index.html")
        check = lambda value: check_help(value, sitemap, home)
        print(f"help: {check(raw)} visible article words", flush=True)
        self.control(check, raw, raw.replace("</head>", '<meta name="robots" content="noindex"></head>'),
                     "help is noindex", "help noindex")
        self.control(check, raw, raw.replace("matt@outlier.host", "other@example.com"),
                     "support email differs", "wrong support email")
        self.control(check, raw, raw.replace('<h3>How do I activate Pro?</h3>', '<h3 hidden>How do I activate Pro?</h3>'),
                     "FAQ question differs or hidden", "hidden FAQ question")
        self.control(check, raw, raw.replace('    <p>Open Settings &gt; license,', '    <p>Open another menu,'),
                     "FAQ answer differs or hidden", "FAQ answer mismatch")

    def test_unrelated_copy_is_allowed(self):
        sitemap, home = read("sitemap.xml"), read("index.html")
        check_help(read("help/index.html").replace("</article>", "<p>Extra copy.</p></article>"), sitemap, home)
        for slug in SAFETY:
            with self.subTest(page=slug):
                check_safety(slug, read(f"{slug}/index.html").replace(
                    "</footer>", "<p>Extra copy.</p></footer>"), sitemap)

    def test_help_sitemap_removal_control(self):
        raw, sitemap, home = read("help/index.html"), read("sitemap.xml"), read("index.html")
        planted = re.sub(r'<url>\s*<loc>https://outlier.host/help/</loc>.*?</url>', "", sitemap, flags=re.S)
        self.control(lambda value: check_help(raw, value, home), sitemap, planted,
                     "help missing or repeated in sitemap", "help removed from sitemap")

    def test_safety_and_sitemap_control(self):
        sitemap = read("sitemap.xml")
        for slug in SAFETY:
            raw = read(f"{slug}/index.html")
            check_safety(slug, raw, sitemap)
            planted = sitemap.replace('</urlset>', f'<url><loc>{SITE}/{slug}/</loc></url></urlset>')
            self.control(lambda value: check_safety(slug, raw, value), sitemap, planted,
                         "safety-net page is in sitemap", f"/{slug}/ in sitemap")

    def test_incoming_links(self):
        home, about = Page(read("index.html")), Page(read("about/index.html"))
        self.assertEqual(home.links.count("/help/"), 1)
        self.assertEqual(about.links.count("/help/"), 1)
        self.assertIn("/help/", [n.attrs.get("href") for n in home.root.find("footer")[0].find("a")])

    def test_generator_and_drift_control(self):
        slugs = (*typed_url_pages.PAGES, *typed_url_pages.HELP_PAGES)
        self.assertTrue(set(SAFETY) <= set(typed_url_pages.HELP_PAGES))
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for slug in ("about", *slugs):
                target = root / slug / "index.html"
                target.parent.mkdir()
                target.write_text(read("about/index.html") if slug == "about" else typed_url_pages.build(slug), encoding="utf-8")
            with patch.object(typed_url_pages, "ROOT", root):
                self.assertEqual(typed_url_pages.main(["--check"]), 0)
                target = root / "support/index.html"
                planted = target.read_text().replace('/help/#contact', '/help/#install')
                self.assertNotEqual(target.read_text(), planted)
                target.write_text(planted, encoding="utf-8")
                self.assertEqual(typed_url_pages.main(["--check"]), 1)
                self.assertEqual(target.read_text(), planted)
        print("CONTROL safety-net generator drift: --check fails and writes nothing", flush=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
