#!/usr/bin/env python3
"""Every stated tier COUNT on the site must match how many tiers actually ship.

Why this exists
---------------
Adding Qwen3.8 (vision38) put a row in models.csv and a chip in the hero, and
tier_lineup_gate covers those. But 113 sentences across 45 pages encode the count
in prose — "seven tiers", "all seven", "the other six tiers", "six tiers on
Apache 2.0 Qwen checkpoints". Those are correct while seven tiers ship and become
wrong the moment an eighth does, in 45 places at once, silently.

That is the Plus-decode shape exactly: the home page was corrected and 43 other
pages kept the old figure for months.

The counts are NOT interchangeable
----------------------------------
A global 7 -> 8 rewrite would be wrong. Each phrase counts a different set:

    "seven tiers"        ALL shipping tiers                  -> total
    "all seven"          ALL shipping tiers                  -> total
    "the other six"      all EXCEPT Plus                     -> total - 1
    "six tiers ... Apache 2.0 ... one on Gemma"  Apache-licensed only -> total - 1
                         (Quick is the Gemma one)

Bind the number to its subject before touching it — the same rule that stopped a
$9 sweep rewriting competitor prices and an OCR sweep rewriting competitor
products.

What counts as shipping
-----------------------
models.csv rows whose `source` says SHIPS IN THE NEXT BUILD are in the catalog but
not in the DMG a customer downloads, so they do NOT count until that build lands.
Remove that marker and this gate immediately demands the prose be updated.
"""
import csv
import html
import re
import sys
from pathlib import Path

NEXT_BUILD = "SHIPS IN THE NEXT BUILD"
MIN_PAGES = 120          # vacuity guard: a short scan is a broken scan
MIN_CLAIMS = 40          # vacuity guard: this site states the count a lot

WORD = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five",
        6: "six", 7: "seven", 8: "eight", 9: "nine", 10: "ten"}


def shipping_tier_count(root: Path):
    """Tiers a customer can actually get today, and the ones held back."""
    csv_path = root / "seo" / "_data" / "models.csv"
    if not csv_path.is_file():
        return None, None
    shipping, pending = [], []
    for r in csv.DictReader(csv_path.open()):
        tid = (r.get("tier_id") or "").strip()
        if not tid:
            continue
        (pending if NEXT_BUILD in (r.get("source") or "") else shipping).append(tid)
    return shipping, pending


