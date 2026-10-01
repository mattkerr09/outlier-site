#!/usr/bin/env python3
"""Two small pages for the URLs a reviewer is most likely to type: /pricing/ and /download/.

    python3 scripts/typed_url_pages.py [--check]

WHY (CEO, 2026-09-29). outlier.host is on Porkbun's static hosting, which answers every
missing path with a bare "404 Not Found — openresty" page (the site's own 404.html is never
used). A Product Hunt reviewer who types outlier.host/pricing or /download hit that dead end.
The rest of the 404 problem is Matthew's hosting item; these two are the safety net.

WHAT THEY ARE. Real pages, not redirects: no meta refresh, no JS redirect, noindex, a
self-canonical, not in the sitemap (they are not SEO content). The site header and footer
(taken from /about/, so the pages look like the site), one heading, the product box
(scripts/product_box.box: price, pay-in-four, the live founders line, Download free and
Buy Pro through the hub with src "pricing-page" / "download-page", requirements, refund),
and a link home. Rebuilt from /about/ and product_box each run; --check writes nothing.
"""
from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import product_box  # noqa: E402

PAGES = {
    "pricing": {"title": "Outlier pricing", "crumb": "pricing", "src": "pricing-page",
                "description": "Outlier is free to start with Nano and Lite. Pro is $249 once, or 4 payments, with a 30-day refund."},
    "download": {"title": "Download Outlier", "crumb": "download", "src": "download-page",
                 "description": "Download Outlier for Mac: free to start, signed and notarized, for Apple silicon on macOS 26+."},
}


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
    h = h.replace('<meta name="viewport" content="width=device-width, initial-scale=1.0">',
                  '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
                  '  <meta name="robots" content="noindex">', 1)
    return h + product_box.STYLE


def build(slug: str) -> str:
    meta = PAGES[slug]
    head, nav, footer, tail = _shell()
    version = product_box.current_version()
    box = product_box.box(f"{slug}-page", "answer", version, src=meta["src"])
    return (
        "<!DOCTYPE html>\n<html lang=\"en\">\n<head>" + _page_head(head, slug, meta) + "</head>\n<body>\n"
        + nav + "\n<article>\n  <div class=\"wrap\">\n"
        + f"    <div class=\"crumb\"><a href=\"https://outlier.host/\">Outlier</a> &nbsp;›&nbsp; {meta['crumb']}</div>\n"
        + f"    <h1>{meta['title']}</h1>\n"
        + box
        + "    <p><a href=\"https://outlier.host/\">← Back to outlier.host</a></p>\n"
        + "  </div>\n</article>\n\n" + footer + "\n" + tail + product_box.SCRIPT + "</body>\n</html>\n"
    )


def main(argv: list[str]) -> int:
    check = "--check" in argv
    for slug in PAGES:
        out = ROOT / slug / "index.html"
        new = build(slug)
        same = out.exists() and out.read_text(encoding="utf-8") == new
        print(f"  /{slug}/: {'unchanged' if same else ('would write' if check else 'written')}")
        if not check and not same:
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(new, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
