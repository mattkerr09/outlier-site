#!/usr/bin/env python3
"""Offline download, maker and Compare checks, with planted failing controls."""
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

import download_size
import typed_url_pages

ROOT = Path(__file__).resolve().parents[1]
BASE = "fbdc4134d"
COMPARE = (
    ("/vs/lm-studio-alternative/", "LM Studio alternative"),
    ("/best/local-ai-for-mac/", "best local AI app for Mac"),
    ("/vs/outlier-vs-ollama/", "Ollama app alternative"),
)
QUESTIONS = ("Is Outlier free?", "What Mac do I need?", "Does it work offline?")


class Visible(HTMLParser):
    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.parts = []
        self.robots = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "meta" and attrs.get("name", "").lower() == "robots":
            self.robots.append(attrs.get("content", "").lower())
        if tag not in self.VOID:
            self.stack.append((tag, tag in {"script", "style", "template"} or "hidden" in attrs))
        self.parts.append(" ")

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break
        self.parts.append(" ")

    def handle_data(self, data):
        if not any(hidden for _, hidden in self.stack):
            self.parts.append(data)

    @property
    def text(self):
        return " ".join("".join(self.parts).split())


def visible(raw):
    parser = Visible()
    parser.feed(raw)
    return parser


def read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


def before(rel):
    return subprocess.run(["git", "show", f"{BASE}:{rel}"], cwd=ROOT,
                          check=True, capture_output=True, text=True).stdout


def check_download(raw):
    page = visible(raw)
    assert not any("noindex" in directive for directive in page.robots), "download is noindex"
    assert '<link rel="canonical" href="https://outlier.host/download/">' in raw, "missing self-canonical"
    article = re.search(r'<article>.*?</article>', raw, re.S)[0]
    text = visible(article).text
    assert len(text.split()) > 300, "download needs over 300 visible article words"
    home = read("index.html")
    requirements = visible(re.search(r'<p class="hw-foot reveal">(.*?)</p>', home, re.S)[1]).text
    assert requirements in text, "requirements differ from home"
    version = re.search(r'"softwareVersion":\s*"([\d.]+)"', home)[1]
    release = download_size.load()
    assert release["version"] == version, "home and release record differ"
    assert f"Current version: v{version}." in text, "current version missing"
    assert f"The installer is about {release['dmg_mb']} MB" in text, "DMG size differs from release"
    assert any(rx.search(article) for rx in download_size.SHAPES), "DMG size is not covered by the size gate"
    assert f"/v{version}/Outlier-{version}-arm64.dmg" in article, "download URL is stale"
    for fact in ("Nano 4B", "Lite 9B", "local chat and saved sessions", "8K context window",
                 "no account", "Quick, Core, Vision and Plus", "coding agent", "local memory",
                 "projects", "128K context window", "on-device fine-tuning", "up to 3 Macs",
                 "future model releases", "no subscription or renewal", "signed and notarized",
                 "drag Outlier to Applications", "brew install --cask outlier-host/tap/outlier",
                 "download a model tier before going offline", "Pro keeps working", "opt-in"):
        assert fact.lower() in text.lower(), f"missing download fact: {fact}"
    # Ignore only the existing sale mount's data attribute and reveal scripts.
    static = re.sub(r'<span data-pbox-founding hidden>.*?</span>', "", raw, flags=re.S)
    static = re.sub(r'<script\b[^>]*>.*?</script>', "", static, flags=re.S)
    static = re.sub(r'data-now="[^"]*"', "", static)
    assert not re.search(r'\$(?:16\.99|34\.99)(?![\d.])', static), "static sale price outside hidden founding span"
    schemas = [json.loads(s) for s in re.findall(r'<script type="application/ld\+json">(.*?)</script>', raw, re.S)]
    faqs = [s for s in schemas if s.get("@type") == "FAQPage"]
    assert len(faqs) == 1, "expected one FAQPage"
    assert tuple(q["name"] for q in faqs[0]["mainEntity"]) == QUESTIONS, "FAQ questions differ"
    for q in faqs[0]["mainEntity"]:
        assert f'<h3>{q["name"]}</h3>' in article, "FAQ question is not visible"
        assert q["acceptedAnswer"]["text"] in text, "FAQ answer differs from visible copy"
    for path in ("/pricing/", "/privacy.html"):
        assert f'href="{path}"' in article, f"missing {path} link"
    old_box = re.search(r'<div class="pbox".*?</div>', before("download/index.html"), re.S)[0]
    assert old_box in raw, "existing product box or buttons changed"
    return len(text.split())


