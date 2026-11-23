#!/usr/bin/env python3
"""Build the home page's FAQPage JSON-LD from the home page's OWN visible FAQ (section#faq, one Question per <details>).

RULES 77 (Article Studio, 23 Nov 2026): the home had 9 visible FAQ items and no FAQPage, so search and AI read none of them.
One source: the question is the <summary> text and the answer the rest of the <details>, whitespace collapsed. The price toggle
spans (data-pbox-regular / data-pbox-founding) are left OUT of the answer text, so the JSON-LD never states a sale price after the
sale or the regular price during it; prices live in the SoftwareApplication Offers with their validity dates.

    home_faq_jsonld.py write [index.html]   rewrite the block between the faq-jsonld markers in place
    home_faq_jsonld.py check [index.html]   exit 1 when the block on the page differs from what the visible FAQ gives
"""
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys

START, END = "<!-- faq-jsonld:start -->", "<!-- faq-jsonld:end -->"
VOID = {"br", "img", "hr", "input", "meta", "link", "source", "wbr"}


class FaqParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_faq = False       # inside section id="faq"
        self.section_depth = 0
        self.items, self.cur, self.part = [], None, None
        self.skip = 0             # depth inside a price-toggle span

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "section" and a.get("id") == "faq":
            self.in_faq, self.section_depth = True, 1
            return
        if not self.in_faq:
            return
        if tag == "section":
            self.section_depth += 1
        if self.skip:
            if tag not in VOID:
                self.skip += 1
            return
        if tag == "span" and ("data-pbox-regular" in a or "data-pbox-founding" in a):
            self.skip = 1
            return
        if tag == "details":
            self.cur, self.part = {"q": "", "a": ""}, None
        elif tag == "summary" and self.cur is not None:
            self.part = "q"
        elif tag in ("p", "div", "li") and self.cur is not None and self.part != "q":
            self.part = "a"
            if self.cur["a"]:
                self.cur["a"] += " "

    def handle_endtag(self, tag):
        if not self.in_faq:
            return
        if self.skip:
            self.skip -= 1
            return
        if tag == "summary":
            self.part = "a"
        elif tag == "details" and self.cur is not None:
            self.items.append({k: re.sub(r"\s+", " ", v).strip() for k, v in self.cur.items()})
            self.cur, self.part = None, None
        elif tag == "section":
            self.section_depth -= 1
            if self.section_depth == 0:
                self.in_faq = False

    def handle_data(self, data):
        if self.in_faq and not self.skip and self.cur is not None and self.part:
            self.cur[self.part] += data


def faq_items(html):
    p = FaqParser()
    p.feed(html)
    return [i for i in p.items if i["q"] and i["a"]]


def block(html):
    data = {"@context": "https://schema.org", "@type": "FAQPage",
            "mainEntity": [{"@type": "Question", "name": i["q"],
                            "acceptedAnswer": {"@type": "Answer", "text": i["a"]}} for i in faq_items(html)]}
    return (START + "\n  <script type=\"application/ld+json\">\n" + json.dumps(data, indent=2, ensure_ascii=False)
            + "\n  </script>\n  " + END)


def current(html):
    m = re.search(re.escape(START) + r".*?" + re.escape(END), html, re.S)
    return m.group(0) if m else None


def main(argv):
    cmd = argv[1] if len(argv) > 1 else "check"
    path = Path(argv[2] if len(argv) > 2 else Path(__file__).resolve().parents[1] / "index.html")
    html = path.read_text(encoding="utf-8")
    want, have = block(html), current(html)
    if cmd == "write":
        if have is None:
            print("no faq-jsonld markers in", path)
            return 2
        path.write_text(html.replace(have, want), encoding="utf-8")
        print(f"wrote {len(faq_items(html))} questions")
        return 0
    if have != want:
        print("FAQPage JSON-LD differs from the visible FAQ; run: scripts/home_faq_jsonld.py write")
        return 1
    print(f"FAQPage JSON-LD matches the visible FAQ ({len(faq_items(html))} questions)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
