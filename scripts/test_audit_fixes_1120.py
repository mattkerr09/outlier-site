#!/usr/bin/env python3
"""Offline audit regression checks. Each fix has a planted failing CONTROL."""
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import sitemap_lastmod
import typed_url_pages

ROOT = Path(__file__).resolve().parents[1]
SALE = "Black Friday sale: $16.99 once through December 2. Then $39"
BUNDLE = "Black Friday sale: $34.99 once through December 2. Then $79"
CORRECTION = "Both removed. Outlier has one price, paid once: $39 once; the Black Friday sale lowers it through December 2."
TERMS_UPDATED = ('<p class="updated">Last updated: 2026-11-04 (one licence, one price, up to 3 Macs at a time; '
                 '2026-11-02: a lost or dead Mac, we release its seat) · Kerr &amp; Company LLC, Grand Rapids, MI</p>')
TERMS_CHANGED = ('<p class="updated">Changed 2026-11-04: "lifetime" means the same for every Outlier lifetime licence, '
                 'the current licence and the earlier Founding 200 and Founders 500 tiers: the lifetime of the '
                 "Outlier product, with 90 days' notice and a final binary release if it is ever sunset.</p>")


class Visible(HTMLParser):
    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag not in self.VOID:
            self.stack.append((tag, tag in {"script", "style", "template"} or "hidden" in dict(attrs)))
        if tag in {"p", "div", "li", "td", "th", "h1", "h2", "h3", "br"}:
            self.parts.append(" ")

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break
        if tag in {"p", "div", "li", "td", "th", "h1", "h2", "h3"}:
            self.parts.append(" ")

    def handle_data(self, data):
        if not any(off for _, off in self.stack):
            self.parts.append(data)


def visible(raw):
    parser = Visible()
    parser.feed(raw)
    return " ".join("".join(parser.parts).split())


def read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


def check_pricing(raw):
    assert not re.search(r'<meta\b[^>]*name="robots"[^>]*noindex', raw), "pricing is noindex"
    assert '<link rel="canonical" href="https://outlier.host/pricing/">' in raw
    article = re.search(r'<article>.*?</article>', raw, re.S)[0]
    text = visible(article)
    assert len(text.split()) >= 400, "pricing has too little content"
    for fact in ("Nano 4B", "Lite 9B", "Quick, Core, Vision and Plus", "8K context window",
                 "128K context window", "up to 3 Macs", "future model releases", "no subscription",
                 "30 days, no questions asked", "$39 once", "$79 once",
                 "Apple Silicon (M1 or newer) on macOS 15 or later, which is a free update."):
        assert fact in text, f"missing pricing fact: {fact}"
    spans = re.findall(r'<span data-pbox-founding hidden>(.*?)</span>', raw, re.S)
    assert all(any(line in span for span in spans) for line in (SALE, BUNDLE)), "pricing sale lines must be in hidden founding spans"
    static = re.sub(r'<span data-pbox-founding hidden>.*?</span>', "", raw, flags=re.S)
    static = re.sub(r'<script\b[^>]*>.*?</script>', "", static, flags=re.S)
    static = re.sub(r'data-now="[^"]*"', "", static)
    assert not re.search(r'\$(?:16\.99|34\.99)(?![\d.])', static), "static pricing sale price outside hidden founding spans"
    schemas = [json.loads(s) for s in re.findall(r'<script type="application/ld\+json">(.*?)</script>', raw, re.S)]
    faq = next(s for s in schemas if s.get("@type") == "FAQPage")
    assert [q["name"] for q in faq["mainEntity"]] == [
        "Is it a subscription?", "What happens after December 2?", "Is there a free version?"]
    for q in faq["mainEntity"]:
        assert q["name"] in text and q["acceptedAnswer"]["text"] in text, "FAQ does not match visible copy"


def check_correction(raw):
    assert CORRECTION in visible(raw), "benchmark correction is stale"
    assert "$49 once" not in visible(raw), "benchmark still says $49 once"


def check_terms(raw):
    assert "$49" not in raw, "terms still say $49"
    assert raw.count(TERMS_UPDATED) == 1, "terms Last updated note differs"
    assert raw.count(TERMS_CHANGED) == 1, "terms Changed note differs"


