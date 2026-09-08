#!/usr/bin/env python3
"""An annual figure WE computed must show the arithmetic. A quoted one must not.

Measured 2026-09-08: this site states annual costs for rivals that appear on no
vendor page. "$240/year for ChatGPT Plus" is our own $20 x 12. "$1,080 a year" is
$90 x 12. OpenAI publishes neither.

That is what makes them dangerous. Every price check here compares our page to a
vendor page, and a figure we computed is invisible to all of them because the number
exists nowhere upstream. If Plus moves to $25/month, "$240/year" is wrong and every
source-comparison stays green.

THE HARD PART IS TELLING DERIVED FROM QUOTED, and a word-proximity heuristic cannot.
A first version of this gate looked for annual figures near a justification word and
flagged Msty's "$149/yr" and Poe's "$49.99/year" -- both of which ARE on the vendor's
own pricing page. Demanding that a quoted price show arithmetic it never did would
have taught the site to explain a number it correctly copied.

So the discriminator is the arithmetic itself, not a word:

    an annual figure is DERIVED when a monthly figure ON THE SAME PAGE multiplies
    to it exactly.

Run on 2026-09-08 that split 21 annual figures into 4 derived and 17 quoted with no
overlap. Every quoted price failed the multiplication (Msty $149, Poe's five, xAI's
unverified $300, Perplexity's $400 and $3,250); every derived one hit to the cent.

WHAT THE DERIVED ONES MUST DO is what vs/outlier-vs-grok/ already does:

    "the only annual figure you can COMPUTE from xAI's own material is $360/year,
     at twelve monthly payments"

It says the figure was computed and shows what from, so a reader can redo it when the
monthly price moves. That sentence, or the monthly figure itself sitting beside the
annual one, is the whole requirement.

DECIMALS ARE ALLOWED ON PURPOSE. An earlier sweep for derived prices missed
"$37.25 x 4" because its pattern required whole dollars. Instalment splits are exactly
where decimals live, and an odd number is the strongest tell that a human did the sum.

RATCHET, currently EMPTY. The four bare figures this gate found on its first run were
FIXED rather than grandfathered, so no baseline file exists and every derived figure
must show its working. If one is ever added, edit it BY REMOVAL ONLY -- each removal
is a page that gained its derivation. A key goes stale when the page is edited near
the figure, which fails the item; that is the right direction for a ratchet.

    python3 scripts/derived_price_gate.py              # check
    python3 scripts/derived_price_gate.py <root>       # aim it (meta_gate needs this)
    python3 scripts/derived_price_gate.py --self-check # prove it can fail
"""
from __future__ import annotations

import html
import json
import os
import re
import sys

BASELINE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "derived_price_baseline.json")
WINDOW = 240            # characters either side in which the derivation must appear
MIN_ANNUAL = 12         # vacuity guard: a site with fewer annual figures is not this one
MULTIPLIERS = {12: "twelve monthly payments", 24: "twenty-four monthly payments"}

AMOUNT = r"\$(\d[\d,]*(?:\.\d\d)?)"
PER = r"\s*(?:/|\s+a\s+|\s+per\s+)\s*"
ANNUAL = re.compile(AMOUNT + PER + r"(?:year|yr\b|annum)", re.I)
MONTHLY = re.compile(AMOUNT + PER + r"(?:month|mo\b)", re.I)

#: evidence the figure was computed rather than copied off a pricing page
JUSTIFIED = re.compile(
    r"(?i)\bcomput\w+|\bderiv\w+|\bwork(?:ed|ing)\s+out\b|\bannualis\w+|\bannualiz\w+|"
    r"(?:×|x|\*)\s*(?:12|24)\b|\btwelve\b|\btwenty-four\b|\bmonthly\s+rate\b|"
    r"\bat\s+(?:the\s+)?published\s+monthly\b|" + AMOUNT + PER + r"(?:month|mo\b)")


def money(s: str) -> float:
    return float(s.replace(",", ""))


