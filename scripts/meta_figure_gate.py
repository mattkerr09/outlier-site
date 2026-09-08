#!/usr/bin/env python3
"""A number in a meta description must be a number on the page.

Found 2026-09-08 by asking which claims the other gates CANNOT see. Every text
check here reaches the page through a tag-strip -- `re.sub(r"<[^>]+>", " ", html)`
-- and two whole representations die in that one line:

  * meta/og/twitter descriptions live INSIDE a tag, so stripping tags deletes them
  * JSON-LD lives inside <script>, which the same helpers drop wholesale

Both are exactly the text a search engine and an AI crawler quote. So the site had
a class of claim that was published, indexed, read first by most visitors -- and
invisible to all 24 gates.

It was not hypothetical. learn/ai-subscription-stacking said:

    body:   "$20 + $20 + $20 + $10 + $20 = $90/mo, ~$1,080/yr"   (five places, exact)
    meta:   "...you're near $1,100 a year, forever."             (three places)

$1,100 appears nowhere in the body and is not the arithmetic. It was in the meta
description, the og:description AND the JSON-LD Article.description -- three copies
of a figure contradicting the page under them, and no check could reach any of them.

THE RULE IS NOT "SHOW YOUR WORKING". A 155-character description cannot carry a
derivation, and demanding one would be the wrong ask. The rule that fits the format
is exact and needs no heuristic:

    every money figure in a description must appear verbatim in the visible body

If the body says $1,080 the description may say $1,080. It may also say nothing.
What it may not do is introduce a number the page does not support -- which is the
only failure mode this position has, because nobody writes an argument in a meta tag.

    python3 scripts/meta_figure_gate.py              # check
    python3 scripts/meta_figure_gate.py <root>       # aim it
    python3 scripts/meta_figure_gate.py --self-check # prove it can fail
"""
from __future__ import annotations

import html
import json
import os
import re
import sys

BASELINE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "meta_figure_baseline.json")
MIN_DESCRIBED = 150    # vacuity guard on REACH -- see the note in main()

MONEY = re.compile(r"\$\d[\d,]*(?:\.\d\d)?")
#: the meta names whose content is quoted back to a reader
DESCRIPTIVE = re.compile(r"(?i)(description|title)")


def amount(fig: str) -> str:
    """Compare money by VALUE, not by typography.

    Added after sweeping the same meta/JSON-LD position for non-money claims. RAM
    figures produced 22 findings and every one was formatting: the body writes
    "16 GB", the description writes "16GB", same fact. Money escaped that because
    this site writes "$1,080" consistently -- but nothing enforces the comma, and a
    description saying "$1080" against a body saying "$1,080" would have been
    reported as a contradiction that is not one. Strip the separators and compare
    the number.
    """
    value = fig.lstrip("$").replace(",", "")
    try:
        return f"{float(value):.2f}"
    except ValueError:
        return fig


def body_text(raw: str) -> str:
    """What a reader sees -- the same tag-strip every other gate uses, on purpose."""
    b = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", raw, flags=re.S)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", b)))


def described(raw: str):
    """(where, text) for every description a crawler reads: meta, og, and JSON-LD."""
    out = []
    for m in re.finditer(r"<meta\b([^>]*)>", raw, re.I):
        attrs = m.group(1)
        key = re.search(r'(?:name|property)\s*=\s*"([^"]*)"', attrs, re.I)
        val = re.search(r'content\s*=\s*"([^"]*)"', attrs, re.I)
        if key and val and DESCRIPTIVE.search(key.group(1)):
            out.append((f"meta {key.group(1)}", html.unescape(val.group(1))))
    for m in re.finditer(r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>',
                         raw, re.S | re.I):
        blob = m.group(1)
        try:
            data = json.loads(blob)
        except Exception:
            # A gate that silently skips what it cannot parse is a gate that reports
            # clean on a broken file. Fall back to the raw text rather than skipping.
            out.append(("JSON-LD (unparsed)", blob))
            continue
        stack = [data]
        while stack:
            node = stack.pop()
            if isinstance(node, dict):
                for k, v in node.items():
                    if isinstance(v, (dict, list)):
                        stack.append(v)
                    elif isinstance(v, str) and DESCRIPTIVE.search(k):
                        out.append((f"JSON-LD {k}", v))
            elif isinstance(node, list):
                stack.extend(node)
    return out


