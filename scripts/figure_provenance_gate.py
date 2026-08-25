#!/usr/bin/env python3
"""Performance figures on the page must match seo/_data/models.csv.

The page and its own data file drifted apart without anyone noticing, and the
drift ran in the flattering direction on the one that matters:

    tier     models.csv        index.html
    plus     1.59 tok/s        2.1 tok/s      <- page is 32% FASTER than the data
    quick    14.6 tok/s        "Not measured" <- page is more conservative
    vision   (blank)           16.31 tok/s    <- page has a figure the data lacks

Plus is the serious one. benchmarks.csv records K_SWEEP_RESULTS at 1.31/1.55/
1.59/1.61 tok/s across K=4/20/32/48, models.csv carries 1.59, and
docs/v11_engine_modes.md reports 1.67 for the V9 stable default. Nothing measured
is 2.1. The page is publishing the best of several conflicting runs, which is the
failure this site exists to argue against — a figure a reader cannot reproduce.

WHY THIS IS A GATE AND NOT A CORRECTION. Which run is authoritative is not mine
to decide: 1.59, 1.67 and 2.1 all claim M1 Ultra and V9, so picking one silently
would replace an unsourced number with a differently-unsourced number. The
conflict is recorded in CONFLICTS below, where it is visible in code and in CI
output, until someone who owns the measurement resolves it.

    python3 scripts/figure_provenance_gate.py
"""
from __future__ import annotations

import csv
import html
import re
import sys
from pathlib import Path


#: WHERE EACH HEADLINE FIGURE COMES FROM — recorded so nobody re-audits these, and
#: so a future edit has to argue with a source rather than a memory.
#:
#:   MMLU (53.0 / 77.5 / 81.5 / 89.5, n=200)
#:       The SHIPPING 4-bit build measured on this hardware. Deliberately NOT the
#:       same evaluation as FINAL_LAUNCH_NUMBERS.md, which reports the BF16 base on
#:       a B200 cluster at n=14042 (Nano 0.7250, Core 0.8467, int4 0.8408). Both are
#:       real; the page publishes the build a customer downloads and names it.
#:
#:   SWE-bench 46.0% (23/50, blind, official Docker, v1.11.757)
#:       docs/analysis/SWE_BLIND_v757_DENOMINATOR_2026-08-09.md. The run's own
#:       artifact said 24/54 = 44.4% and was CONTAMINATED — four rows left over from
#:       an unrelated run were graded. Scoped to the seed-42 N=50 sample it is
#:       23/50 = 46.0%, verified complete with `missing = pick50 - submitted == 0`.
#:       Note the contamination LOWERED the headline, so an unimpressive number is
#:       not evidence of a clean one.
#:       ⚠️ FINAL_SWE_BLIND_RESULTS.md in the parent repo reports 0/50 for compact
#:       on 2026-06-25 and CONTRADICTS this. It is a failed run, not a result: the
#:       same period measured 18/40 = 45.0%. Do not treat that file as authority.
#:
#:   Plus decode 1.59 tok/s
#:       sprints/v18_plus_ship/artifacts/K_SWEEP_RESULTS.md, the pre-ship sweep that
#:       locked the setting ("K=20 stays locked"). 2.1 had no artifact anywhere.
#:
#:   Quick decode — page says "Not measured", and that is RIGHT.
#:       models.csv carries 14.6, which OUTLIER_SESSION_HISTORY_RECON.md records as
#:       "site-only". The data file holds the unsourced figure, not the page.

#: Known, deliberate divergences. Each needs a reason and, where it exists, the
#: conflicting sources — so an exception cannot be added without stating its case.
CONFLICTS = {
    ("quick", "toks"): (
        "models.csv has 14.6; the page says 'Not measured'. The page is the more "
        "conservative claim, so it is safe to leave while the provenance of 14.6 "
        "is confirmed."),
    ("vision", "toks"): (
        "models.csv is blank; the page says 16.31, which IS sourced — "
        "docs/v11_engine_modes.md lists 16.31 for the V9 stable default. "
        "The data file is the one with the gap."),
}

MIN_TIERS = 5


