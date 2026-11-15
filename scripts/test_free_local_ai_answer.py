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
EDIT_DATE = "2026-11-15"


def text(raw):
    raw = re.sub(r"<(script|style)\b.*?</\1>", " ", raw, flags=re.S)
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", raw)).split())


def block(pattern, raw):
    match = re.search(pattern, raw, re.S)
    if not match:
        raise AssertionError("Missing HTML block: " + pattern)
    return match.group(1) if match.lastindex else match.group(0)


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
        for phrase in ("Outlier", "free", "Apple silicon", "M1 or newer",
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
        protected = (
            (r'<div class="pbox" data-pbox="answer">.*?</div>',
             "cca7d51a5c5dcea44a283bfe6b9ba7fad3fc14009235f0bab66444e669bab5ad"),
            (r'<div class="cta">.*?</div>',
             "d2af8dd7f670d22907f1a483d68afebea5c212f189245b8bada7ed0ecea8355e"),
            (r'<table>.*?</table>',
             "1bce2402443048ee16297fe384f4a3996b7874ef6fb4238d1c5c87f118468f84"),
            (r'<p>Prices and licences read .*?</p>',
             "3d1595c94047444288a7cb00814b45a25eb0ed8551eaba0e4aed7cd74fc0053b"),
            (r'<span class="byline" data-claims-checked=.*?</span>',
             "afbd5d4ee623b395535087c62aedbd2abaca5eac0e85eec6c655acdbb9eae28c"),
            (r'<section class="subscribe-strip">.*',
             "48200e82daa4d6625a98540dde0cb45bac15d8c081ad9a52d68aeaf5ce10461c"),
            (r'<div class="quick-answer">.*?(<ul>.*?</ul>)',
             "6033bb44012b584e4110db89014a97d666a5f866e5816e40104d17a79abbd2e0"),
        )
        for pattern, expected in protected:
            with self.subTest(block=pattern):
                self.assertEqual(hashlib.sha256(block(pattern, self.raw).encode()).hexdigest(),
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
