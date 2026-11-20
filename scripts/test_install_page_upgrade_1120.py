#!/usr/bin/env python3
"""Install page upgrade, 20 November 2026 (job cx-20261120-2115, Article Studio).

Search Console showed the /how-to/ hub, not the install page, for "run local ai apple silicon mac".
The hub now describes its list; the install page keeps every section and adds a Mac-by-RAM list and
a 16 GB FAQ. Figures come only from the page's own tier table (the app's catalog).
"""
import html, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HUB = (ROOT / "how-to/index.html").read_text()
PAGE = (ROOT / "how-to/install-local-ai-on-mac/index.html").read_text()
fails = []

def check(ok, msg):
    if not ok:
        fails.append(msg)

title = re.search(r"<title>(.*?)</title>", HUB, re.S).group(1)
desc = re.search(r'<meta name="description" content="([^"]*)"', HUB).group(1)
check("install" not in (title + desc).lower() and "run local ai" not in (title + desc).lower(), "hub title or description still competes")
check(len(title) <= 60 and len(desc) <= 155, "hub title or description too long")
main = HUB[HUB.find("<h1"):]
first = re.search(r'<a [^>]*href="([^"]+)"[^>]*>([^<]*)</a>', main)
check(first and first.group(1).endswith("/how-to/install-local-ai-on-mac/") and first.group(2) == "run local AI on an Apple silicon Mac", "hub's first link is not the install page with its anchor")

check("<title>How to run local AI on an Apple silicon Mac (2026) | Outlier</title>" in PAGE, "install title changed")
for h2 in ["What your Mac needs", "Pick a model for your RAM", "Step by step, with times", "Confirm it's actually local", "Adding bigger models", "Other ways to run local AI on a Mac"]:
    check(f"<h2>{h2}</h2>" in PAGE, f"section removed: {h2}")
for row in ["Nano (4B)</td><td>2.37&nbsp;GB</td><td><strong>6&nbsp;GB</strong>", "Lite (9B)</td><td>5.04&nbsp;GB</td><td>12&nbsp;GB", "Quick (26B, 4B active)</td><td>15.61&nbsp;GB</td><td>16&nbsp;GB", "Core (27B)</td><td>15.13&nbsp;GB</td><td>24&nbsp;GB", "Vision 3.8 (27B, reads images)</td><td>15.5&nbsp;GB</td><td>24&nbsp;GB", "Plus (397B)</td><td>209&nbsp;GB</td><td>64&nbsp;GB"]:
    check(row in PAGE, f"tier row changed: {row[:20]}")
check("<strong>Which Mac runs what.</strong>" in PAGE, "Mac-by-RAM list missing")
for gb in ["8 GB:", "16 GB:", "24 GB to 48 GB:", "64 GB or more:"]:
    check(f"<strong>{gb}</strong>" in PAGE, f"Mac list row missing: {gb}")

vis_faq = [html.unescape(q) for q in re.findall(r'<div class="faq-item">\s*<h3>(.*?)</h3>', PAGE, re.S)]
ld = None
for block in re.findall(r'<script type="application/ld\+json">\s*(.*?)\s*</script>', PAGE, re.S):
    d = json.loads(block)
    if d.get("@type") == "FAQPage":
        ld = [q["name"] for q in d["mainEntity"]]
check(ld == vis_faq, "FAQ JSON-LD differs from the visible FAQ")
check("Can a 16 GB Mac run local AI?" in vis_faq and len(vis_faq) == 6, "16 GB FAQ missing or FAQ count wrong")

check('<meta name="last-modified" content="2026-11-20">' in PAGE and "Last updated 2026-11-20" in PAGE and '"dateModified": "2026-11-20"' in PAGE, "install dates not 20 November 2026")
body = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", PAGE, flags=re.S)
check(not re.search("[–—]", body), "em or en dash in the page")
for word in [" best ", "fastest", "#1", "unlike ", "only app"]:
    check(word not in html.unescape(re.sub(r"<[^>]+>", " ", body)).lower(), f"self-ranking word: {word.strip()}")

if fails:
    print("FAIL"); [print(" -", f) for f in fails]; sys.exit(1)
print("ok: install page upgrade (", len(vis_faq), "FAQ )")
