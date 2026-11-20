#!/usr/bin/env python3
"""Offline content checks. Never run the app, load a model or change networking.

Use --page /tmp/base.html to run a control against saved old text.
Protected hashes are from c03fa1f98, before this job's edits.
"""
import argparse
import hashlib
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import unittest
from urllib.parse import unquote, urljoin, urlsplit
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "how-to/keep-prompts-private-on-mac/index.html"
CANONICAL = "https://outlier.host/how-to/keep-prompts-private-on-mac/"
EDIT_DATE = "2026-11-15"


class Visible(HTMLParser):
    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input",
            "link", "meta", "param", "source", "track", "wbr"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag not in self.VOID:
            a = dict(attrs)
            style = re.sub(r"\s+", "", a.get("style", "").lower())
            hidden = ("hidden" in a or a.get("aria-hidden") == "true"
                      or "display:none" in style or "visibility:hidden" in style
                      or tag in {"head", "script", "style", "template", "noscript"})
            self.stack.append((tag, hidden))

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break

    def handle_data(self, data):
        if not any(hidden for _, hidden in self.stack):
            self.parts.append(data)


def text(raw):
    parser = Visible()
    parser.feed(raw)
    parser.close()
    return " ".join(" ".join(parser.parts).split())


def block(pattern, raw):
    match = re.search(pattern, raw, re.S)
    if not match:
        raise AssertionError("Missing HTML block: " + pattern)
    return match.group(1) if match.lastindex else match.group(0)


