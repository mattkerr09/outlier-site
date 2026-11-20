#!/usr/bin/env python3
"""Offline audit regression checks. Each fix has a planted failing CONTROL."""
import datetime as dt
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import product_box
import sitemap_lastmod
import typed_url_pages

ROOT = Path(__file__).resolve().parents[1]
BASE = "9d81bb8ef17f754c4b715b18ae59d9e456fd62a4"
SALE = "Black Friday sale: $16.99 once, 31% off our November price of $24.50, through December 2. Then $39"
BUNDLE = "Black Friday sale: $34.99 once, 29% off our November price of $49.50, through December 2. Then $79"
CORRECTION = "Both removed. One-time price only: $39 once, $16.99 in the Black Friday sale through December 2."
TERMS_PRICE = "$39 once ($16.99 in the Black Friday sale through December 2, 2026)"


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


def before(rel):
    return subprocess.run(["git", "show", f"{BASE}:{rel}"], cwd=ROOT,
                          check=True, capture_output=True, text=True).stdout


def check_pricing(raw):
    assert not re.search(r'<meta\b[^>]*name="robots"[^>]*noindex', raw), "pricing is noindex"
    assert '<link rel="canonical" href="https://outlier.host/pricing/">' in raw
    article = re.search(r'<article>.*?</article>', raw, re.S)[0]
    text = visible(article)
    assert len(text.split()) >= 400, "pricing has too little content"
    for fact in ("Nano 4B", "Lite 9B", "Quick, Core, Vision and Plus", "8K context window",
                 "128K context window", "up to 3 Macs", "future model releases", "no subscription",
                 "30 days, no questions asked", SALE, BUNDLE,
                 "Apple Silicon (M1 or newer) on macOS 15 or later, which is a free update."):
        assert fact in text, f"missing pricing fact: {fact}"
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
    assert raw.count(TERMS_PRICE) == 2, "terms current prices missing"


def check_thanks(raw):
    lines = [s for s in re.findall(r'<p><strong>.*?</p>', raw, re.S) if "once" in s]
    assert len(lines) == 2
    expected = (("Crisp Video", "$29", "$9.99", "31%", "$14.50", "$29"),
                ("Check Engine SEO", "$39", "$19.99", "32%", "$29.50", "$39"))
    for line, (name, regular, sale, discount, november, later) in zip(lines, expected):
        assert name in line
        assert re.findall(r'\$\d+(?:\.\d+)?', line) == [regular, sale, november, later], "cross-sell prices differ"
        assert f"Black Friday sale: {sale} once, {discount} off our November price of {november}, through December 2. Then {later}" in line


def check_home(raw):
    assert "reaches Matthew directly" in raw and "reaches Matt directly" not in raw, "maker name is stale"
    assert "the current $39 regular price and $16.99 sale price" in raw, "instalment comment is stale"
    assert "$39 and $16.99 are under Dodo's $50.01" in raw, "BNPL comment is stale"
    comments = " ".join(re.findall(r'/\*.*?\*/|//[^\n]*', raw, re.S))
    assert not re.search(r'\$49(?![\d.])', comments), "comment still says $49"


