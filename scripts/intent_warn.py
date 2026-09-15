#!/usr/bin/env python3
"""Warn when two live pages appear to be aimed at the SAME SEARCH, whatever their words.

WHY THIS EXISTS. seo_lint's DUP check compares 8-word shingles. That finds pages
WRITTEN alike. It cannot find pages AIMED alike, and aimed alike is what costs us:
Google picks one URL per intent and files the rest under "Crawled - currently not
indexed". On 2026-09-15, 55.6% of /run/ sat in exactly that state while seo_lint
reported those pages clean - correctly, by its own rule. The two worst offenders
shared 12% of their shingles and the whole of their purpose:

    "Claude-Code-style agents, offline on Mac"
    "Local coding agent on macOS, no API keys"

Different words. One search. So this is a second instrument, not a wider threshold
on the first one. The two are meant to disagree: the /seo/ run-* matrix trips DUP
on a shared template and is silent here, because each of those pages names a
different Mac. That disagreement is the useful part.

HOW IT READS INTENT, off <title> and <h1>:

  SHAPE    what kind of answer the reader wants - comparison, how-to,
           recommendation, explainer, troubleshooting. Different shapes are not
           competing even on one subject: "Mac mini vs Mac Studio" and "How to run
           AI on a Mac Studio" answer different questions. Must MATCH.
  TOPIC    the subject axes - privacy/locality, agents, cost, speed, memory,
           quality. Must be EQUAL, and at least two of them.
  ENTITY   the specific thing named. THIS IS THE PART THAT WAS WRONG FIRST TIME
           and the reason the file is worth reading.

THE ENTITY MISTAKE, AND THE FIX. The first version carried a hand-written list of
entities - chips, Macs, model families, rival products. It produced 1,274 warnings
on 238 pages, and twenty-five of them were pairs like

    vs/outlier-vs-grok  ~  vs/outlier-vs-tabnine

because the list had never heard of Grok or Tabnine. Both pages therefore named
"no entity", so they matched each other. A hand-written allowlist beside generated
content is the producer-and-validator failure in one file: the content grows and
the list does not, and the check degrades silently into noise.

The slug already names the entity, and its RARITY says how specific it is. "grok"
appears in one slug on this site; "ai" appears in 83. A token carried by one page
names a thing that page is about; a token carried by 83 is vocabulary. So two
pages are held apart when the tokens they DIFFER by include a rare one - no list
to maintain, and the next competitor page defends itself the day it is written.

Calibration, measured rather than chosen (238 live pages):

    hand-written entity list, topic containment, >=1 topic   1,274 pairs
    topics equal, >=2 topics                                   103
    + slug overlap >= 0.40                                      44
    + rare-token rule (a token on <=1 page is specific)           5

Hand-labelled, all five: one clear true positive (free-up-disk-space-for-ai-models
~ seo/how-to/free-up-disk-space-for-large-models, differing only by "ai"/"large"),
one borderline (the same task compared against two different rivals), three false
(cloud-coding-assistants-for-<task>, where the task IS the intent). Call it one to
two useful findings in five - poor precision, small enough to read in a minute.

RARE_MAX IS 1 ON PURPOSE. At 2 the run drops to a single pair and at 3 to none,
and what it loses first is the true positive: "large" appears on two pages, so
raising the bar by one would silence the one finding that was worth having. A
narrowing rule tuned until its output looks tidy has been tuned to say nothing.

IT IS A WARNING, NOT A GATE, and returns 0 whatever it finds. Intent is inferred
here, not declared - no page on this site states the query it was written for - so
this reads a proxy off two lines of markup and is wrong most of the time by its own
measurement above. A check that is wrong three times in five must not be able to
block a deploy. When the rate is better known it can become a gate or be deleted;
either beats guessing.

Noindex stubs are skipped (a page outside the index competes for nothing). Section
hubs are skipped (a hub is meant to restate what it links to).
"""
from __future__ import annotations

import collections
import re
import sys
from pathlib import Path

SHAPE = {
    "comparison":     r"\bvs\.?\b|\bversus\b|\bcompared\b|\bcomparison\b",
    "recommendation": r"\bbest\b|\btop \d|\bworth it\b",
    "howto":          r"\bhow to\b|\bhow do\b|\bsetup\b|\bset up\b|\binstall\b|\brunn?ing\b|\brun\b",
    "explainer":      r"\bwhy\b|\bwhat\b|\bexplained\b|\bmeans\b|\bactually\b|\bdoes\b",
    "troubleshoot":   r"\bfix\b|\bnot working\b|\berrors?\b|\bfails?\b|\bslow\b",
}
TOPIC = {
    "privacy": r"\bprivate\b|\bprivacy\b|\bno cloud\b|\bcloud\b|\boffline\b|\blocal(?:ly)?\b|"
               r"\bon-device\b|\bair-?gapped\b|\bno internet\b|\bdata\b",
    "agent":   r"\bagents?\b|\bcoding\b|\bcode\b|\bassistants?\b|\bclaude[- ]code\b|\bcopilot\b",
    "cost":    r"\bfree\b|\bprice\b|\bcost\b|\bcheap\b|\bsubscription\b|\bapi keys?\b|\bno keys?\b",
    "speed":   r"\bfast\b|\bspeed\b|\btok/s\b|\btokens? per second\b|\bslow\b",
    "memory":  r"\bram\b|\bmemory\b|\bunified\b|\bfits?\b|\bquantiz|\bdisk space\b|\bstorage\b",
    "quality": r"\baccura|\bquality\b|\bmmlu\b|\bhumaneval\b|\bbenchmark|\bbetter\b|\bsmart",
}
MIN_TOPICS = 2
SLUG_OVERLAP = 0.40
RARE_MAX = 1            # a slug token on this many pages or fewer names a specific thing
HUBS = {"run", "learn", "vs", "best", "seo", "compare", "how-to"}
STOP = {"a", "an", "the", "on", "in", "for", "to", "of", "and", "or", "with", "your",
        "you", "is", "it", "how", "what", "why", "can", "do", "does", "that", "this",
        "at", "as", "by", "from", "2026", "be", "are", "my", "we", "vs"}
