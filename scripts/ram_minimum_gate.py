#!/usr/bin/env python3
"""Every RAM minimum stated for a tier must match models.csv.

Why this exists
---------------
Ten how-to pages carried "6 GB for Nano, 12 GB for Lite, 24 GB for Core / Code /
Vision, 32 GB for Plus". Plus needs 64. models.csv said 64, the home page tier
table said 64, and four comparison pages said 64 — ten pages said 32, for months.

This is the expensive kind of wrong. A reader with a 32 GB Mac follows a how-to,
buys Pro at $249, downloads 209 GB of weights and finds the tier will not load.
Unlike a marketing figure being slightly off, a hardware minimum is acted on
before the customer can discover it is false.

It is also the shape this repo keeps producing: one source of truth, many
restatements, and a sweep that fixes the ones you happened to grep for. The Plus
decode figure was the same story at 43 pages.

What is checked
---------------
Two phrasings, both anchored on a tier name so a number is never read out of
context:

    "<N> GB for <Tier>"              possibly listing several tiers per number,
                                     e.g. "24 GB for Core / Code / Vision"
    "<Tier> ... needs <N> GB"

Disk sizes are deliberately NOT checked here. "15.61 GB" next to Quick is its
download size, not its RAM floor, and conflating the two would produce exactly
the false positives that get a gate ignored.
"""
import csv
import html
import re
import sys
from pathlib import Path

MIN_PAGES = 120
MIN_CLAIMS = 10

# page label -> models.csv tier_id
ALIASES = {
    "nano": "nano", "lite": "lite", "quick": "quick",
    "core": "compact", "code": "code",
    "vision 3.8": "vision38", "vision3.8": "vision38",
    "vision": "vision", "plus": "plus",
}
# longest first so "Vision 3.8" is matched before "Vision".
#
# TWO PATTERNS, and the difference matters. The "N GB for X" shape is unambiguous
# enough to match case-insensitively. The "X ... needs N GB" shape is not: "a whole
# file plus its imports ... It needs 24 GB" is the English conjunction, and reading
# it as the Plus tier turns a correct sentence into a 40 GB error. So that shape
# matches the PROPER-NOUN spellings only.
#
# Building the case-sensitive pattern from these ALIAS KEYS would match lowercase
# and nothing else — the keys are lowercase — which is the inverted version of this
# same bug, and it is what the first attempt actually did.
LABELS = sorted(ALIASES, key=len, reverse=True)
LABEL_RE = "|".join(re.escape(x) for x in LABELS)
PROPER = {"Nano", "Lite", "Quick", "Core", "Code", "Vision 3.8", "Vision", "Plus"}
PROPER_RE = "|".join(re.escape(x) for x in sorted(PROPER, key=len, reverse=True))


def load_floors(root: Path):
    p = root / "seo" / "_data" / "models.csv"
    if not p.is_file():
        return None
    out = {}
    for r in csv.DictReader(p.open()):
        tid = (r.get("tier_id") or "").strip()
        ram = (r.get("min_ram_gb") or "").strip()
        if tid and ram:
            try:
                out[tid] = float(ram)
            except ValueError:
                pass
    return out


