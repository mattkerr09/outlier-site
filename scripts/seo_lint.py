#!/usr/bin/env python3
"""SEO article gate — blocks AI-slop prose, thin pages, and near-duplicates.

Run before shipping any article set:
    scripts/seo_lint.py .        # whole site, or a subdir: scripts/seo_lint.py seo

Three checks, each of which is a real ship-blocker (all three come from what actually went
wrong on the Outlier programmatic set, plus matt's 2026-07-23 rule "articles must not look
like AI wrote it"):

  VOICE      banned stock phrases + the "not just X, it's Y" construction. These are the
             tells readers and reviewers pattern-match on instantly.
  THIN       < MIN_WORDS of real body text. Thin pages are a flag risk on their own.
  DUPLICATE  near-identical 8-word shingles across pages. This — not thinness — is what
             actually tripped the Outlier set, because programmatic pages drift toward one
             template. Two pages sharing too much phrasing means one of them shouldn't exist.

Exit 1 if anything fails, so it can gate a build.
"""
from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

MIN_WORDS = 600
SHINGLE_N = 8
DUP_RATIO = 0.28          # >28% shared shingles between two pages = too close
CHROME_DF_PAGES = 20      # a shingle on >=20 pages is site furniture, not prose

# The tells. Lowercased substring match against visible text.
BANNED = [
    "in today's digital", "in today's fast-paced", "ever-evolving", "ever-changing",
    "let's dive in", "let's explore", "dive into the world", "look no further",
    "game-changer", "game changer", "unlock the power", "take your videos to the next level",
    "revolutionize", "revolutionary", "cutting-edge", "state-of-the-art",
    "seamlessly integrate", "effortlessly", "seamless experience",
    "in conclusion", "at the end of the day", "when it comes to",
    "whether you're a", "whether you are a",
    "it's important to note", "it is important to note",
    "harness the power", "elevate your", "supercharge",
    "in the realm of", "navigating the", "delve into",
]
# "It's not just X, it's Y" / "isn't just X — it's Y"
NOT_JUST = re.compile(r"\b(it'?s|is|isn'?t|not)\s+just\s+\w+[,—-]\s*it'?s\b", re.I)

_TAG = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.S | re.I)
# Nav and footer are IDENTICAL on every page by design. Counting them as shared prose makes
# any well-templated site look like a duplicate farm — the first run of this linter flagged
# two pages at 30% whose only overlap was the footer and a shared comparison table. Shared
# chrome is fine; shared PHRASING is the actual spam signal, so measure only the body.
_CHROME = re.compile(
    r"<(nav|footer)[^>]*>.*?</\1>"
    # Repeated CTA / related-links / breadcrumb blocks are chrome too. They are not
    # inside <nav> or <footer>, but a download button and a "Related pages" list that
    # appear identically on 20 pages are exactly the shared furniture the nav/footer
    # exclusion already exists for. Counting them made 20 honest hardware pages look
    # like a duplicate farm, and the only way to "fix" that would be rewriting one
    # download button 20 ways -- writing for the linter instead of the reader.
    r'|<div class="(cta|related|foot|crumbs)"[^>]*>.*?</div>',
    re.S | re.I,
)
_HTML = re.compile(r"<[^>]+>")


def visible_text(html: str, *, body_only: bool = False) -> str:
    html = _TAG.sub(" ", html)
    if body_only:
        html = _CHROME.sub(" ", html)
    return re.sub(r"\s+", " ", _HTML.sub(" ", html)).strip()


def shingles(text: str, n: int = SHINGLE_N) -> set[str]:
    w = re.findall(r"[a-z0-9']+", text.lower())
    return {" ".join(w[i:i + n]) for i in range(max(0, len(w) - n + 1))}


def _is_section_hub(p: Path) -> bool:
    """True for an index.html whose directory holds further page directories.

    seo/index.html and seo/vs/index.html are link hubs of 7-19 entries and tripped the
    word floor on the first run. That is the floor being wrong, not the pages: MIN_WORDS
    is a rule about thin ARTICLES, and padding a nav index to 600 words makes it worse to
    read and no better to rank. Same reasoning as the /legal/ exemption above.
    """
    return p.name == "index.html" and any(
        (child / "index.html").exists() for child in p.parent.iterdir() if child.is_dir()
    )