def main(root_arg: str = ".") -> int:
    root = Path(root_arg)
    shipping, pending = shipping_tier_count(root)
    if shipping is None:
        print("FAIL: seo/_data/models.csv not found — nothing to count against.")
        return 1
    total = len(shipping)
    if total < 5:
        print(f"FAIL: only {total} shipping tiers parsed from models.csv.")
        print("      The scan is likelier broken than the product. Not reporting clean.")
        return 1

    # PRECISION OVER COVERAGE. The first version of this gate produced 13
    # findings and every one was mine, not the site's. "tier" is polysemous here:
    # a colour ladder ("three tiers still read as three tiers"), a COMPETITOR's
    # pricing tiers ("$7.99 and $19.99 for the two tiers"), and "two versions of
    # one tier" on a disk-space page. It also mis-assigned "six of our seven
    # tiers are Apache" — seven is the TOTAL there, six is the subset — and
    # assumed "the other five tiers" meant all-except-Plus when it means
    # all-except-the-free-two.
    #
    # So this checks only two shapes that unambiguously count OUR lineup, and
    # requires the sentence to be about Outlier. Everything else is left alone:
    # a gate that cries wolf gets ignored, and an ignored gate hides real drift.
    # v1.11.794: DIGITS TOO. This gate matched only spelled-out numbers, so it
    # reported PASS while 114 places said "7 model tiers" in digit form — the
    # standard CTA boilerplate on 104 pages, every one of them stale the day an
    # eighth tier shipped. Knowing one spelling of a number is the same hole as
    # knowing one spelling of a unit, which is what let "tokens per second" slip
    # past the decode-rate check.
    NUMS = "|".join(list(WORD.values()) + [str(k) for k in WORD])
    OURS = re.compile(r'\bOutlier\b|\bour\b|\bmy\b|\bships?\b|\blineup\b', re.I)
    #  "six of our seven tiers"  -> second number is the TOTAL
    # BOTH tokens must be numbers. `(\w+) of ... (\w+) tiers` matched "two VERSIONS of one tier"
    # on a disk-space page and read it as a lineup count of one.
    OF_SHAPE = re.compile(rf'\b({NUMS}) of (?:our |my |the )?({NUMS}) tiers?\b', re.I)
    #  "seven tiers" -> the TOTAL, but NOT when preceded by "of".
    #  ADJECTIVES INTERVENE CONSTANTLY and an earlier version missed all of them:
    #  "seven MODEL tiers", "seven FIXED tiers", "seven CURATED tiers", "seven
    #  ON-DEVICE tiers", "seven READY-TO-RUN tiers". With `(\w+) tiers?` the capture
    #  lands on the adjective, which is not a number word, so the claim is silently
    #  skipped -- 34 occurrences across 21 files, every one of which would have gone
    #  stale on build day while this gate reported PASS.
    #  The capture MUST be anchored on number words. A version using (\w+) with
    #  optional intervening words captured "the" in "the seven model tiers" -- the
    #  number was eaten as an adjective and matched claims fell from 46 to 21, which
    #  the vacuity guard caught.
    TOTAL_SHAPE = re.compile(
        rf'(?<!of )(?<!of our )(?<!of my )\b({NUMS})[\s-]+(?:[\w-]+[\s-]+){{0,2}}tiers?\b', re.I)
    #  "Seven-tier lineup" -- hyphenated, no plural
    HYPHEN_SHAPE = re.compile(rf'\b({NUMS})-tier\b', re.I)
    #  "Pro unlocks all seven", "one of the seven" -- the noun is dropped entirely
    BARE_SHAPE = re.compile(rf'\b(?:all|of the|of)\s+({NUMS})\b(?![\s-]*[\w-]*[\s-]*tiers?)', re.I)

    bad, pages, claims = [], 0, 0
    for f in sorted(root.rglob("*.html")):
        rel = f.relative_to(root).as_posix()
        if "_seo_build" in rel:
            continue
        pages += 1
        raw = f.read_text(errors="replace")
        metas = " ".join(m.group(1) for m in re.finditer(
            r'<meta[^>]+content="([^"]*)"', raw, re.I))
        txt = html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", raw) + " " + metas))
        # v1.11.795: ON A PAGE THAT IS ENTIRELY ABOUT US, EVERY TIER COUNT IS OURS.
        # The ownership check looks for "Outlier"/"our"/"lineup" within 120 chars, and
        # the home page's own pricing answer — "Pro includes everything: all eight
        # tiers and every feature" — carries none of them, because a page about
        # Outlier does not keep saying Outlier. A planted regression there went
        # undetected: the gate skipped the claim rather than judging it.
        page_is_ours = (rel == "index.html" or rel.endswith("/index.html") and
                        re.search(r"<title>[^<]*Outlier", raw, re.I) is not None)
        consumed = []
        for m in OF_SHAPE.finditer(txt):
            ctx = txt[max(0, m.start() - 120): m.start() + 120]
            if not (page_is_ours or OURS.search(ctx)):
                continue
            word = m.group(2).lower()
            if word not in WORD.values() and not word.isdigit():
                continue
            consumed.append((m.start(), m.end()))
            claims += 1
            if word != WORD.get(total) and word != str(total):
                bad.append(f"{rel}: 'of our {word} tiers' — {total} ship. …{ctx.strip()[:110]}")
        for m in TOTAL_SHAPE.finditer(txt):
            if any(a <= m.start() < b for a, b in consumed):
                continue
            word = m.group(1).lower()
            if word not in WORD.values() and not word.isdigit():
                continue
            ctx = txt[max(0, m.start() - 120): m.start() + 120]
            if not (page_is_ours or OURS.search(ctx)):
                continue
            # a number word that is not the total may be counting a legitimate
            # SUBSET ("the other five", "four tiers that have an MMLU number").
            # Only flag the exact word that WAS the total before a tier landed,
            # i.e. a stale count, never an unfamiliar one.
            if word == WORD.get(total) or word == str(total):
                claims += 1
                continue
            if word in (WORD.get(total - 1), str(total - 1)) and re.search(r'\bother\b', ctx, re.I):
                continue                     # "the other six" — a subset, not the total
            # BOTH names required. An earlier version matched 'weights' too, which
            # is common enough that it swallowed real stale counts — the control
            # then failed on the vacuity guard instead of naming them, i.e. the
            # exclusion ate the signal it was meant to sit beside.
            if word in (WORD.get(total - 1), str(total - 1)) and (
                    re.search(r'Apache', ctx, re.I) and re.search(r'Gemma', ctx, re.I)):
                continue                     # "six tiers on Apache 2.0 ... one on Gemma"
                                             # counts the LICENCE subset. Quick ships under
                                             # the Gemma Terms of Use, so total-1 is right
                                             # here and stays right when a tier is added —
                                             # provided the new tier is Apache too.
            if word in (WORD.get(total - 1), WORD.get(total + 1), str(total - 1), str(total + 1)):
                claims += 1
                bad.append(f"{rel}: says '{word} tiers' but {total} ship. …{ctx.strip()[:110]}")

        # hyphenated and noun-dropped forms, same rules
        for pat, label in ((HYPHEN_SHAPE, "-tier"), (BARE_SHAPE, "bare count")):
            for m in pat.finditer(txt):
                if any(a <= m.start() < b for a, b in consumed):
                    continue
                word = m.group(1).lower()
                if word not in WORD.values() and not word.isdigit():
                    continue
                ctx = txt[max(0, m.start() - 130): m.start() + 130]
                if not OURS.search(ctx):
                    continue
                if label == "bare count" and not re.search(r'tier', ctx, re.I):
                    continue          # "all seven" about something else entirely
                if word == WORD.get(total) or word == str(total):
                    claims += 1
                    continue
                if word in (WORD.get(total - 1), str(total - 1)) and re.search(r'\bother\b', ctx, re.I):
                    continue
                if word in (WORD.get(total - 1), str(total - 1)) and (
                        re.search(r'Apache', ctx, re.I) and re.search(r'Gemma', ctx, re.I)):
                    continue
                if word in (WORD.get(total - 1), WORD.get(total + 1), str(total - 1), str(total + 1)):
                    claims += 1
                    bad.append(f"{rel}: '{word}' ({label}) but {total} ship. …{ctx.strip()[:110]}")

    if pages < MIN_PAGES:
        print(f"FAIL: only {pages} pages scanned, expected >= {MIN_PAGES}.")
        return 1
    if claims < MIN_CLAIMS:
        print(f"FAIL: only {claims} tier-count claims matched, expected >= {MIN_CLAIMS}.")
        print("      The site states the count constantly; a low match means the")
        print("      scan broke, not that the prose stopped counting.")
        return 1

    print(f"shipping tiers: {total} ({', '.join(shipping)})")
    if pending:
        print(f"held back until a build ships: {', '.join(pending)} "
              f"— not counted, by design")
    print(f"pages scanned: {pages} | tier-count claims checked: {claims}")

    if bad:
        print(f"\nFAIL ({len(bad)}): prose disagrees with what ships:")
        for b in bad[:25]:
            print(f"  {b}")
        if len(bad) > 25:
            print(f"  ... and {len(bad) - 25} more")
        print("\n  Each phrase counts a DIFFERENT set. Do not global-replace:")
        print("    'seven tiers' / 'all seven'  -> every shipping tier")
        print("    'the other six'              -> all except Plus")
        print("    'six tiers ... Apache'       -> Apache-licensed only (Quick is Gemma)")
        return 1

    print("\nPASS — every stated tier count matches what actually ships.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "."))
