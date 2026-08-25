#!/usr/bin/env python3
"""Outlier has no monthly plan. Fail if any page prices it as though it does.

Matthew retired the monthly offer ("lets not do monthly and only do 249").
Commit 77ee3242 recorded that the offer was "now at ZERO across the site" —
and it was not. Seven prose and table claims survived, including a comparison
table that priced Outlier Pro at "$9 / month" and a sentence inviting the
reader to rent it monthly. They survived because nothing enforced the decision;
the sweep that removed 283 of them was a one-off, and a one-off cannot hold a
line. This gate is the thing that holds it.

Two checks, because the damage took two shapes:

1. Structural. In any comparison table, find the price row and the columns
   whose header names Outlier, then assert those cells carry no per-month
   unit. This is the check that catches a table cell, where prose patterns do
   not apply and where a wrong number is most likely to be believed.

2. Attribution. In prose, a monthly figure bound directly to Outlier by a verb
   ("Outlier Pro is $9/mo", "Our Pro at $9 a month"). Deliberately tight: an
   earlier proximity heuristic reported 15 hits, all of them competitor prices
   that merely sat near the word Outlier in a table header. A gate that cries
   wolf gets ignored, and an ignored gate is the same as no gate.

$9 specifically is also flagged wherever it is attributed to us, with or
without a unit, because $9 was the retired price — it is the fingerprint of
this particular corruption rather than a generic mistake.

What it does not catch, stated plainly so nobody trusts it further than it
goes: replayed against the eight pre-fix pages it fires on five of the seven
real defects. The two it misses have no subject to bind to — "the other is a $9
app you download" and "Or $9/month if you'd rather rent" name no product, and a
pattern loose enough to catch them matched competitor prices in nav text. This
gate holds the direct claim; it is not a substitute for reading the sentence.

Run: python3 scripts/retired_monthly_gate.py <site-root>
"""
import html
import os
import re
import sys

MONTHLY = re.compile(r'\$\s?\d+(?:\.\d\d)?\s*(?:/\s*(?:mo\b|month)|\s+(?:per|a)\s+month|\s+monthly)', re.I)
OUTLIER_COL = re.compile(r'(?i)\boutlier\b')
PRICE_ROW = re.compile(r'(?i)^\s*(price|cost|monthly cost|what you pay)\b')

# Attribution must be DIRECT: our name, a linking verb, then the price with at
# most a filler word between. A looser window (40 chars either side, run over
# the whole page flattened) reported 8 hits and every one was a competitor's
# price that happened to sit near the word "Outlier" in a nav bar, a breadcrumb
# or a related-links list. Matching per block element rather than per page is
# what stops nav text from being read as body prose.
_SUBJ = r'(?:outlier(?:\s+pro)?|our\s+pro)'
_FILL = r'(?:\s+(?:only|just|now|still))?\s+'
PROSE = re.compile(r'(?i)\b' + _SUBJ + r'\b\s+(?:is|at|costs?)' + _FILL +
                   r'(\$\s?\d+(?:\.\d\d)?\s*(?:/\s*(?:mo\b|month)|\s+(?:per|a)\s+month|\s+monthly))')
RETIRED = re.compile(r'(?i)\b' + _SUBJ + r'\b\s+(?:is|at|costs?)' + _FILL + r'(\$9\b(?!\.99))')

# A markdown pricing line has no verb: "- Pro: $9/mo - all six tiers…". The
# verb-based patterns above are blind to it, which I only learned by running
# this gate against the real pre-fix llms.txt and watching it report OK on the
# exact line that motivated the gate. A label, a colon, a price.
LABELLED = re.compile(
    r'(?im)^[\s*\-\u2022]*(?:outlier\s+)?(?:pro|founders(?:\s+lifetime)?|lifetime)\s*[:\u2013\u2014-]'
    r'[^\n]*?(\$\s?\d+(?:\.\d\d)?\s*(?:/\s*(?:mo\b|month)|\s+(?:per|a)\s+month|\s+monthly))')

