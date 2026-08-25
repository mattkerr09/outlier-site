#!/usr/bin/env python3
"""Our own price must never appear in a competitor's column.

This is the shape the bulk price replace took, and it is the most damaging one
because a comparison table is exactly where a reader looks for the number. The
ChatGPT and Perplexity pages both showed "$249 once" in the *rival's* Price cell
— our lifetime price wearing their name — and the Windsurf page listed Devin's
Max tier at "$249/mo" when Devin charges $200. Two of those sat live for weeks,
through a full drift audit, because every one of them is a well-formed table
containing a real price. Nothing about the markup is wrong; only the attribution
is, and no gate we had could see attribution.

The invariant is narrow on purpose: in a table that has at least one column
naming Outlier and at least one that does not, no cell under a non-Outlier
column may contain our canonical price. Column 0 is skipped — it holds row
labels, not values.

The price is read from index.html's price block rather than written here, so
there is exactly one place in the repo where that number lives. A gate carrying
its own copy of the figure it guards would be the same duplication that produced
the bug.

If a competitor ever genuinely charges what we charge, this gate will fail and
should be edited deliberately, with the coincidence noted. That friction is the
point: our price appearing under a rival's name should always require a human to
say "yes, really".

Run: python3 scripts/rival_price_gate.py <site-root>
"""
import html
import os
import re
import sys

CELL = re.compile(r'(?is)<t([hd])[^>]*>(.*?)</t\1>')
OUTLIER = re.compile(r'(?i)\boutlier\b')
PRICE_IN_INDEX = re.compile(r'<div class="price">(\$\d[\d,]*)\s*<small>once</small></div>')


def text_of(fragment):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', fragment))).strip()


def canonical_price(root):
    index = os.path.join(root, 'index.html')
    if not os.path.exists(index):
        return None
    m = PRICE_IN_INDEX.search(open(index, encoding='utf-8', errors='replace').read())
    return m.group(1) if m else None


def check(src, price):
    found = []
    tables = 0
    for table in re.findall(r'(?is)<table.*?</table>', src):
        rows = re.findall(r'(?is)<tr[^>]*>.*?</tr>', table)
        if len(rows) < 2:
            continue
        header = [text_of(c[1]) for c in CELL.findall(rows[0])]
        ours = {i for i, h in enumerate(header) if OUTLIER.search(h)}
        theirs = [i for i in range(1, len(header)) if i not in ours]
        if not ours or not theirs:
            continue
        tables += 1
        for row in rows[1:]:
            cells = [text_of(c[1]) for c in CELL.findall(row)]
            if not cells:
                continue
            for i in theirs:
                if i < len(cells) and re.search(re.escape(price) + r'\b', cells[i]):
                    found.append(f'column {header[i]!r}, row {cells[0]!r}: {cells[i]!r}')
    return tables, found


def main(root):
    price = canonical_price(root)
    if not price:
        print('rival_price_gate: could not read the canonical price from index.html — '
              'the check would have passed while testing nothing', file=sys.stderr)
        return 1

    failures = []
    tables = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in ('.git', 'node_modules', 'fonts', '_seo_build')]
        for name in filenames:
            if not name.endswith('.html'):
                continue
            path = os.path.join(dirpath, name)
            src = open(path, encoding='utf-8', errors='replace').read()
            n, found = check(src, price)
            tables += n
            for f in found:
                failures.append(f'{os.path.relpath(path, root)}: {f}')

    if not tables:
        print('rival_price_gate: found no comparison table with both an Outlier column '
              'and a rival column — nothing was actually checked', file=sys.stderr)
        return 1
    if failures:
        print(f'rival_price_gate: FAIL ({len(failures)} across {tables} comparison tables)', file=sys.stderr)
        for f in failures:
            print(f'  {f}', file=sys.stderr)
        print(f'\n{price} is our price. It must not appear under a competitor.', file=sys.stderr)
        return 1
    print(f'rival_price_gate: ok ({tables} comparison tables, {price} appears in no rival column)')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else '.'))
