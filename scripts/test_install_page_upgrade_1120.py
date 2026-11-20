#!/usr/bin/env python3
"""Offline checks for cx-20261120-2115-outliersite-install-page-upgrade.

Figures transcribed from Article Studio's FACTS.md, 20 November 2026.
Protected hashes are from feaae4c720f6db304b42963214aebb04078eb987.
No app, model, network access or third-party Python package is needed.
"""
import hashlib
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parent.parent
INSTALL = ROOT / "how-to/install-local-ai-on-mac/index.html"
HUB = ROOT / "how-to/index.html"
DATASET = "https://outlier.host/data/local-ai-benchmarks-mac-2026/"
TIERS = {
    "Outlier Nano": ("2.37 GB", "6 GB", "Nano 4B"),
    "Outlier Lite": ("5.04 GB", "12 GB", "Lite 9B"),
    "Outlier Quick": ("15.61 GB", "16 GB", None),
    "Outlier Core": ("15.13 GB", "24 GB", "Core 27B"),
    "Outlier Vision 3.8": ("15.5 GB", "24 GB", None),
    "Outlier Plus": ("209 GB", "64 GB", "Plus 397B"),
}


def block(pattern, raw):
    match = re.search(pattern, raw, re.S)
    if match is None:
        raise AssertionError("Missing HTML block: " + pattern)
    return match.group(0)


def text(raw):
    raw = re.sub(r"<(script|style|noscript)\b.*?</\1>", " ", raw, flags=re.S | re.I)
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", raw)).split())


class Elements(HTMLParser):
    """Read attributes without depending on their order or quote style."""
    def __init__(self, raw):
        super().__init__(convert_charrefs=True)
        self.tags = []
        self.feed(raw)

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))


def meta(raw, key):
    return next(a["content"] for t, a in Elements(raw).tags
                if t == "meta" and key in (a.get("name"), a.get("property")))


def faq(raw):
    return [(text(q), text(a)) for q, a in re.findall(
        r'<div class="faq-item">\s*<h3>(.*?)</h3>\s*<p>(.*?)</p>\s*</div>', raw, re.S)]


def shingles(raw):
    """Use near_dup_gate's chrome and five-word comparison rules on every page."""
    body = block(r"<body\b.*?</body>", raw) if "<body" in raw else raw
    body = re.sub(r"<(script|style|nav|header|footer|noscript)\b.*?</\1>", " ", body,
                  flags=re.S | re.I)
    body = re.sub(r'<div class="(?:related|byline-row)".*?</div>', " ", body, flags=re.S)
    body = re.sub(r"&[a-z#0-9]+;", " ", re.sub(r"<[^>]+>", " ", body))
    words = re.findall(r"[a-z0-9$.%]+", body.lower())
    return {" ".join(words[i:i + 5]) for i in range(len(words) - 4)}