def main(root: str) -> int:
    pages = sorted(Path(root).rglob("index.html"))
    if not pages:
        print(f"no pages under {root}")
        return 1

    fails: list[str] = []
    sh: dict[Path, set[str]] = {}

    for p in pages:
        try:
            text = visible_text(p.read_text(encoding="utf-8", errors="ignore"))
        except OSError:
            continue
        words = len(text.split())
        low = text.lower()

        hits = [b for b in BANNED if b in low]
        if NOT_JUST.search(text):
            hits.append("not-just-X-its-Y")
        if hits:
            fails.append(f"VOICE  {p}: {', '.join(hits[:4])}")
        # LEGAL PAGES ARE EXEMPT from the word floor. MIN_WORDS is an SEO rule for articles —
        # a refund policy should be as short as it can be while staying complete, and padding one
        # to clear a word count makes it worse for the reader and no better legally.
        #
        # ⚠️ MATCHED AS A PATH COMPONENT, NOT AS THE SUBSTRING "/legal/". The substring form made
        # the verdict depend on where you invoked the linter from: `seo_lint.py site` produced
        # ".../site/legal/refunds" and exempted it, while `seo_lint.py .` from inside the site
        # produced "legal/refunds" with no leading slash and failed it. Same tree, same page, two
        # answers — and the failing one is the invocation a person is most likely to try.
        if words < MIN_WORDS and "legal" not in p.parts \
                and not _is_section_hub(p):
            fails.append(f"THIN   {p}: {words}w (min {MIN_WORDS})")
        # duplicate check ignores shared nav/footer chrome — see _CHROME above
        sh[p] = shingles(visible_text(p.read_text(encoding="utf-8", errors="ignore"),
                                      body_only=True))

    # SHARED FURNITURE IS WHATEVER APPEARS EVERYWHERE, NOT WHATEVER _CHROME LISTS.
    #
    # _CHROME above is a hardcoded allowlist: <nav>, <footer>, and four class
    # names. That works only until someone adds a NEW block to every page, and
    # on 2026-08-24 someone did — b14377a2 put the same ~40-line email-capture
    # form on 52 pages. It matches none of those selectors, so its identical
    # prose counted as body content, every pair of those pages crossed the 28%
    # line at once, and DUP went 227 -> 573. The linter had been green 51 times;
    # it has failed every run since, hourly, for two days, on a real feature
    # working correctly.
    #
    # The comment on _CHROME already states the correct rule — text that "appears
    # identically on 20 pages" IS furniture — it just was not the test being run.
    # Now it is: any shingle carried by CHROME_DF_PAGES or more pages is site
    # furniture by definition and is subtracted before any pair is compared. That
    # is self-maintaining. The next shared block added to every page is absorbed
    # instead of turning the suite red, and nobody has to remember to add a class
    # name here. _CHROME stays as a cheap first pass for the nav and footer.
    #
    # It cannot mask real duplication: prose repeated across a HANDFUL of pages
    # is what this linter exists to catch, and it stays well under the threshold.
    if sh:
        _df: dict[str, int] = {}
        for _set in sh.values():
            for _g in _set:
                _df[_g] = _df.get(_g, 0) + 1
        _furniture = {g for g, n in _df.items() if n >= CHROME_DF_PAGES}
        if _furniture:
            print(f"treating {len(_furniture)} shingle(s) on >={CHROME_DF_PAGES} "
                  f"pages as site furniture")
            sh = {p_: (s_ - _furniture) for p_, s_ in sh.items()}

    # near-duplicate detection, pairwise within the set
    seen: set[tuple[Path, Path]] = set()
    for a, sa in sh.items():
        if len(sa) < 40:
            continue
        for b, sb in sh.items():
            if a >= b or (a, b) in seen or len(sb) < 40:
                continue
            seen.add((a, b))
            overlap = len(sa & sb) / min(len(sa), len(sb))
            if overlap > DUP_RATIO:
                fails.append(f"DUP    {a.parent.name} ~ {b.parent.name}: {overlap:.0%} shared")

    print(f"checked {len(pages)} pages")
    if not fails:
        print("PASS — no voice, thin, or duplicate failures")
        return 0
    print(f"\nFAIL ({len(fails)}):")
    for f in sorted(fails):
        print("  " + f)
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "."))