CELL = re.compile(r'(?is)<t([hd])[^>]*>(.*?)</t\1>')
BLOCK = re.compile(r'(?is)<(p|li|td|th|h[1-6]|figcaption|summary|dd|blockquote)\b[^>]*>(.*?)</\1>')


def text_of(fragment):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', fragment))).strip()


def check_tables(src):
    """Outlier-headed cells in a price row must carry no per-month unit."""
    out = []
    for table in re.findall(r'(?is)<table.*?</table>', src):
        rows = re.findall(r'(?is)<tr[^>]*>.*?</tr>', table)
        if len(rows) < 2:
            continue
        header = [text_of(c[1]) for c in CELL.findall(rows[0])]
        ours = [i for i, h in enumerate(header) if OUTLIER_COL.search(h)]
        if not ours:
            continue
        for row in rows[1:]:
            cells = [text_of(c[1]) for c in CELL.findall(row)]
            if not cells or not PRICE_ROW.match(cells[0]):
                continue
            for i in ours:
                if i < len(cells) and MONTHLY.search(cells[i]):
                    out.append(f'table column {header[i]!r}, row {cells[0]!r}: {cells[i]!r}')
    return out


def _scan(flat, where):
    out = []
    for rx, label in ((PROSE, 'monthly price'), (RETIRED, 'the retired $9 price')):
        for m in rx.finditer(flat):
            out.append(f'{label} in {where}: …{flat[max(0, m.start() - 50):m.end() + 25].strip()}…')
    return out


def check_prose(src):
    body = re.sub(r'(?is)<(script|style|nav|footer)\b.*?</\1>', ' ', src)
    out = []
    for tag, inner in BLOCK.findall(body):
        flat = text_of(inner)
        if flat:
            out += _scan(flat, f'<{tag}>')
    return out


def check_plain_text(src):
    """llms.txt and friends are served too, and a line is their block element.

    This gate shipped walking *.html only, and llms.txt — the file whose entire
    job is telling AI crawlers what we cost — advertised "Pro: $9/mo" straight
    through it. robots.txt names GPTBot, ClaudeBot and PerplexityBot explicitly,
    so the one place the dead price survived was the one place aimed squarely at
    the systems a buyer asks about us. A gate that skips a category eventually
    reports clean on a defect inside it.
    """
    out = []
    for i, line in enumerate(src.splitlines(), 1):
        flat = re.sub(r'\s+', ' ', line).strip()
        if not flat:
            continue
        out += _scan(flat, f'line {i}')
        for m in LABELLED.finditer(flat):
            out += [f'a plan line priced monthly, line {i}: …{flat[:90].strip()}…']
    return out


def main(root):
    failures = []
    checked = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in ('.git', 'node_modules', 'fonts', '_seo_build')]
        for name in filenames:
            is_html = name.endswith('.html')
            is_text = name.endswith(('.txt', '.md'))
            if not (is_html or is_text):
                continue
            path = os.path.join(dirpath, name)
            src = open(path, encoding='utf-8', errors='replace').read()
            checked += 1
            problems = (check_tables(src) + check_prose(src)) if is_html else check_plain_text(src)
            for problem in problems:
                failures.append(f'{os.path.relpath(path, root)}: {problem}')

    if not checked:
        print('retired_monthly_gate: no HTML found — the check proved nothing', file=sys.stderr)
        return 1
    if failures:
        print(f'retired_monthly_gate: FAIL ({len(failures)} across {checked} pages)', file=sys.stderr)
        for f in failures:
            print(f'  {f}', file=sys.stderr)
        print('\nOutlier has no monthly plan. Price it as a one-time purchase.', file=sys.stderr)
        return 1
    print(f'retired_monthly_gate: ok ({checked} pages, no monthly pricing claimed for Outlier)')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else '.'))
