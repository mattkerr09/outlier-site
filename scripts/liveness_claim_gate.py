#!/usr/bin/env python3
"""A badge that LOOKS live must be wired to something live, or not exist.

DESIGN-BRIEF.md, 2026-08-18: "A 'LIVE' badge means live. If it is not wired to
something real, remove the badge." The brief notes no gate catches it. This is
that gate.

WHAT IT ACTUALLY CAUGHT, and why the rule needed teeth. outlier.host's hero had

    <span class="live"></span>   +   animation: pulse 2.4s infinite   +   green

sitting beside "Runs entirely on your Mac · notarized by Apple". No wrong number
was printed anywhere — the defect was a CONVENTION asserting a live reading, in
three independent signals at once, with no live state on the page for it to read.
Both neighbouring facts are permanently static, so it could never have been made
true. Removal was the only fix.

THE DISTINCTION THIS ENCODES — marker versus reading:

  MARKER   a static coloured dot used as a bullet or a section mark. Decorative.
           This page has three (.pill-offline, .proof-head, .msg-note) and they
           are fine, because nothing about them claims to be sampling anything.
  READING  the same dot ANIMATED, or an element named live/online/realtime, or a
           standalone "LIVE" chip. Those are the conventions people read as
           "this is being measured right now".

Animation is the strongest single tell: a thing that pulses is a thing claiming
to be updating. So the rule is not "no green dots" — it is that anything wearing
the READING conventions must appear in ALLOWED with a written justification.

WHAT IT DELIBERATELY DOES NOT FLAG, verified against this site:
  - "SWE-bench-Live"          a benchmark NAME that contains the word
  - "Live web search"         a COMPETITOR's feature, described factually
  - "real-time web access"    same, describing Claude/Grok rather than us
A blanket search for the word would fail on all three, cry wolf, and get itself
switched off. It matches the badge SHAPE — a class, or a short standalone chip —
not the word in prose.

    python3 scripts/liveness_claim_gate.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

#: Conventions that read as "currently being measured".
CLASS_RE = re.compile(r'class="[^"]*\b(live|online|realtime|real-time|streaming)\b[^"]*"', re.I)
CHIP_RE = re.compile(r'>\s*(LIVE|ONLINE)\s*<')
#: Animation applied to a status-shaped selector. Animation is the loudest tell.
ANIM_RE = re.compile(
    r'\.(?:[a-z0-9_-]*\b(?:live|dot|pulse|status|badge|indicator|blink|beacon)[a-z0-9_-]*)\b[^{}]*\{[^{}]*animation:',
    re.I)

#: Anything here is a deliberate, justified exception. Empty is the healthy state.
ALLOWED: dict[str, str] = {}

MIN_FILES = 50


def scan(root: Path):
    hits, files = [], 0
    for p in sorted(root.rglob("*.html")):
        if ".git" in p.parts:
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        files += 1
        rel = str(p.relative_to(root))
        for m in CLASS_RE.finditer(text):
            hits.append((rel, "class", m.group(0)[:70]))
        for m in CHIP_RE.finditer(text):
            hits.append((rel, "chip", m.group(0).strip()[:70]))
        for m in ANIM_RE.finditer(text):
            hits.append((rel, "animated-status", re.sub(r"\s+", " ", m.group(0))[:70]))
    return hits, files


def main(root_arg: str = ".") -> int:
    root = Path(root_arg)
    hits, files = scan(root)

    # Vacuity control: the detector must fire on a known-bad sample every run.
    sample = '<span class="live"></span>'
    if not CLASS_RE.search(sample):
        print("FAIL: the detector does not flag a known liveness badge. Instrument broken.")
        return 1

    print(f"scanned {files} html file(s); liveness conventions found: {len(hits)}")
    if files < MIN_FILES:
        print(f"\nFAIL: only {files} files scanned, expected >= {MIN_FILES}.")
        print("      The scan is likelier broken than the site. Not reporting clean.")
        return 1

    unjustified = [h for h in hits if f"{h[0]}::{h[2]}" not in ALLOWED]
    for rel, kind, snip in hits:
        mark = "ok " if f"{rel}::{snip}" in ALLOWED else "FAIL"
        print(f"  [{mark}] {kind:<16} {rel}: {snip}")

    if unjustified:
        print(f"\nFAIL: {len(unjustified)} element(s) wear a live-status convention "
              f"with no entry in ALLOWED.")
        print("  Either wire it to something real, remove it, or add it to ALLOWED with")
        print("  a written reason. A static dot used as a marker is fine — animate it,")
        print("  or name it live/online/realtime, and it becomes a reading.")
        return 1

    print(f"\nPASS — no unjustified live-status conventions across {files} files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "."))