def survey(site_root: str = "."):
    """(page, where, figure) for each description figure missing from the body."""
    bad, with_desc = [], 0
    for root, _d, files in os.walk(site_root):
        if any(x in root for x in (".git", "_seo_build", "scripts", "node_modules")):
            continue
        for f in sorted(files):
            if not f.endswith(".html") or ".pre" in f:
                continue
            path = os.path.join(root, f)
            rel = os.path.relpath(path, site_root)
            raw = open(path, encoding="utf-8", errors="replace").read()
            seen = {amount(x) for x in MONEY.findall(body_text(raw))}
            here = described(raw)
            for where, text in here:
                figs = MONEY.findall(text)
                for fig in figs:
                    if amount(fig) not in seen:
                        bad.append((rel, where, fig, text[:90]))
            if here:
                with_desc += 1
    return bad, with_desc


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    site_root = args[0] if args else "."

    if "--self-check" in sys.argv:
        probe = ('<meta name="description" content="near $1,100 a year">'
                 '<p>the total is $1,080 a year</p>')
        found = {f for _w, t in described(probe) for f in MONEY.findall(t)}
        assert found == {"$1,100"}, f"self-check: description figures not read: {found}"
        assert "$1,100" not in set(MONEY.findall(body_text(probe))), \
            "self-check: a tag-stripped body still shows the meta figure"
        assert "$1,080" in set(MONEY.findall(body_text(probe))), \
            "self-check: the body figure was lost"
        ld = '<script type="application/ld+json">{"description": "costs $7"}</script>'
        assert ("JSON-LD description", "costs $7") in described(ld), \
            "self-check: JSON-LD description not read"
        assert "$7" not in body_text(ld), "self-check: JSON-LD leaked into the body text"
        assert amount("$1,080") == amount("$1080") == "1080.00", \
            "self-check: the comma is being treated as part of the number"
        assert amount("$20") == amount("$20.00") == "20.00", \
            "self-check: cents normalisation is wrong"
        assert amount("$20") != amount("$2"), \
            "self-check: normalisation collapses different amounts — the first version of " \
            "this helper used rstrip('.0'), which turns $20.00 into $2"
        print("self-check: meta and JSON-LD figures are read, neither reaches the body text "
              "the other gates use, and $1,080/$1080 compare equal while $20/$2 do not. OK")

    bad, with_desc = survey(site_root)
    if with_desc < MIN_DESCRIBED:
        print(f"FAIL: only {with_desc} page(s) under {site_root!r} have a description this "
              f"gate could read; expected at least {MIN_DESCRIBED}.")
        print("      GUARDED ON REACH, NOT ON FINDINGS. This counted pages carrying money in")
        print("      a description until 2026-09-08, which is fine while seven do — but the")
        print("      AdPlaybook port has ZERO such pages by editorial habit, and that guard")
        print("      would have failed a clean site forever. A guard that counts findings")
        print("      cannot tell \"nothing wrong\" from \"nothing read\".")
        return 1

    baseline = json.load(open(BASELINE)) if os.path.exists(BASELINE) else {}
    new = [b for b in bad if f"{b[0]}|{b[2]}" not in baseline]

    print(f"meta_figure_gate: {with_desc} page(s) with a readable description; "
          f"{len(bad)} figure(s) in one are not in the body it describes")
    print(f"meta_figure_gate: {len(baseline)} baselined")

    if new:
        print(f"\nFAIL ({len(new)} new):")
        for rel, where, fig, text in new[:8]:
            print(f"  {rel}: {where} says {fig}, which is not on the page.")
            print(f"       \"{text}\"")
            print("       This is what a search engine and an AI crawler quote, and no")
            print("       other gate can see it — they all reach the page through a")
            print("       tag-strip, which deletes meta content and JSON-LD alike.")
        return 1
    print("\nPASS — every figure in a description is a figure on its page.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