NOINDEX = re.compile(r'name=["\']robots["\'][^>]*noindex', re.I)


def signals(html: str) -> tuple[str, frozenset[str], frozenset[str]]:
    t = re.search(r"<title>([^<]*)</title>", html, re.I)
    h = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.I | re.S)
    title = (t.group(1) if t else "").replace("| Outlier", "")
    text = title + " " + re.sub(r"<[^>]*>", " ", h.group(1) if h else "")
    text = re.sub(r"\s+", " ", text).lower()
    return (title.strip(),
            frozenset(k for k, rx in SHAPE.items() if re.search(rx, text)),
            frozenset(k for k, rx in TOPIC.items() if re.search(rx, text)))


def slug_tokens(p: Path) -> frozenset[str]:
    return frozenset(t for t in re.split(r"[-/]", p.parent.name) if t and t not in STOP)


def main(root: str = ".") -> int:
    base = Path(root)
    pages: dict[Path, tuple] = {}
    skipped_noindex = skipped_hubs = 0
    for p in sorted(base.rglob("index.html")):
        s = str(p)
        if ".git" in s or "_seo_build" in s or "node_modules" in s:
            continue
        html = p.read_text(encoding="utf-8", errors="ignore")
        if NOINDEX.search(html):
            skipped_noindex += 1
            continue
        if p.parent.name in HUBS or p.parent == base:
            skipped_hubs += 1
            continue
        sig = signals(html)
        if sig[0]:
            pages[p] = sig

    # THE CLASSIFIER MUST PROVE IT STILL CLASSIFIES. This is a pile of regexes over
    # two lines of markup. If any stopped matching, every page would read as
    # shapeless, no pair could ever match, and the run would print zero warnings -
    # indistinguishable from a site with no duplicate intent. So it is asked about a
    # title whose answer is known. The pair that caused this file to be written was
    # consolidated the same day, so the probe is on the CLASSIFIER, not on the site.
    probe = signals("<title>Local coding agent on macOS, no API keys</title>"
                    "<h1>How to run a local coding agent with no API keys</h1>")
    if not ({"howto"} <= probe[1] and {"agent", "privacy", "cost"} <= probe[2]):
        print(f"intent_warn: FAIL - the classifier no longer reads its own probe "
              f"(shapes={sorted(probe[1])}, topics={sorted(probe[2])}). Every result "
              f"below, a zero included, is meaningless.")
        return 1
    if not pages:
        print("intent_warn: FAIL - no live pages found; nothing was compared")
        return 1

    df: collections.Counter[str] = collections.Counter()
    for p in pages:
        df.update(slug_tokens(p))

    items = sorted(pages.items())
    # Counted per stage so a zero is never bare. Each rule here NARROWS, and a
    # narrowing rule that has quietly started excluding everything reports exactly
    # what a clean site reports.
    stage = collections.Counter()
    warns = []
    for i, (pa, (ta_title, sa, tpa)) in enumerate(items):
        for pb, (tb_title, sb, tpb) in items[i + 1:]:
            stage["pairs"] += 1
            if not sa or sa != sb:
                continue
            stage["same shape"] += 1
            if tpa != tpb or len(tpa) < MIN_TOPICS:
                continue
            stage["same topics"] += 1
            A, B = slug_tokens(pa), slug_tokens(pb)
            if not A or not B or len(A & B) / min(len(A), len(B)) < SLUG_OVERLAP:
                continue
            stage["slug overlap"] += 1
            diff = A ^ B
            rare = sorted(t for t in diff if df[t] <= RARE_MAX)
            if rare:
                continue
            stage["no rare token"] += 1
            warns.append((pa, pb, ta_title, tb_title, sorted(sa | tpa), sorted(diff)))

    print(f"intent_warn: read {len(pages)} live page(s) "
          f"({skipped_noindex} noindex, {skipped_hubs} hub(s) skipped)")
    print("intent_warn: " + " -> ".join(
        f"{stage[k]} {k}" for k in ("pairs", "same shape", "same topics",
                                    "slug overlap", "no rare token")))
    if not warns:
        print("intent_warn: no two live pages read as aimed at the same search "
              "(the funnel above shows the check was able to say otherwise)")
        return 0
    print(f"intent_warn: {len(warns)} pair(s) may be aimed at the same search. "
          f"WARNING, NOT A GATE - measured at roughly one useful finding in five, "
          f"so read them, do not obey them.")
    for pa, pb, ta, tb, why, diff in warns:
        print(f"  WARN  /{pa.parent}/  \"{ta}\"")
        print(f"        /{pb.parent}/  \"{tb}\"")
        print(f"        same {', '.join(why)}; differ only by {diff}, none rare")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "."))
