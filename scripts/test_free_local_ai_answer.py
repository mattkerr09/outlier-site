#!/usr/bin/env python3
"""Offline checks for the free local AI answer. No app or model is run.

Use --page /tmp/base.html to check the saved base page with these same tests.
Protected-block hashes come from base commit 8cc083026, before this job's edits.
"""
import argparse
import hashlib
import html
import json
from pathlib import Path
import re
import unittest
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "best/free-local-ai-mac/index.html"
CANONICAL = "https://outlier.host/best/free-local-ai-mac/"
EDIT_DATE = "2026-11-20"   # re-pinned 2026-11-20: the CEO-ordered /best/ unranking (8560cbe7d, 118acb694) re-dated the page


def text(raw):
    raw = re.sub(r"<(script|style)\b.*?</\1>", " ", raw, flags=re.S)
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", raw)).split())


def block(pattern, raw):
    match = re.search(pattern, raw, re.S)
    if not match:
        raise AssertionError("Missing HTML block: " + pattern)
    return match.group(1) if match.lastindex else match.group(0)


# A release moves every Download link to the new DMG (ship_chain's site bump). The protected blocks are compared with
# only the version inside a release-asset URL replaced, so a release does not need a re-pin and any other edit still fails.
RELEASE_ASSET = re.compile(r"(releases/download/v)\d+(?:\.\d+)+(/Outlier-)\d+(?:\.\d+)+(-arm64\.dmg)")


def release_neutral(raw):
    return RELEASE_ASSET.sub(r"\1VERSION\2VERSION\3", raw)