def main(root_arg: str = ".") -> int:
    root = Path(root_arg)
    floors = load_floors(root)
    if not floors:
        print("FAIL: could not read min_ram_gb from models.csv.")
        return 1
    if len(floors) < 5:
        print(f"FAIL: only {len(floors)} tiers have a RAM floor; the scan is likelier broken.")
        return 1

    # "24 GB for Core / Code / Vision 3.8"  -- one number, several tiers
    FOR_RE = re.compile(
        rf"(\d+(?:\.\d+)?)\s*GB\s+for\s+((?:{LABEL_RE})(?:\s*/\s*(?:{LABEL_RE}))*)", re.I)
    # "Plus 397B needs 64 GB", "Vision needs 24 GB of unified memory".
    #
    # ATTRIBUTION IS BY THE NEAREST LABEL BEFORE "needs", NOT THE FIRST ONE IN
    # RANGE. The first version of this searched forward from any tier name within
    # 40 characters and produced five false positives on sentences like
    #   "Core 27B and Code 27B want 24 GB+; Plus 397B needs 64 GB+"
    #   "Nano runs on any Apple Silicon Mac and Lite needs 12 GB"
    # where the subject of "needs" is the LAST tier named, not the first. Proximity
    # is not attribution — the exact mistake this gate exists to catch, made inside
    # the gate itself.
    # Tier names are proper nouns, so this match is CASE-SENSITIVE. "a whole file
    # plus its imports ... It needs 24 GB" is the English conjunction, and a
    # case-insensitive match read it as the Plus tier and reported a real sentence
    # as a 40 GB error.
    NEEDS_RE = re.compile(r"\bneeds?\s+(\d+(?:\.\d+)?)\s*GB")
    LAST_LABEL_RE = re.compile(rf"\b({PROPER_RE})\b(?!.*\b(?:{PROPER_RE})\b)")
    ALL_LABELS_RE = re.compile(rf"\b({PROPER_RE})\b")
    # "need 6GB and 12GB" pairs each number with a different tier; a single-subject
    # rule cannot split it, so it is skipped rather than guessed at.
    PAIRED_RE = re.compile(r"^\s*(?:and|or|,)\s*\d+(?:\.\d+)?\s*GB", re.I)

    bad, pages, claims = [], 0, 0
    for f in sorted(root.rglob("*.html")):
        rel = f.relative_to(root).as_posix()
        if "_seo_build" in rel:
            continue
        pages += 1
        raw = f.read_text(errors="replace")
        txt = html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", raw)))

        for m in FOR_RE.finditer(txt):
            gb = float(m.group(1))
            for label in re.split(r"\s*/\s*", m.group(2)):
                tid = ALIASES.get(label.strip().lower())
                if not tid or tid not in floors:
                    continue
                claims += 1
                if abs(gb - floors[tid]) > 0.01:
                    bad.append(f"{rel}: '{gb:g} GB for {label.strip()}' — models.csv says "
                               f"{floors[tid]:g} GB")
        for m in NEEDS_RE.finditer(txt):
            before = txt[max(0, m.start() - 60): m.start()]
            # ATTRIBUTION CANNOT CROSS A SENTENCE BOUNDARY. "…with Nano and Lite.
            # For coding-grade models, plan on 32 GB. Do I really need 64 GB for a
            # 397B model?" — the subject is Plus, two sentences later, and a raw
            # 60-character lookback claimed it for Lite. Trim to the current
            # sentence before looking for a subject at all.
            # A sentence end is punctuation FOLLOWED BY SPACE. Using a bare "." cut
            # the lookback at the decimal point in "15.13 GB" and threw away the
            # subject, so a genuinely wrong figure stopped being reported — the
            # control caught it going quiet, which is the only reason I noticed.
            _ends = [mm.end() for mm in re.finditer(r"[.?!]\s", before)]
            if _ends:
                before = before[_ends[-1]:]
            # NEAREST label wins. Requiring exactly one was too strict: in
            # "Vision 35B-a3b, and Plus 397B-a17b, which needs 64 GB" the relative
            # pronoun binds to the nearest noun, and demanding a single candidate
            # made the gate silently skip a sentence it should judge. Genuine lists
            # ("Nano and Lite tiers need 6GB and 12GB") are caught by PAIRED_RE
            # below, which is the condition that actually distinguishes them.
            if not ALL_LABELS_RE.search(before):
                continue
            if PAIRED_RE.match(txt[m.end(): m.end() + 24]):
                continue
            lab = LAST_LABEL_RE.search(before)
            if not lab:
                continue
            tid = ALIASES.get(lab.group(1).strip().lower())
            if not tid or tid not in floors:
                continue
            gb = float(m.group(1))
            claims += 1
            if abs(gb - floors[tid]) > 0.01:
                bad.append(f"{rel}: '{lab.group(1)} … needs {gb:g} GB' — models.csv "
                           f"says {floors[tid]:g} GB")

    if pages < MIN_PAGES:
        print(f"FAIL: only {pages} pages scanned, expected >= {MIN_PAGES}.")
        return 1
    if claims < MIN_CLAIMS:
        print(f"FAIL: only {claims} RAM claims matched, expected >= {MIN_CLAIMS}. "
              f"This site states hardware floors constantly; a low count means the "
              f"scan broke, not that the pages stopped saying it.")
        return 1

    print(f"pages scanned: {pages} | RAM claims checked: {claims}")
    if bad:
        print(f"\nFAIL ({len(bad)}): a stated RAM floor disagrees with models.csv:")
        for b in bad[:25]:
            print(f"  {b}")
        if len(bad) > 25:
            print(f"  ... and {len(bad) - 25} more")
        print("\n  A hardware minimum is acted on before it can be disproved — a reader")
        print("  buys, downloads 209 GB, and only then finds the tier will not load.")
        return 1
    print("\nPASS — every stated RAM floor matches models.csv.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "."))
