#!/usr/bin/env python3
"""Build indexable /pricing/ and the noindex typed-URL /download/ page.

    python3 scripts/typed_url_pages.py [--check]

The site chrome comes from /about/ and the shared product box supplies prices,
requirements and the dated sale switch. --check writes nothing and fails on drift.
"""
from __future__ import annotations

import html
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import product_box  # noqa: E402

PAGES = {
    "pricing": {"title": "Outlier pricing", "crumb": "pricing", "src": "pricing-page",
                "description": "Compare Outlier Free and Pro for Mac. Nano and Lite are free. Pay once for Pro, with no subscription and a 30-day refund."},
    "download": {"title": "Download Outlier", "crumb": "download", "src": "download-page",
                 "description": f"Download Outlier for Mac: free to start, signed and notarized, for Apple silicon on {product_box.OS_REQ}."},
}


FAQ = (
    ("Is it a subscription?", "No. Pro is one payment for the Outlier Lifetime Licence. There is no subscription or renewal. Local generation is never metered or charged per token."),
    ("What happens after December 2?", "The Black Friday sale ends. From December 3, Outlier is $39 once and the bundle is $79 once. Nano and Lite stay free."),
    ("Is there a free version?", "Yes. Free includes Nano and Lite, local chat and sessions, the model picker and downloads, and an 8K context window per conversation. No account is needed."),
)


def pricing_content() -> str:
    return """    <p class="updated-pill">Last updated 2026-11-20</p>
    <p class="lead">Start with Free for everyday chat on your Mac. Choose Pro for the other four model tiers and every feature. Both plans run local AI on your own Mac. There is no monthly plan and no token bill.</p>
    <h2>Free: Nano and Lite</h2>
    <p>Free costs $0 and stays free. It is for everyday private chat, with no account needed. It includes:</p>
    <ul>
      <li>Nano 4B and Lite 9B.</li>
      <li>Local chat and saved sessions.</li>
      <li>The model picker and model downloads.</li>
      <li>An 8K context window per conversation.</li>
    </ul>
    <p>Nano needs 6 GB of memory and Lite needs 12 GB. Both fit a 16 GB MacBook Air. Start here to see how local chat works before you pay.</p>
    <h2>Pro: the Outlier Lifetime Licence</h2>
    <p>Pro adds Quick, Core, Vision and Plus to Nano and Lite. You get all six tiers and every feature, including the coding agent, local memory, projects, a 128K context window and on-device fine-tuning. Quick needs 16 GB to load and wants 24 GB. Core and Vision need 24 GB.</p>
    <p>The licence activates on up to 3 Macs at a time. Pay once to keep everything Pro has, including future model releases, for as long as Outlier exists. There is no subscription, no renewal and no per-token charge for local generation.</p>
"""


def pricing_faq() -> str:
    return ("    <h2>Mac requirements and refunds</h2>\n"
            "    <p>Apple Silicon (M1 or newer) on macOS 15 or later, which is a free update. Intel Macs are not supported.</p>\n"
            "    <p>Refund window: 30 days, no questions asked. To get a refund, email "
            '<a href="mailto:matt@outlier.host?subject=Refund%20request">matt@outlier.host</a>. '
            'Read the <a href="/terms.html">terms</a> for the licence details.</p>\n'
            "    <h2>Pricing FAQ</h2>\n" + "".join(
                "    <h3>" + html.escape(q) + "</h3>\n    <p>" + html.escape(a) + "</p>\n"
                for q, a in FAQ))


def _shell() -> tuple[str, str, str, str]:
    """(head, nav, footer, tail) from /about/, so the pages carry the site's own chrome."""
    s = (ROOT / "about" / "index.html").read_text(encoding="utf-8")
    head = s[s.index("<head>") + len("<head>"):s.index("</head>")]
    nav = s[s.index("<nav>"):s.index("</nav>") + len("</nav>")]
    footer = s[s.index("<footer>"):s.index("</footer>") + len("</footer>")]
    tail_start = s.index('<div data-founding ')
    tail = s[tail_start:s.index('<script data-pbox-script>')]
    return head, nav, footer, tail


def _page_head(head: str, slug: str, meta: dict) -> str:
    url = f"https://outlier.host/{slug}/"
    h = re.sub(r"(?s)\s*<script type=\"application/ld\+json\">.*?</script>", "", head)
    h = re.sub(r'\s*<meta (?:property="og:[^"]+"|name="twitter:[^"]+")[^>]*>', "", h)
    h = re.sub(r'\s*<meta name="last-modified"[^>]*>', "", h)
    h = re.sub(r"<title>.*?</title>", f"<title>{meta['title']} | Outlier</title>", h, count=1, flags=re.S)
    h = re.sub(r'<meta name="description" content="[^"]*">',
               f'<meta name="description" content="{meta["description"]}">', h, count=1)
    h = re.sub(r'<link rel="canonical" href="[^"]*">', f'<link rel="canonical" href="{url}">', h, count=1)
    if slug == "download":
        h = h.replace('<meta name="viewport" content="width=device-width, initial-scale=1.0">',
                  '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
                  '  <meta name="robots" content="noindex">', 1)
    if slug == "pricing":
        schema = [
            {"@context": "https://schema.org", "@type": "WebPage", "name": meta["title"],
             "url": url, "dateModified": "2026-11-20"},
            {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
                {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
                for q, a in FAQ]},
        ]
        h += "".join('<script type="application/ld+json">' + json.dumps(v) + '</script>\n' for v in schema)
    return h + product_box.STYLE


def build(slug: str) -> str:
    meta = PAGES[slug]
    head, nav, footer, tail = _shell()
    version = product_box.current_version()
    box = product_box.box(f"{slug}-page", "answer", version, src=meta["src"])
    bundle = ('<p class="pbox-req">Or all three apps, Outlier, Crisp and Check Engine SEO: '
              + product_box.price_spans("$79 once", "Black Friday sale: $34.99 once, 29% off our November price of $49.50, through December 2. Then $79")
              + f': <a href="https://kerr-affiliate-hub.kerrco.workers.dev/buy/bundle?src=outlier-{slug}-bundle" rel="nofollow">the bundle</a>.</p>\n')
    box = box.replace('</p>\n', '</p>\n' + bundle, 1)
    return (
        "<!DOCTYPE html>\n<html lang=\"en\">\n<head>" + _page_head(head, slug, meta) + "</head>\n<body>\n"
        + nav + "\n<article>\n  <div class=\"wrap\">\n"
        + f"    <div class=\"crumb\"><a href=\"https://outlier.host/\">Outlier</a> &nbsp;›&nbsp; {meta['crumb']}</div>\n"
        + f"    <h1>{meta['title']}</h1>\n"
        + (pricing_content() if slug == "pricing" else "")
        + box
        + (pricing_faq() if slug == "pricing" else "")
        + "    <p><a href=\"https://outlier.host/\">← Back to outlier.host</a></p>\n"
        + "  </div>\n</article>\n\n" + footer + "\n" + tail + product_box.SCRIPT + '<script src="/js/mac-only.js?v=20261111" defer></script>\n' + "</body>\n</html>\n"
    )


def main(argv: list[str]) -> int:
    check = "--check" in argv
    changed = False
    for slug in PAGES:
        out = ROOT / slug / "index.html"
        new = build(slug)
        same = out.exists() and out.read_text(encoding="utf-8") == new
        changed |= not same
        print(f"  /{slug}/: {'unchanged' if same else ('would write' if check else 'written')}")
        if not check and not same:
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(new, encoding="utf-8")
    return 1 if check and changed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
