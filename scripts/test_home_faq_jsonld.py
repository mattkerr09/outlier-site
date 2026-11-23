"""RULES 77 fix 2 (2026-11-23): the home page's FAQPage JSON-LD is the visible FAQ, one Question per <details>, and an edit to
either side that is not regenerated fails here (run scripts/home_faq_jsonld.py write)."""
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
HOME = ROOT / "index.html"


def test_the_faqpage_matches_the_visible_faq():
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "home_faq_jsonld.py"), "check", str(HOME)],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


def test_every_visible_faq_item_is_a_question_and_no_price_is_frozen_in():
    html = HOME.read_text(encoding="utf-8")
    faq = html[html.index('<section class="alt" id="faq">'):]
    visible = faq[:faq.index("</section>")].count("<details")
    blocks = [json.loads(b) for b in re.findall(r'<script type="application/ld\+json">\s*(.*?)\s*</script>', html, re.S)]
    page = [b for b in blocks if b.get("@type") == "FAQPage"]
    assert len(page) == 1 and len(page[0]["mainEntity"]) == visible == 9
    text = json.dumps(page[0])
    assert "$16.99" not in text and "$39" not in text      # prices live in the dated Offers, not in a frozen answer


def test_the_page_names_its_site_page_and_maker():
    html = HOME.read_text(encoding="utf-8")
    types = {json.loads(b).get("@type") for b in re.findall(r'<script type="application/ld\+json">\s*(.*?)\s*</script>', html, re.S)}
    assert {"WebSite", "WebPage", "Person", "FAQPage", "SoftwareApplication", "Organization"} <= types
    assert "I&rsquo;m Matthew Kerr, and I build Outlier in Grand Rapids." in html     # the Person is named on the page too