def page_figures(root: Path):
    s = (root / "index.html").read_text(encoding="utf-8", errors="ignore")
    m = re.search(r'<section id="benchmarks".*?</section>', s, re.S)
    if not m:
        return {}
    out = {}
    for row in re.findall(r"<tr>(.*?)</tr>", m.group(1) if m.lastindex else m.group(0), re.S):
        cells = [html.unescape(re.sub(r"<[^>]+>", " ", c)).strip()
                 for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, re.S)]
        if len(cells) < 4 or "Outlier" not in cells[0]:
            continue
        name = cells[0].lower()
        tier = next((t for t in ("nano", "lite", "quick", "core", "code", "plus", "vision")
                     if t in name), None)
        if not tier:
            continue
        tier = "compact" if tier == "core" else tier
        # Find the decode cell by CONTENT, not position. This read cells[3]
        # until a HumanEval column was inserted at index 2 and shifted Decode
        # to index 4 — the gate then reported four tiers as "page says None",
        # i.e. it failed because the TABLE changed shape, not because a figure
        # diverged. Only the decode column carries "tok/s", so scanning is
        # both safe and immune to future columns.
        tok = next((re.search(r"([\d.]+)\s*tok/s", c) for c in cells[1:]
                    if re.search(r"([\d.]+)\s*tok/s", c)), None)
        out[tier] = tok.group(1) if tok else None
    return out



def check_plus_decode_sitewide(root):
    """Every page stating a Plus decode rate on an M1 Ultra must state models.csv's.

    Shipped defect this exists for: models.csv and the home page said 1.59 while 73
    occurrences across 43 other pages said 2.1 -- a ~32% overstatement of the
    flagship tier, several citing FINAL_LAUNCH_NUMBERS.md, which says 1.59. Twelve
    gates stayed green because this gate compared only the HOME page against
    models.csv. A figure is not sourced because one page agrees with the data file.

    Attribution is by NEAREST TIER NAME, not proximity. A first attempt flagged
    Core's 20.7 and Nano's 71.7 on pages where the word "Plus" merely appeared
    within 190 characters -- on a lineup page every number is near every tier.
    """
    import html as _h
    root = Path(root)
    mp = root / "seo" / "_data" / "models.csv"
    if not mp.is_file():
        return ["models.csv missing -- cannot verify Plus decode"]
    plus = next((r for r in csv.DictReader(mp.open()) if r["tier_id"] == "plus"), None)
    if not plus or not plus.get("m1_ultra_toks"):
        return ["models.csv has no Plus m1_ultra_toks -- cannot verify"]
    want = float(plus["m1_ultra_toks"])

    # The engine-comparison dataset measures V9/V10/V11 against each other on its own
    # per-token RSS protocol; its V9 row must stay on that protocol or the comparison
    # stops being like-for-like. It carries an inline note reconciling the two.
    EXEMPT = {"data/v11-streaming-engine-benchmarks/index.html"}
    TIER = re.compile(r"\b(Nano|Lite|Quick|Core|Code|Vision|Plus|397B)\b", re.I)
    # models.csv's column is m1_ultra_toks. A figure explicitly about other silicon
    # is a different measurement, not a contradiction.
    OTHER_SILICON = re.compile(r"\bM[234]\b|\bM1 (Pro|Max)\b", re.I)

    bad, scanned, checked = [], 0, 0
    for f in sorted(root.rglob("*.html")):
        rel = f.relative_to(root).as_posix()
        if "_seo_build" in rel or rel in EXEMPT:
            continue
        scanned += 1
        raw = f.read_text(errors="replace")
        # Meta/og/twitter descriptions live INSIDE a tag, so stripping tags deletes
        # them -- and they are exactly the text search engines and AI crawlers show.
        # A control aimed at one of them found the gate reading clean on a page whose
        # search snippet carried the wrong number.
        metas = " ".join(mm.group(1) for mm in re.finditer(
            r'<meta[^>]+content="([^"]*)"', raw, re.I))
        txt = _h.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", raw) + " " + metas))
        # A page whose whole subject is Plus states its speed without re-naming the
        # tier every time; attribution-by-nearest-name alone skips the page's point.
        page_is_plus = bool(re.search(r"397b|plus", rel, re.I) or
                            re.search(r"<title>[^<]*(397B|Plus)", raw, re.I))
        # The site spells the unit at least three ways. A gate that knows one spelling
        # reports clean on the other two: the first version of this check matched only
        # "tok/s" and sailed past a control that reintroduced the bug as
        # "2.1 tokens per second".
        for m in re.finditer(r"(?<![\d.])(\d+\.\d+)\s*(?:tok/s|tokens?[ /](?:per[ ])?sec(?:ond)?s?\b|tok/sec\b)", txt):
            before = txt[max(0, m.start() - 260): m.start()]
            names = TIER.findall(before)
            if names:
                if names[-1].lower() not in ("plus", "397b"):
                    continue                  # nearest tier is not Plus -- not its number
            elif not page_is_plus:
                continue                      # unattributed on a page not about Plus
            # A number carrying its own qualifier ("71.7 tok/s for a 4B model") belongs
            # to that model, however recently Plus was named in the prose before it.
            near = txt[max(0, m.start() - 46): m.start() + 46]
            if re.search(r"\b(4B|9B|26B|27B|35B)\b", near) or re.search(
                    r"\b(Nano|Lite|Quick|Core|Code|Vision)\b", near, re.I):
                continue
            if OTHER_SILICON.search(txt[max(0, m.start() - 160): m.start() + 80]):
                continue                      # a different machine, not a different claim
            if re.search(r"estimate|scaled|projected|approx", txt[max(0, m.start() - 200): m.start() + 120], re.I):
                continue                      # labelled as derived, not measured -- allowed to differ
            checked += 1
            if abs(float(m.group(1)) - want) > 0.005:
                bad.append(f"{rel}: Plus stated at {m.group(1)} tok/s, models.csv says {want}")
        # Bare figures in a table cell carry no unit -- the unit is in the column
        # header. Ten of the shipped 2.1s had this shape ("<td>Plus 397B (V9 paged,
        # K=20)</td><td>2.1</td>"), so a unit-anchored scan alone reports clean on the
        # single most common form of the defect.
        for row in re.finditer(r"<tr[^>]*>(.*?)</tr>", raw, re.S | re.I):
            body = row.group(1)
            if not re.search(r"Plus|397B", body, re.I):
                continue
            if re.search(r"\b(Nano|Lite|Quick|Core|Code|Vision)\b", body, re.I):
                continue          # a lineup row naming several tiers -- not attributable
            if re.search(r"estimate|scaled|projected|V10|V11", body, re.I):
                continue
            for cell in re.finditer(r"<t[dh][^>]*>\s*~?(\d+\.\d+)\s*(?:tok/s)?\s*</t[dh]>", body, re.I):
                got = float(cell.group(1))
                if got > 60 or abs(got - want) <= 0.005:
                    continue      # >60 cannot be a 397B decode rate; equal is fine
                if abs(got - want) > 0.005 and got < 60:
                    bad.append(f"{rel}: Plus table cell says {cell.group(1)}, models.csv says {want}")
                    checked += 1

    if scanned < 120:
        return [f"VACUITY: only {scanned} pages scanned; expected 120+"]
    if checked < 20:
        return [f"VACUITY: only {checked} Plus decode claims matched; the scan is likelier broken than the site"]
    return bad