class InstallPageUpgrade(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = INSTALL.read_text(encoding="utf-8")
        cls.hub = HUB.read_text(encoding="utf-8")
        cls.article = block(r"<article>.*?</article>", cls.raw)
        cls.schemas = [json.loads(s) for s in re.findall(
            r'<script type="application/ld\+json">(.*?)</script>', cls.raw, re.S)]
        cls.dataset = json.loads((ROOT / "data/local-ai-benchmarks-mac-2026/dataset.json").read_text())

    def test_hub_describes_a_list_and_starts_with_install_link(self):
        title = text(block(r"<title>.*?</title>", self.hub))
        description = meta(self.hub, "description")
        self.assertLessEqual(len(title), 60)
        self.assertLess(len(description), 155)
        for value in (title, description):
            self.assertNotRegex(value.lower(), r"install|run local ai")
        for key in ("og:title", "twitter:title"):
            self.assertEqual(meta(self.hub, key), title)
        for key in ("og:description", "twitter:description"):
            self.assertEqual(meta(self.hub, key), description)
        body = block(r"<body>.*?</body>", self.hub)
        self.assertEqual(hashlib.sha256(body.encode()).hexdigest(),
                         "7d97529568da957140493a06828635610f9f35d84ce9a509cd216ce6280c5eb7")
        main = body.split("</nav>", 1)[1].split("<footer>", 1)[0]
        first = block(r"<a\b.*?</a>", main)
        self.assertEqual(Elements(first).tags[0][1]["href"],
                         "https://outlier.host/how-to/install-local-ai-on-mac/")
        self.assertEqual(text(first), "run local AI on an Apple silicon Mac")

    def test_identity_quick_answer_and_price_blocks_are_preserved(self):
        self.assertEqual(text(block(r"<title>.*?</title>", self.raw)),
                         "How to run local AI on an Apple silicon Mac (2026) | Outlier")
        self.assertEqual(text(block(r"<h1>.*?</h1>", self.raw)),
                         "How to run local AI on an Apple silicon Mac")
        self.assertIn("Matthew Kerr · Outlier · published 2026-06-09", text(self.article))
        for pattern, digest in (
            (r'<div class="quick-answer">.*?</div>',
             "3ae138095d91db075265e52f23852ef0d7cc240bdeb007373f79f939ae35b5ac"),
            (r'<div class="pbox" data-pbox="answer">.*?</div>',
             "f39822fd87b968cf7adc658812939c5eac52cac4cf8c4ed933bad25eec816e4b"),
            (r'<div class="cta">.*?</div>',
             "ee03f2eb06675620364ea23517d78119a76fdbcba750f5315c9c8704fc09bafd"),
        ):
            with self.subTest(block=pattern):
                self.assertEqual(hashlib.sha256(block(pattern, self.raw).encode()).hexdigest(), digest)
        lead = text(block(r'<p class="lead">.*?</p>', self.article))
        for phrase in ("private", "offline when you want it", "one price", "no rate limits"):
            self.assertIn(phrase, lead)
        self.assertLess(self.article.index('class="lead"'), self.article.index('class="quick-answer"'))

    def test_ram_table_matches_facts_and_measured_dataset(self):
        table = block(r'<table id="model-ram">.*?</table>', self.article)
        self.assertIn("Measured speed on M1 Ultra", text(table))
        rows = re.findall(r"<tr>(.*?)</tr>", block(r"<tbody>.*?</tbody>", table), re.S)
        self.assertEqual(len(rows), len(TIERS))
        seen = []
        speeds = self.dataset["tokens_per_sec_m1_ultra_v9_paged"]
        self.assertEqual(self.dataset["dateModified"], "2026-11-09")
        for row in rows:
            cells = [text(c) for c in re.findall(r"<t[dh]\b[^>]*>(.*?)</t[dh]>", row, re.S)]
            self.assertEqual(len(cells), 4)
            name, download, minimum, speed = cells
            seen.append(name)
            size, ram, measured = TIERS[name]
            self.assertEqual((download, minimum), (size, ram))
            self.assertEqual(speed, f"{speeds[measured]:.1f} tokens per second" if measured
                             else "Not measured in this dataset")
        self.assertEqual(seen, list(TIERS))
        self.assertIn(f'href="{DATASET}"', self.article)
        self.assertIn("measured 9 November 2026 dataset", text(self.article))
        self.assertIn("Plus was measured on 24 June 2026", text(self.article))
        # Reject extra decode claims as well as incorrect figures in the main table.
        actual = re.findall(r"(\d+(?:\.\d+)?)\s*(?:tokens per second|tok/s)", text(self.article))
        self.assertCountEqual(actual, ["71.7", "53.4", "20.7", "2.0"])
        for cell in re.findall(r"<t[dh]\b[^>]*>(.*?)</t[dh]>", self.article, re.S):
            value = text(cell)
            if re.search(r"\d", value) and re.search(r"M[2-9]|M1 (?:Pro|Max)|MacBook|Mac mini|Air", value):
                self.assertIn("estimated", value.lower())

    def test_memory_explanation_and_mac_mapping_come_before_steps(self):
        headings = ("How much RAM each model needs", "Why memory decides the model",
                    "Which Mac runs what", "Step by step, with times")
        positions = [self.article.index(f"<h2>{h}</h2>") for h in headings]
        self.assertEqual(positions, sorted(positions))
        self.assertLess(self.article.index('class="quick-answer"'), positions[0])
        memory = text(block(r"<h2>Why memory decides the model</h2>\s*<p>.*?</p>", self.article))
        self.assertIn("unified memory", memory)
        self.assertIn("macOS", memory)
        self.assertIn("8 GB Mac", memory)
        sentences = re.split(r"[.!?]\s+", memory)
        self.assertGreaterEqual(len(sentences), 3)
        self.assertLessEqual(len(sentences), 5)
        mapping = block(r'<ul id="mac-ram-tiers">.*?</ul>', self.article)
        rows = [text(r) for r in re.findall(r"<li>(.*?)</li>", mapping, re.S)]
        self.assertEqual(len(rows), 4)
        for row, ram in zip(rows[:3], (8, 16, 24)):
            self.assertTrue(row.startswith(f"{ram} GB Mac:"))
            expected = [tier for tier, (_, minimum, _) in TIERS.items()
                        if int(minimum.split()[0]) <= ram]
            self.assertEqual([tier for tier in TIERS if tier in row], expected)
        self.assertTrue(rows[3].startswith("32 to 64 GB Macs:"))
        for tier in TIERS:
            self.assertIn(tier, rows[3])
        self.assertIn("Outlier Plus joins the list at 64 GB", rows[3])

    def test_faq_matches_schema_and_questions_are_unique_sitewide(self):
        visible = faq(self.article)
        schemas = [s for s in self.schemas if s.get("@type") == "FAQPage"]
        self.assertEqual(len(schemas), 1)
        self.assertGreaterEqual(len(visible), 4)
        self.assertLessEqual(len(visible), 6)
        self.assertEqual(visible, [(q["name"], q["acceptedAnswer"]["text"])
                                   for q in schemas[0]["mainEntity"]])
        questions = {q.lower() for q, _ in visible}
        self.assertEqual(len(questions), len(visible))
        for page in ROOT.rglob("*.html"):
            if page == INSTALL or any(p in page.parts for p in (".git", "node_modules", "_seo_build")):
                continue
            raw = page.read_text(encoding="utf-8")
            for question in questions:
                self.assertNotIn(question, text(raw).lower(), str(page.relative_to(ROOT)))

    def test_dates_copy_and_prices(self):
        # Keep the site's date format and placement readable by its dateline gate.
        self.assertIn("Last updated 2026-11-20 Quick answer", text(self.article))
        self.assertEqual(meta(self.raw, "last-modified"), "2026-11-20")
        self.assertEqual([a["href"] for t, a in Elements(self.raw).tags
                          if t == "link" and a.get("rel") == "canonical"],
                         ["https://outlier.host/how-to/install-local-ai-on-mac/"])
        article = next(s for s in self.schemas if s.get("@type") == "Article")
        self.assertEqual(article["dateModified"], "2026-11-20")
        self.assertEqual(article["datePublished"], "2026-06-09")
        ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        for url in ("how-to/", "how-to/install-local-ai-on-mac/"):
            entries = [u for u in ET.parse(ROOT / "sitemap.xml").getroot()
                       if u.findtext("s:loc", namespaces=ns) == "https://outlier.host/" + url]
            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0].findtext("s:lastmod", namespaces=ns), "2026-11-20")
        prose = text(block(r"<body>.*?</body>", self.raw))
        self.assertNotRegex(prose.lower(), r"\b(?:best|top|fastest|only|unlike)\b|#1|[\u2013\u2014]")
        self.assertNotRegex(prose.lower(), r"server\.py|tier_catalog|release check|quality desk|routing order")
        self.assertNotRegex(text(self.raw), r"LM Studio|Ollama|Msty")
        outside = re.sub(r'<div class="pbox"[^>]*>.*?</div>', " ", self.raw, flags=re.S)
        outside = re.sub(r'<span data-pbox-(?:regular|founding)[^>]*>.*?</span>', " ", outside, flags=re.S)
        self.assertNotRegex(text(outside), r"[$£€]\s*\d|\d+(?:\.\d+)?\s*(?:USD|dollars)")

    def test_install_jaccard_is_below_half_against_every_page(self):
        source = shingles(self.raw)
        compared = []
        for page in ROOT.rglob("*.html"):
            if page == INSTALL or any(p in page.parts for p in (".git", "node_modules", "_seo_build")):
                continue
            other = shingles(page.read_text(encoding="utf-8"))
            if other:
                score = len(source & other) / len(source | other)
                compared.append((score, str(page.relative_to(ROOT))))
        self.assertGreaterEqual(len(compared), 50)
        score, page = max(compared)
        print(f"Install max Jaccard: {score:.6f} with {page}")
        self.assertLess(score, 0.5, page)


if __name__ == "__main__":
    unittest.main()