def check_thanks(raw):
    lines = [s for s in re.findall(r'<p><strong>.*?</p>', raw, re.S) if "once" in s]
    assert len(lines) == 2
    # 2026-11-20 (Matthew, 13:04:44Z): the sale line carries no comparison ("% off", "November price") any more.
    expected = (("Crisp Video", "$29", "$9.99", "$29"),
                ("Check Engine SEO", "$39", "$19.99", "$39"))
    for line, (name, regular, sale, later) in zip(lines, expected):
        assert name in line
        assert re.findall(r'\$\d+(?:\.\d+)?', line) == [regular, sale, later], "cross-sell prices differ"
        assert f"Black Friday sale: {sale} once through December 2. Then {later}" in line
        assert "% off" not in line and "November price" not in line


def check_home(raw):
    assert "reaches Matthew directly" in raw and "reaches Matt directly" not in raw, "maker name is stale"
    assert "the current $39 regular price and $16.99 sale price" in raw, "instalment comment is stale"
    assert "$39 and $16.99 are under Dodo's $50.01" in raw, "BNPL comment is stale"
    comments = " ".join(re.findall(r'/\*.*?\*/|//[^\n]*', raw, re.S))
    assert not re.search(r'\$49(?![\d.])', comments), "comment still says $49"



class AuditFixes(unittest.TestCase):
    def control(self, check, good, bad, label):
        check(good)
        self.assertNotEqual(good, bad, "CONTROL plant did not land")
        with self.assertRaises(AssertionError):
            check(bad)
        print(f"CONTROL {label}: planted error rejected", flush=True)

    def test_1_pricing_and_rebuild(self):
        raw = read("pricing/index.html")
        self.control(check_pricing, raw, raw.replace('<meta charset="UTF-8">',
                     '<meta charset="UTF-8"><meta name="robots" content="noindex">'), "pricing noindex")
        self.control(check_pricing, raw, raw.replace('<h3>Is it a subscription?</h3>',
                     '<h3>Another question?</h3>'), "FAQ not visible")
        for price in ("$16.99", "$34.99"):
            self.control(check_pricing, raw, raw.replace('<h1>Outlier pricing</h1>',
                         f'<h1>Outlier pricing</h1><p>{price}</p>'), f"static pricing {price}")
        self.control(check_pricing, raw, raw.replace('data-pbox-founding hidden>',
                     'data-pbox-founding>', 1), "pricing sale span visible")
        self.control(check_pricing, raw, raw.replace("Outlier is $39 once and the bundle is $79 once",
                     "Outlier is $16.99 once and the bundle is $34.99 once"), "FAQ sale prices")
        self.assertIn('<loc>https://outlier.host/pricing/</loc>', read("sitemap.xml"))
        # Exercise --check's exit code on drift without writing to the checkout.
        with tempfile.TemporaryDirectory() as tmp:
            for slug in ("about", *typed_url_pages.PAGES, *typed_url_pages.HELP_PAGES):
                target = Path(tmp) / slug / "index.html"
                target.parent.mkdir()
                target.write_text(read("about/index.html") if slug == "about" else typed_url_pages.build(slug))
            target = Path(tmp) / "pricing/index.html"
            planted = target.read_text().replace("Outlier pricing</h1>", "Old pricing</h1>")
            self.assertNotEqual(planted, target.read_text())
            with patch.object(typed_url_pages, "ROOT", Path(tmp)):
                self.assertEqual(typed_url_pages.main(["--check"]), 0)
                target.write_text(planted)
                self.assertEqual(typed_url_pages.main(["--check"]), 1)
            self.assertEqual(target.read_text(), planted)
        print(f"pricing: {len(visible(re.search(r'<article>.*?</article>', raw, re.S)[0]).split())} visible article words")

    def test_2_benchmark_correction_only(self):
        rel = "data/local-ai-benchmarks-mac-2026/index.html"
        raw = read(rel)
        self.control(check_correction, raw, raw.replace('paid once: <strong>$39 once</strong>',
                     'paid once: <strong>$49 once</strong>'), "benchmark $49 once")
        self.control(check_correction, raw, raw.replace(
            'Both removed. Outlier has one price, paid once: <strong>$39 once</strong>; the Black Friday sale lowers it through December 2.',
            'Both removed; <strong>$49 once</strong> is the only Outlier price.'),
            "restored old benchmark correction")

    def test_3_terms_prices_only(self):
        raw = read("terms.html")
        self.control(check_terms, raw, raw.replace("one licence, one price", "one licence, $49", 1), "terms $49")
        self.control(check_terms, raw, raw.replace("one licence, one price", "one licence, same price", 1), "terms Last updated note")
        self.control(check_terms, raw, raw.replace("the current licence and the earlier", "the current licence and earlier", 1), "terms Changed note")
        if (ROOT / "terms/index.html").exists():
            check_terms(read("terms/index.html"))

    def test_4_crisp_and_other_receipt_prices(self):
        raw = read("thank-you.html")
        self.control(check_thanks, raw, raw.replace("Then $29", "Then $19", 1), "Crisp Then $19")
        self.control(check_thanks, raw, raw.replace('data-pbox-regular>$29 once', 'data-pbox-regular>$19 once', 1), "Crisp regular $19")

    def test_5_home_name_and_comments(self):
        raw = read("index.html")
        self.control(check_home, raw, raw.replace("reaches Matthew directly", "reaches Matt directly"), "Matt directly")
        self.control(check_home, raw, raw.replace("the current $39 regular price", "the current $49 regular price"), "stale price comment")

    def test_unrelated_copy_is_allowed(self):
        for check, rel in ((check_pricing, "pricing/index.html"),
                           (check_correction, "data/local-ai-benchmarks-mac-2026/index.html"),
                           (check_terms, "terms.html"), (check_thanks, "thank-you.html"),
                           (check_home, "index.html")):
            with self.subTest(page=rel):
                check(read(rel).replace("</body>", "<p>Extra copy.</p></body>"))

    def test_7_sitemap_dates_and_control(self):
        # Check dates on this job's pages without gating unrelated sitemap entries.
        from xml.etree import ElementTree
        ns = sitemap_lastmod.NS
        entries = ElementTree.fromstring(read("sitemap.xml")).findall("s:url", ns)
        for rel in ("index.html", "pricing/index.html", "terms.html",
                    "data/local-ai-benchmarks-mac-2026/index.html"):
            date = sitemap_lastmod.page_date(read(rel))
            url = "https://outlier.host/" + rel.removesuffix("index.html")
            matches = [node for node in entries if node.findtext("s:loc", namespaces=ns) == url]
            self.assertEqual(len(matches), 1, url)
            if date:
                self.assertEqual(matches[0].findtext("s:lastmod", namespaces=ns), date, url)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "index.html").write_text('<script type="application/ld+json">{"@graph":[{"dateModified":"2026-11-20T01:00:00Z"}]}</script><p>Last updated 2026-11-19</p>')
            (root / "visible.html").write_text('<p>Last updated: <time>2026-11-18</time></p>')
            (root / "undated.html").write_text('<p>No dateline.</p><p hidden>Last updated 2026-11-20</p>')
            sitemap = ('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
                       '<url><loc>https://outlier.host/</loc><lastmod>2026-11-20</lastmod></url>'
                       '<url><loc>https://outlier.host/visible.html</loc><lastmod>2026-11-18</lastmod></url>'
                       '<url><loc>https://outlier.host/undated.html</loc><lastmod>2026-09-01</lastmod></url></urlset>')
            target = root / "sitemap.xml"
            target.write_text(sitemap)
            command = [sys.executable, str(ROOT / "scripts/sitemap_lastmod.py"), str(root)]
            self.assertEqual(subprocess.run(command + ["--check"], capture_output=True).returncode, 0)
            planted = sitemap.replace('<lastmod>2026-11-20</lastmod>', '<lastmod>2026-11-01</lastmod>')
            target.write_text(planted)
            self.assertEqual(subprocess.run(command + ["--check"], capture_output=True).returncode, 1)
            self.assertEqual(target.read_text(), planted, "--check changed the sitemap")
            print("CONTROL lagging lastmod: --check exits 1 and writes nothing", flush=True)
            # Write mode sets an ahead date back to the page's own date too.
            target.write_text(planted.replace('2026-11-18</lastmod>', '2026-12-01</lastmod>'))
            self.assertEqual(subprocess.run(command, capture_output=True).returncode, 0)
            self.assertEqual(target.read_text(), sitemap)


if __name__ == "__main__":
    unittest.main(verbosity=2)
