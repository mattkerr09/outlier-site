#!/usr/bin/env python3
"""Every question in a page's FAQPage schema is a question the page SHOWS.

Google's rule for FAQ markup: the questions and answers must be visible on the page. Measured 2026-10-20 on
outlier.host: 34 indexable pages broke it, three ways.
  - 28 generated /seo/ pages carried a stock FAQ block ("Does this affect which tier I should choose?" ... "Read the
    body above for the specific answer") and one /data/ page an FAQ block; no visible section showed any of it.
    Those blocks were removed.
  - 2 /vs/ pages created on 2026-09-16 carried the FAQ, headline and breadcrumb of /vs/outlier-vs-lm-studio/, copied
    at creation: Google was told /vs/when-ollama-is-enough/ is "Outlier vs LM Studio for agentic workflows".
  - 3 pages whose visible questions were reworded (the 2026-10-12 em-dash sweep turned "load — why?" into
    "load: why?") while the schema kept the old words.
  Those 5 were rebuilt from the questions and answers the page shows.
Nothing checked it: every other gate reads the visible text OR the JSON-LD, never one against the other.

    python3 scripts/faq_schema_visible_gate.py .             # check
    python3 scripts/faq_schema_visible_gate.py --self-check  # prove it can fail
"""
from __future__ import annotations

import html
import json
import os
import re
import sys

#: the site has ~250 pages; a scan that finds fewer was aimed at the wrong tree and proves nothing (meta_gate)
MIN_PAGES = 20

LD = re.compile(r'<script type="application/ld\+json">\s*(.*?)\s*</script>', re.S)


def norm(s: str) -> str:
    s = html.unescape(s or "").replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", s).strip().lower()


def visible_text(t: str) -> str:
    t = re.sub(r"<script.*?</script>|<style.*?</style>", " ", t, flags=re.S | re.I)
    return norm(re.sub(r"<[^>]+>", " ", t))


def faq_questions(t: str) -> list:
    out = []
    for b in LD.findall(t):
        try:
            d = json.loads(b)
        except ValueError:
            continue
        for item in (d if isinstance(d, list) else d.get("@graph", [d])):
            if isinstance(item, dict) and item.get("@type") == "FAQPage":
                out += [q.get("name", "") for q in item.get("mainEntity", []) if isinstance(q, dict)]
    return out


def check_page(t: str) -> list:
    if re.search(r'name="robots" content="[^"]*noindex', t):
        return []
    body = visible_text(t)
    return [q for q in faq_questions(t) if norm(q) not in body]


def main(root: str) -> int:
    bad = pages = faqs = 0
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if not d.startswith(".") and d != "node_modules"]
        for fn in fns:
            if not fn.endswith(".html"):
                continue
            p = os.path.join(dp, fn)
            with open(p, encoding="utf-8", errors="replace") as fh:
                t = fh.read()
            pages += 1
            faqs += bool(faq_questions(t))
            miss = check_page(t)
            for q in miss:
                print(f"FAQ NOT ON PAGE  {os.path.relpath(p, root)}: {q!r}")
            bad += len(miss)
    print(f"faq_schema_visible_gate: examined {pages} page(s), {faqs} with FAQ schema; "
          f"{bad} schema question(s) not shown on their page")
    if pages < MIN_PAGES:
        print(f"FAIL: only {pages} page(s) found, expected >= {MIN_PAGES}: wrong root, nothing proven")
        return 1
    return 1 if bad else 0


def self_check() -> int:
    ld = '<script type="application/ld+json">{"@type":"FAQPage","mainEntity":[{"@type":"Question","name":"Is it free?"}]}</script>'
    shown = f"<html><head>{ld}</head><body><h3>Is it free?</h3><p>Yes.</p></body></html>"
    hidden = f"<html><head>{ld}</head><body><h3>Is it paid?</h3></body></html>"
    # the question only inside the JSON-LD itself must not count as visible
    assert check_page(shown) == [] and check_page(hidden) == ["Is it free?"], "self-check failed"
    assert check_page(hidden.replace("<head>", '<head><meta name="robots" content="noindex">')) == []
    print("faq_schema_visible_gate --self-check: OK (a hidden question fails, a shown one passes)")
    return 0


if __name__ == "__main__":
    if "--self-check" in sys.argv:
        sys.exit(self_check())
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "."))