class FreeLocalAIAnswer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = PAGE.read_text(encoding="utf-8")
        cls.article = block(r"<article>.*?</article>", cls.raw)
        cls.prose = text(cls.article)
        cls.schemas = [json.loads(s) for s in re.findall(
            r'<script type="application/ld\+json">(.*?)</script>', cls.raw, re.S)]

    def test_early_answer(self):
        quick = block(r'<div class="quick-answer">.*?</div>', self.article)
        answer = text(block(r"<p>.*?</p>", quick))
        for phrase in ("Outlier", "free", "Apple silicon",   # "M1 or newer" left with the 11-20 /best/ rewrite; Apple silicon says the same
                       
                       "macOS 15 or later", "Nano 4B", "Lite 9B", "chat",
                       "writing", "summaries", "no account or API key", "8 GB Mac",
                       "Lite needs at least 12 GB",
                       "Download the app and a model", "internet", "offline"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, answer)
        self.assertLess(len(text(self.article.split(quick)[0]).split()), 70)
        self.assertLess(self.article.index(quick), self.article.index('data-pbox="answer"'))
        self.assertNotIn("zero setup", self.prose.lower())
        self.assertNotIn("zero-setup", self.prose.lower())

    def test_models_and_requirements_match_repo(self):
        home = (ROOT / "index.html").read_text(encoding="utf-8")
        for tier, model, size, minimum in (
                ("Nano", "Qwen3.5-4B", "2.37 GB", "6 GB"),
                ("Lite", "Qwen3.5-9B", "5.04 GB", "12 GB")):
            row = text(block(r'<tr>\s*<td><div class="tname">Outlier ' + tier
                             + r'</div>.*?</tr>', home))
            for fact in (model, size, minimum):
                with self.subTest(tier=tier, fact=fact):
                    self.assertIn(fact, row)
                    self.assertIn(fact, self.prose)
        for phrase in ("8 GB Mac", "16 GB", "Intel Macs are not supported"):
            self.assertIn(phrase, self.prose)
        for tier in ("Quick", "Core", "Vision 3.8", "Plus"):
            self.assertIn(tier, self.prose)

    def test_setup_and_offline_use(self):
        steps = block(r'<h2>Start a free local chat in Outlier</h2>.*?<ol>(.*?)</ol>',
                      self.article)
        self.assertEqual(len(re.findall(r"<li>", steps)), 4)
        for phrase in ("Applications", "Download & start", "Type a question",
                       "Wi-Fi off", "new question"):
            self.assertIn(phrase, text(steps))
        for phrase in ("Settings > Models", "green check", "files must already be on your Mac",
                       "cloud-only file", "Web search", "internet connection"):
            self.assertIn(phrase, self.prose)
        install = text((ROOT / "how-to/install-local-ai-on-mac/index.html").read_text())
        models = text((ROOT / "how-to/download-a-model-tier/index.html").read_text())
        self.assertIn("Download & start", install)
        self.assertIn("Settings > Models", models)
        self.assertIn("green check", models)

    def test_faq_schema_matches_visible_questions_and_answers(self):
        visible = [(text(q), text(a)) for q, a in re.findall(
            r'<div class="faq-item">\s*<h3>(.*?)</h3>\s*<p>(.*?)</p>\s*</div>',
            self.article, re.S)]
        faqs = [s for s in self.schemas if s.get("@type") == "FAQPage"]
        self.assertEqual(len(faqs), 1)
        schema = [(q["name"], q["acceptedAnswer"]["text"])
                  for q in faqs[0]["mainEntity"]]
        self.assertEqual(visible, schema)
        self.assertEqual(len(visible), 4)
        self.assertIn("Can I use free local AI with Wi-Fi off?", dict(visible))

    def test_canonical_dates_and_links(self):
        self.assertEqual(re.findall(r'<link rel="canonical" href="([^"]+)">', self.raw),
                         [CANONICAL])
        self.assertIn('name="last-modified" content="' + EDIT_DATE + '"', self.raw)
        self.assertIn("Last updated " + EDIT_DATE, self.prose)
        article = next(s for s in self.schemas if s.get("@type") == "Article")
        self.assertEqual(article["dateModified"], EDIT_DATE)
        self.assertEqual(article["datePublished"], "2026-06-09")
        ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        entries = [u for u in ET.parse(ROOT / "sitemap.xml").getroot()
                   if u.findtext("s:loc", namespaces=ns) == CANONICAL]
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].findtext("s:lastmod", namespaces=ns), EDIT_DATE)
        links = re.findall(r'href="([^"]+)"', self.article)
        for path in ("download/", "pricing/", "how-to/install-local-ai-on-mac/",
                     "how-to/download-a-model-tier/", "how-to/use-ai-offline-mac/"):
            self.assertIn("https://outlier.host/" + path, links)
            self.assertTrue((ROOT / path / "index.html").is_file())

    def test_protected_blocks_unchanged(self):
        # 2026-11-20 re-pin: every block below was reviewed after that day's sale wording (2fa7aa899), no former price
        # (f5a7902b2), the /best/ unranking and live re-read (8560cbe7d, 118acb694) and the restored early-answer requirements.
        protected = (
            # re-pinned 2026-11-20: Matthew's exact sale line (2fa7aa899) and no former price (f5a7902b2) changed this box
            (r'<div class="pbox" data-pbox="answer">.*?</div>',
             "ade7f948ace65d223b964cb0665a6b110826adba4fecfaf8c330ac1c2b603b55"),
            # re-pinned 2026-11-20 with the sale-wording and no-former-price changes (2fa7aa899, f5a7902b2)
            (r'<div class="cta">.*?</div>',
             "91502cf6791b7129351f19e72251b32a1aed9dc0773ae355da647b708bb4b5dc"),
            # re-pinned 2026-11-20: the rival rows were corrected from that day's live re-read (118acb694)
            (r'<table>.*?</table>',
             "195f4ec45ac69133221665f2b7e6b78bdea178eb36085a0fc484ade32fd7cd4d"),
            (r'<p>Prices and licences read .*?</p>',
             "f46d6cb5029d821c990fa8fe397b8530e4a3b3978b0c4d731e1435cab2ca5ff8"),
            (r'<span class="byline" data-claims-checked=.*?</span>',
             "74684029fe7e466a3d3bd19368365f52e374a3f60f4d2f77c8ff59771f573436"),
            (r'<section class="subscribe-strip">.*',
             "839ca422db5df9b97e694c7bbf7362562bbaa1ca950498d16639a4adb769bca2"),  # 23 Nov: only change, mac-only.js?v=20261121 -> v=20261123 (phone outline button; proven by reverting the string)
            (r'<div class="quick-answer">.*?(<ul>.*?</ul>)',
             "9fdb588f4057eb516ab7f8e9093a957a184fc13a7106f95b8a4edaffec4cc0bb"),
        )
        for pattern, expected in protected:
            with self.subTest(block=pattern):
                self.assertEqual(hashlib.sha256(release_neutral(block(pattern, self.raw)).encode()).hexdigest(),
                                 expected)

    def test_article_word_floor_and_no_new_external_links(self):
        useful = re.sub(r'<div class="(?:byline-row|pbox|cta|related)"[^>]*>.*?</div>',
                        " ", self.article, flags=re.S)
        self.assertGreaterEqual(len(text(useful).split()), 300)
        external = [html.unescape(h) for h in re.findall(r'href="([^"]+)"', self.raw)
                    if urlsplit(html.unescape(h)).hostname not in (None, "outlier.host")]
        self.assertCountEqual(external, [
            "https://ollama.com/pricing", "https://github.com/ollama/ollama",
            "https://jan.ai/", "https://github.com/janhq/jan/blob/main/LICENSE",
            "https://lmstudio.ai/pricing", "https://lmstudio.ai/app-terms",
            "https://kerrandcompanyholdings.com/",
        ])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--page", type=Path, default=PAGE)
    args, remaining = parser.parse_known_args()
    PAGE = args.page
    unittest.main(argv=[__file__] + remaining)