def visible(page_html: str) -> str:
    body = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", page_html, flags=re.S)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", body)))


def pages(site_root: str):
    for root, _dirs, files in os.walk(site_root):
        if any(x in root for x in (".git", "_seo_build", "scripts", "node_modules")):
            continue
        for f in sorted(files):
            if f.endswith(".html") and ".pre" not in f:
                p = os.path.join(root, f)
                yield os.path.relpath(p, site_root), \
                    visible(open(p, encoding="utf-8", errors="replace").read())


def survey(site_root: str = "."):
    """Every annual money figure, classified by whether the page's own monthlies reach it.

    Returns (rel_path, "$240/year", derivation_or_None, justified_bool).
    """
    rows = []
    for rel, text in pages(site_root):
        monthlies = {money(m.group(1)): m.group(0) for m in MONTHLY.finditer(text)}
        for a in ANNUAL.finditer(text):
            got = money(a.group(1))
            src = None
            for mult, phrase in MULTIPLIERS.items():
                hit = [v for v in monthlies if abs(v * mult - got) < 0.005]
                if hit:
                    src = f"{monthlies[hit[0]]} x {mult} ({phrase})"
                    break
            near = text[max(0, a.start() - WINDOW): a.end() + WINDOW]
            rows.append((rel, a.group(0).strip(), src, bool(JUSTIFIED.search(near))))
    return rows


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    site_root = args[0] if args else "."

    if "--self-check" in sys.argv:
        page = ("Plus is $20/month. " + "filler " * 60 +
                "Over a year that is $240/year, and Msty asks $149/yr.")
        got = survey.__wrapped__ if hasattr(survey, "__wrapped__") else None
        monthlies = {money(m.group(1)) for m in MONTHLY.finditer(page)}
        assert monthlies == {20.0}, f"self-check: monthly not seen: {monthlies}"
        found = {a.group(1) for a in ANNUAL.finditer(page)}
        assert found == {"240", "149"}, f"self-check: annuals not seen: {found}"
        assert not JUSTIFIED.search("Over a year that is $240/year, and Msty asks $149/yr."), \
            "self-check: a bare sentence reads as justified"
        assert JUSTIFIED.search("$240/year, computed at twelve monthly payments"), \
            "self-check: a justified sentence reads as bare"
        assert abs(20.0 * 12 - 240) < 0.005 and all(abs(20.0 * m - 149) > 0.005
                                                    for m in MULTIPLIERS), \
            "self-check: the arithmetic does not separate derived from quoted"
        print("self-check: $240 is derived from $20/month, $149 is not derivable. OK")

    rows = survey(site_root)
    if len(rows) < MIN_ANNUAL:
        print(f"FAIL: only {len(rows)} annual money figure(s) under {site_root!r}, "
              f"expected at least {MIN_ANNUAL}.")
        print("      A gate that checked nothing prints the same word as a clean one.")
        return 1

    derived = [r for r in rows if r[2]]
    bare = [r for r in derived if not r[3]]
    baseline = json.load(open(BASELINE)) if os.path.exists(BASELINE) else {}
    new = [r for r in bare if f"{r[0]}|{r[1]}" not in baseline]

    print(f"derived_price_gate: {len(rows)} annual figure(s); {len(derived)} computable "
          f"from a monthly on the same page, {len(rows) - len(derived)} quoted")
    print(f"derived_price_gate: {len(bare)} derived figure(s) show no derivation; "
          f"{len(baseline)} baselined")

    if new:
        print(f"\nFAIL ({len(new)} new):")
        for rel, fig, src, _ in new:
            print(f"  {rel}: \"{fig}\" is {src} — this page computed it.")
            print("       No vendor page carries this number, so no source check can catch")
            print("       it when the monthly price moves. Say what it was computed from,")
            print("       the way vs/outlier-vs-grok/ does.")
        return 1
    print("\nPASS — every computed annual figure shows what it was computed from.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