def check_buy_prices(raw, sale=True):
    buttons = re.findall(r'<a\b[^>]*href="[^" ]*/buy/outlier[^" ]*"[^>]*>.*?</a>', raw, re.S)
    for button in buttons:
        text = visible(button)
        assert ("$16.99 once" if sale else "$39 once") in text, f"wrong button price: {text}"
        assert ("$39" if sale else "$16.99") not in text, f"two button prices: {text}"
    for box in re.findall(r'<p class="pbox-price">.*?</p>', raw, re.S):
        text = visible(box)
        prices = re.findall(r'\$\d+(?:\.\d+)?', text)
        assert prices and prices[0] == ("$16.99" if sale else "$39"), f"wrong leading price: {text}"
        if sale:
            assert text.count("Then $39") == 1, "price box must say Then $39 once"
    return len(buttons)


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
        self.assertIn('<loc>https://outlier.host/pricing/</loc>', read("sitemap.xml"))
        self.assertIn('<meta name="robots" content="noindex">', read("download/index.html"))
        for slug in typed_url_pages.PAGES:
            self.assertEqual(read(f"{slug}/index.html"), typed_url_pages.build(slug))
        # Exercise --check's exit code on drift without writing to the checkout.
        with tempfile.TemporaryDirectory() as tmp:
            for slug in ("about", "pricing", "download"):
                target = Path(tmp) / slug / "index.html"
                target.parent.mkdir()
                target.write_text(read(f"{slug}/index.html"))
            target = Path(tmp) / "pricing/index.html"
            planted = target.read_text().replace("Outlier pricing</h1>", "Old pricing</h1>")
            self.assertNotEqual(planted, raw)
            target.write_text(planted)
            with patch.object(typed_url_pages, "ROOT", Path(tmp)):
                self.assertEqual(typed_url_pages.main(["--check"]), 1)
            self.assertEqual(target.read_text(), planted)
        print(f"pricing: {len(visible(re.search(r'<article>.*?</article>', raw, re.S)[0]).split())} visible article words")

    def test_2_benchmark_correction_only(self):
        rel = "data/local-ai-benchmarks-mac-2026/index.html"
        raw = read(rel)
        self.control(check_correction, raw, raw.replace('One-time price only: <strong>$39 once</strong>',
                     'One-time price only: <strong>$49 once</strong>'), "benchmark $49 once")
        expected = before(rel).replace('Both removed; <strong>$49 once</strong> is the only Outlier price.',
                                      'Both removed. One-time price only: <strong>$39 once</strong>, $16.99 in the Black Friday sale through December 2.')
        self.assertEqual(raw, product_box.refresh_sale(expected), "benchmark data changed")

    def test_3_terms_prices_only(self):
        raw = read("terms.html")
        self.control(check_terms, raw, raw.replace(TERMS_PRICE, "$49", 1), "terms $49")
        self.assertEqual(raw, before("terms.html").replace("$49", TERMS_PRICE))
        if (ROOT / "terms/index.html").exists():
            check_terms(read("terms/index.html"))

    def test_4_crisp_and_other_receipt_prices(self):
        raw = read("thank-you.html")
        self.control(check_thanks, raw, raw.replace("Then $29", "Then $19", 1), "Crisp Then $19")
        self.control(check_thanks, raw, raw.replace('hidden>$29 once', 'hidden>$19 once', 1), "Crisp regular $19")
        expected = before("thank-you.html").replace("$19 once", "$29 once").replace("Then $19", "Then $29")
        self.assertEqual(raw, product_box.refresh_sale(expected))

    def test_5_home_name_and_comments(self):
        raw = read("index.html")
        self.control(check_home, raw, raw.replace("reaches Matthew directly", "reaches Matt directly"), "Matt directly")
        self.control(check_home, raw, raw.replace("the current $39 regular price", "the current $49 regular price"), "stale price comment")

    def test_6_sale_buttons_boxes_and_post_sale_build(self):
        end = dt.datetime.fromisoformat(product_box.FOUNDING_ENDS.replace("Z", "+00:00"))
        self.assertTrue(product_box.sale_open(end - dt.timedelta(microseconds=1)))
        self.assertFalse(product_box.sale_open(end))
        self.assertFalse(product_box.sale_open(end + dt.timedelta(microseconds=1)))
        seen = pages = 0
        for path in ROOT.rglob("index.html"):
            if ".git" in path.parts or "_seo_build" in path.parts:
                continue
            raw = path.read_text(encoding="utf-8")
            if "data-pbox-script" not in raw:
                continue
            pages += 1
            seen += check_buy_prices(raw)
            with patch.object(product_box, "sale_open", return_value=False):
                check_buy_prices(product_box.refresh_sale(raw), sale=False)
        self.assertGreater(pages, 200)
        self.assertGreater(seen, 300)
        raw = read("download/index.html")
        self.control(check_buy_prices, raw, raw.replace('data-pbox-sale-button>$16.99 once',
                     'data-pbox-sale-button>$39 once'), "sale button $39")
        self.control(check_buy_prices, raw, raw.replace('data-pbox-regular hidden>: $39 once',
                     'data-pbox-regular>: $39 once'), "regular price shown beside sale")
        for on in (True, False):
            with patch.object(product_box, "sale_open", return_value=on):
                check_buy_prices(product_box.box("test", "answer", "1.11.1012"), on)
                check_buy_prices(product_box.end_box("test", "1.11.1012"), on)
        self.assertEqual(product_box._founders_visible(product_box.STD_PRICE_NEW), [])
        self.assertTrue(product_box._founders_visible('<p>Uncontrolled sale: $16.99</p>'))
        print(f"sale prices: {seen} Buy buttons on {pages} pages; post-sale rebuilds also checked")

    def test_7_sitemap_dates_and_control(self):
        _raw, changed, lagging = sitemap_lastmod.sync(ROOT, check=True)
        self.assertEqual((changed, lagging), (0, 0))
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