def check_llms(raw):
    section = raw.split("## Who makes Outlier", 1)[1]
    assert "Matthew Kerr, one person in Grand Rapids, Michigan (https://outlier.host/about/)" in section, "maker name or about link missing"
    expected = before("llms.txt").replace("one person in Grand Rapids, Michigan",
        "Matthew Kerr, one person in Grand Rapids, Michigan (https://outlier.host/about/)")
    assert raw == expected, "other llms.txt copy changed"


def check_compare(raw):
    section = re.search(r'<section class="alt" id="compare">.*?</section>', raw, re.S)[0]
    for path, anchor in COMPARE:
        assert re.search(r'<a href="' + re.escape(path) + r'"[^>]*>' + re.escape(anchor) + r'</a>', section), \
            f"missing compare link: {path}"
    added = re.findall(r'    <p class="provenance reveal">Compare local apps:.*?</p>\n', section)
    assert len(added) == 1, "expected one Compare link row"
    # 2026-11-20: later jobs edit the home page too (the /help/ footer link, cx-20261120-0710), so this checks that the
    # Compare row is the ONLY change inside the Compare section, not that the whole page is frozen at this job's base.
    base_section = before("index.html")
    assert section.replace(added[0], "", 1) in base_section, "other Compare-section copy changed"


class DownloadLlmsCompare(unittest.TestCase):
    def control(self, check, good, bad, error, label):
        check(good)
        self.assertNotEqual(good, bad, "CONTROL plant did not land")
        with self.assertRaisesRegex(AssertionError, error):
            check(bad)
        print(f"CONTROL {label}: planted error rejected", flush=True)

    def test_download_and_controls(self):
        raw = read("download/index.html")
        size = download_size.load()["dmg_mb"]
        print(f"download: {check_download(raw)} visible article words", flush=True)
        self.control(check_download, raw, raw.replace('<meta charset="UTF-8">',
                     '<meta charset="UTF-8"><meta name="robots" content="noindex">'), "noindex", "download noindex")
        self.control(check_download, raw, raw.replace('</h1>', '</h1><p>Buy for $16.99</p>', 1),
                     "static sale price", "static $16.99 outside hidden founding span")
        self.control(check_download, raw, raw.replace('data-pbox-founding hidden>', 'data-pbox-founding>', 1),
                     "static sale price", "sale span unhidden")
        self.control(check_download, raw, raw.replace('<h3>Is Outlier free?</h3>', '<h3>Another question?</h3>'),
                     "not visible", "FAQ question missing")
        self.control(check_download, raw, raw.replace(f'The installer is about {size} MB', f'The installer is about {size + 1} MB'),
                     "DMG size differs", "wrong DMG size")

    def test_rebuild_and_check_drift(self):
        for slug in typed_url_pages.PAGES:
            self.assertEqual(read(f"{slug}/index.html"), typed_url_pages.build(slug))
        self.assertEqual(read("pricing/index.html"), before("pricing/index.html"))
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for slug in ("about", *typed_url_pages.PAGES, *getattr(typed_url_pages, "HELP_PAGES", ())):
                target = root / slug / "index.html"
                target.parent.mkdir()
                target.write_text(read(f"{slug}/index.html"), encoding="utf-8")
            with patch.object(typed_url_pages, "ROOT", root):
                self.assertEqual(typed_url_pages.main(["--check"]), 0)
                target = root / "download/index.html"
                planted = target.read_text().replace('Download Outlier</h1>', 'Old download</h1>')
                self.assertNotEqual(target.read_text(), planted)
                target.write_text(planted, encoding="utf-8")
                self.assertEqual(typed_url_pages.main(["--check"]), 1)
                self.assertEqual(target.read_text(), planted)
        print("CONTROL download generator drift: --check fails and writes nothing", flush=True)

    def test_sitemap(self):
        ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        sitemap = ET.fromstring(read("sitemap.xml"))
        entries = [node for node in sitemap.findall("s:url", ns)
                   if node.findtext("s:loc", namespaces=ns) == "https://outlier.host/download/"]
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].findtext("s:lastmod", namespaces=ns), "2026-11-20")

    def test_llms_and_control(self):
        raw = read("llms.txt")
        self.control(check_llms, raw, raw.replace("Matthew Kerr, ", ""), "maker name", "llms.txt missing Matthew Kerr")

    def test_compare_and_controls(self):
        raw = read("index.html")
        for path, _anchor in COMPARE:
            self.control(check_compare, raw, raw.replace(f'href="{path}"', 'href="/vs/"'),
                         "missing compare link", f"missing {path}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