class PrivateOfflineGuide(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = PAGE.read_text(encoding="utf-8")
        cls.body = block(r"<body>.*?</body>", cls.raw)
        cls.prose = text(cls.body)
        cls.schemas = [json.loads(s) for s in re.findall(
            r'<script type="application/ld\+json">(.*?)</script>', cls.raw, re.S)]

    def test_early_direct_answer(self):
        quick = block(r'<div class="qa">.*?</div>', self.body)
        answer = text(quick)
        for phrase in ("Outlier", "private AI chat on a Mac", "local model",
                       "web search off", "prompts, chat history or files",
                       "model files live on your disk", "computed on Apple silicon",
                       "Download the app and a model while connected first",
                       "local chat works with Wi-Fi off",
                       "Other app features can still make connections"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, answer)
        self.assertLess(len(text(self.body.split(quick)[0]).split()), 70)
        self.assertLess(self.body.index(quick), self.body.index('data-pbox="answer"'))
        self.assertNotIn("The whole sequence below stays on the Mac", self.prose)

    def test_setup_distinguishes_downloads_from_local_chat(self):
        steps = block(r'<h2>Set up a private local chat</h2>\s*<ol>(.*?)</ol>', self.body)
        self.assertEqual(len(re.findall(r"<li>", steps)), 4)
        for phrase in ("Install while connected", "Applications", "Download & start",
                       "download finish before going offline", "model already on disk",
                       "Settings > Models", "green check", "Switch to that tier in chat",
                       "web search switch off", "local model", "1.11.1004",
                       "Settings > Advanced > Update automatically", "Earlier versions",
                       "Wi-Fi off", "ask a new question", "Ethernet",
                       "These are steps for you to try"):
            self.assertIn(phrase, text(steps))
        install = text((ROOT / "how-to/install-local-ai-on-mac/index.html").read_text())
        models = text((ROOT / "how-to/download-a-model-tier/index.html").read_text())
        self.assertIn("Download & start", install)
        self.assertIn("Settings > Models", models)
        self.assertIn("green check", models)

    def test_documented_connection_exceptions(self):
        exceptions = text(block(r'<h2>What still needs a connection\?</h2>(.*?)'
                                r'<h2>Check where requests go</h2>', self.body))
        for phrase in ("Hugging Face", "IP address", "repository",
                       "no prompts, chats or model output", "own API key",
                       "prompts and conversation history", "search query",
                       "GitHub", "unless you turn it off", "upgrade window",
                       "no licence key, device ID or text you typed",
                       "Activate a Pro key while connected", "device name",
                       "at startup and once a day", "Pro keeps working",
                       "MCP server", "Google Custom Search", "Gist import",
                       "asks you first, every time", "Approving it",
                       "desktop app has no analytics SDK or inference telemetry"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, exceptions)
        privacy = text((ROOT / "privacy.html").read_text())
        for phrase in ("HuggingFace sees your IP", "conversation history",
                       "at startup and once a day", "Pro keeps working",
                       "MCP server", "asks you first, every time"):
            self.assertIn(phrase, privacy)
        self.assertNotIn("Cloudflare’s own page analytics", self.prose)

    def test_visible_faq_matches_schema_questions_and_answers(self):
        visible = [(text(q), text(a)) for q, a in re.findall(
            r'<div class="faq-item">\s*<h3>(.*?)</h3>\s*<p>(.*?)</p>\s*</div>',
            self.body, re.S)]
        faqs = [s for s in self.schemas if s.get("@type") == "FAQPage"]
        self.assertEqual(len(faqs), 1)
        schema = [(q["name"], q["acceptedAnswer"]["text"])
                  for q in faqs[0]["mainEntity"]]
        self.assertEqual(len(visible), 3)
        self.assertEqual(visible, schema)
        for question, answer in schema:
            self.assertIn(question, self.prose)
            self.assertIn(answer, self.prose)

    def test_canonical_and_only_page_dates(self):
        self.assertEqual(re.findall(r'<link rel="canonical" href="([^"]+)">', self.raw),
                         [CANONICAL])
        self.assertIn("Last updated " + EDIT_DATE, self.prose)
        article = next(s for s in self.schemas if s.get("@type") == "Article")
        self.assertEqual(article["dateModified"], EDIT_DATE)
        self.assertEqual(article["datePublished"], "2026-06-17")
        ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        entries = [u for u in ET.parse(ROOT / "sitemap.xml").getroot()
                   if u.findtext("s:loc", namespaces=ns) == CANONICAL]
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].findtext("s:lastmod", namespaces=ns), EDIT_DATE)

    def test_local_links_resolve_and_useful_guides_are_linked(self):
        links = [html.unescape(h) for h in re.findall(r'href=["\']([^"\']+)["\']', self.raw)]
        for path in ("/how-to/install-local-ai-on-mac/", "/how-to/download-a-model-tier/",
                     "/how-to/use-ai-offline-mac/", "/learn/can-ai-run-without-internet/",
                     "/privacy.html"):
            self.assertIn(path, links)
        for href in links:
            url = urlsplit(urljoin(CANONICAL, href))
            if url.hostname != "outlier.host":
                continue
            if url.path in {"/dl/outlier", "/buy/outlier"}:
                continue
            target = ROOT / unquote(url.path).lstrip("/")
            if target.is_dir():
                target /= "index.html"
            self.assertTrue(target.is_file(), href)
            if url.fragment and target.suffix == ".html":
                self.assertIn('id="' + unquote(url.fragment) + '"', target.read_text())
        external = [h for h in links if urlsplit(h).hostname not in (None, "outlier.host")]
        self.assertEqual(external, ["https://kerrandcompanyholdings.com/"])

    def test_legal_price_product_blocks_and_evidence_unchanged(self):
        protected = (
            # re-pinned 2026-11-20: Matthew's exact sale line (2fa7aa899) and no former price (f5a7902b2) changed this box
            (r'<div class="pbox" data-pbox="answer">.*?</div>',
             "5e4b019083633d31195d4280d75f8d93335194c021460314391abd2ace79b3e0"),
            # re-pinned 2026-11-20 with the sale-wording and no-former-price changes (2fa7aa899, f5a7902b2)
            (r'<div class="pbox" data-pbox="end">.*?</div>',
             "ccee6c35f715af115dea091254d870a8182eba9e15c2a6b6784bd85510fc18f1"),
            # re-pinned 2026-11-20 with the sale-wording and no-former-price changes (2fa7aa899, f5a7902b2)
            (r'<a class="cta".*',
             "146ab503b5c313b1637c175739f5ac9a5eb5aedcedfd72f5920be801cd21fc58"),
            (r'<p>The chat path calls only .*?</p>',
             "0a5dc7e6a4df08f0c90e44428481c732df32e4854617878124bd4fc908bb2b39"),
        )
        for pattern, expected in protected:
            with self.subTest(block=pattern):
                self.assertEqual(hashlib.sha256(block(pattern, self.raw).encode()).hexdigest(),
                                 expected)

    def test_useful_body_word_floor_and_download_next_step(self):
        useful = self.body.split('<a class="cta"')[0]
        useful = re.sub(r'<div class="pbox"[^>]*>.*?</div>|<nav.*?</nav>',
                        " ", useful, flags=re.S)
        self.assertGreaterEqual(len(text(useful).split()), 300)
        cta = block(r'<a class="cta".*?</a>', self.body)
        self.assertIn("Download Outlier for Mac", text(cta))
        self.assertIn("https://outlier.host/dl/outlier?src=", cta)
        self.assertIn('data-plausible="Download"', cta)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--page", type=Path, default=PAGE)
    args, remaining = parser.parse_known_args()
    PAGE = args.page
    unittest.main(argv=[__file__] + remaining)