def main(root_arg: str = ".") -> int:
    root = Path(root_arg)
    csv_path = root / "seo" / "_data" / "models.csv"
    if not csv_path.is_file():
        print(f"FAIL: {csv_path} not found — cannot compare anything.")
        return 1
    data = {r["tier_id"]: r for r in csv.DictReader(csv_path.open())}
    page = page_figures(root)

    print(f"tiers in models.csv: {len(data)} | tiers found on the page: {len(page)}")
    if len(page) < MIN_TIERS:
        print(f"\nFAIL: only {len(page)} tiers parsed from the page, expected >= {MIN_TIERS}.")
        print("      The scan is likelier broken than the page. Not reporting clean.")
        return 1

    fails, noted = [], []
    for tier, shown in page.items():
        want = (data.get(tier, {}).get("m1_ultra_toks") or "").strip()
        same = (shown or "") == want
        if same:
            continue
        key = (tier, "toks")
        if key in CONFLICTS:
            noted.append(f"  [known] {tier:<8} page={shown!s:<8} csv={want or '(blank)':<8} {CONFLICTS[key]}")
        else:
            fails.append(f"  {tier}: page says {shown!s}, models.csv says {want or '(blank)'} — "
                         f"undeclared divergence")
    for n in noted:
        print(n)
    if fails:
        print(f"\nFAIL ({len(fails)}):")
        for f in fails:
            print(f)
        print("\n  Either correct one side, or add an entry to CONFLICTS stating which "
              "sources disagree and why the page keeps its value.")
        return 1
    sitewide = check_plus_decode_sitewide(root)
    if sitewide:
        print(f"\nFAIL ({len(sitewide)}) — Plus decode disagrees with models.csv off the home page:")
        for f in sitewide[:25]:
            print(f"  {f}")
        if len(sitewide) > 25:
            print(f"  ... and {len(sitewide) - 25} more")
        return 1

    print("\nPASS — home-page figures match models.csv (or are declared conflicts), "
          "and every other page agrees on Plus decode.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "."))
