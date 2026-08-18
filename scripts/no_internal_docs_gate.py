#!/usr/bin/env python3
"""Operational notes must not be servable from this domain.

This repository IS the website: every tracked file is published at the site root.
That includes files committed purely as internal working notes, which is easy to
do without noticing, because reviewing a commit asks "is this change correct"
and never "should this file be public".

It has happened here. Internal working notes were committed to the repo root and
were readable over HTTP until they were removed. They are gone; this stops the
next one.

WHY IT MATCHES CONTENT RATHER THAN FILENAMES. A denylist of names only catches
the file that already leaked; the next one is called something else. This looks
for the vocabulary of internal process — task-routing chatter, internal tool
paths, commit-trailer actors, hand-off instructions. A file is internal because
of what it says, not what it is called, so renaming is not a way past it.

SCOPE IS EVERY SERVABLE FILE, NOT JUST PROSE. An earlier version checked only
.md/.txt/.json/.yml and reported clean while the .py files beside it were served
too. Static hosting does not care about file extensions; if it is tracked, it is
readable. Code files are checked for the same reason.

THIS FILE IS ITS OWN EXCEPTION, and that is not a loophole: a detector has to
contain the patterns it detects. It is listed in ALLOWED explicitly so the
exemption is a visible decision rather than an accident.

    python3 scripts/no_internal_docs_gate.py
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

#: Phrases that only appear in inter-session coordination, never in marketing copy.
MARKERS = [
    r"\bstand down\b", r"\bCEO session\b", r"\bsocket session\b",
    # NOT a generic outlier-\w+ pattern: that matched "outlier-vs" (a real dataset
    # path) and "Outlier-Ai" (the HuggingFace org) on the first run. A gate that
    # cries wolf gets switched off, so session ids are listed explicitly.
    r"\boutlier-(?:fa|41|b8|c5|4b)\b", r"^X-Actor:", r"\bListAgents\b",
    r"\bmisrout", r"\bScheduleWakeup\b", r"\bStop hook\b", r"~/ops/",
    r"\bClaude session\b", r"\bthis repo belongs to\b",
]
#: Extensions Pages will serve as plain text alongside the site.
TEXTY = (".md", ".txt", ".json", ".yml", ".yaml", ".py")
#: Legitimately public, checked anyway — listed so an exemption is a decision.
ALLOWED = {"README.md", "NOTICES.txt", "llms.txt", "robots.txt",
           # a detector must contain the patterns it detects
           "scripts/no_internal_docs_gate.py"}

MIN_FILES = 5


def tracked(root: Path) -> list[str]:
    out = subprocess.run(["git", "ls-files"], cwd=root, capture_output=True, text=True)
    return [f for f in out.stdout.splitlines() if f]


def main(root_arg: str = ".") -> int:
    root = Path(root_arg)
    rx = re.compile("|".join(MARKERS), re.I | re.M)

    # Vacuity control: the detector must flag a known-bad sample every run.
    if not rx.search("If you are outlier-fa: STAND DOWN"):
        print("FAIL: detector does not flag known internal text. Instrument broken.")
        return 1

    files = [f for f in tracked(root)
             if f.lower().endswith(TEXTY)]
    print(f"tracked servable text files: {len(files)}")
    if len(files) < MIN_FILES:
        print(f"\nFAIL: only {len(files)} found, expected >= {MIN_FILES}. Scan likely broken.")
        return 1

    bad = []
    for f in files:
        try:
            text = (root / f).read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        hits = sorted({m.group(0).strip() for m in rx.finditer(text)})
        status = "ok " if not hits else ("allow" if f in ALLOWED else "FAIL")
        if hits and f not in ALLOWED:
            bad.append((f, hits))
        if hits:
            print(f"  [{status}] {f}: {', '.join(hits[:4])}")

    if bad:
        print(f"\nFAIL: {len(bad)} tracked file(s) carry internal coordination text and "
              f"would be served from the public site:")
        for f, hits in bad:
            print(f"  {f}  ->  {', '.join(hits[:5])}")
        print("\n  This repo IS the website: every tracked file is published. Move it to")
        print("  ~/ops or the parent repo, or delete it. Do not solve it by renaming.")
        return 1

    print(f"\nPASS — no internal coordination text in {len(files)} servable files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "."))
