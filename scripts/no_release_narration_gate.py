#!/usr/bin/env python3
"""The homepage must not narrate the release history.

WHY THIS EXISTS. The benchmark footnote on the pricing section ("How these were
run") was a short method note. On 2026-08-25 the page began linking a newer build
than the one benchmarked, and a sentence was added saying so. From 2026-09-09 every
release appended another: bump_site_version.py itself ended each bump with "append
the <new> history sentence, LEAVING the <old> one intact". By 1.11.857 the footnote
was 20,173 characters, 57 sentences narrating 28 releases' internals ("1.11.825 then
stopped the agent damaging a file it edited: ... return a - b</args></tool> on
disk") in monospace on the pricing section. It was removed on 2026-09-24, and the
bump script no longer asks for it.

This gate keeps it removed. It fails if the homepage carries per-release narration
(the "1.11.823 then allowed ..." signature, or the "The page now links" /
"Between the benchmark build" openers), or if any benchmark-provenance paragraph
grows past a size no method note needs. What changed in a release belongs in its
GitHub release notes, not on a marketing page.

    python3 scripts/no_release_narration_gate.py [root]
    python3 scripts/no_release_narration_gate.py --self-check
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

PAGE = "index.html"
#: A method note (sample, grading, hardware, intervals) fits comfortably in this.
#: The legitimate footnote is ~2,100 characters; three narrated releases exceed it.
PROVENANCE_CAP = 3000

NARRATION = [
    (re.compile(r"\b\d+\.\d+\.\d+ then\b"), 'per-release narration ("<version> then ...")'),
    (re.compile(r"The page now links"), '"The page now links" opener'),
    (re.compile(r"Between the benchmark build"), '"Between the benchmark build" opener'),
]
PROVENANCE_P = re.compile(r'<p class="provenance[^"]*">(.*?)</p>', re.S)


def problems(html: str) -> list[str]:
    out = []
    for rx, what in NARRATION:
        for m in rx.finditer(html):
            line = html.count("\n", 0, m.start()) + 1
            out.append(f"{PAGE}:{line}: {what}: {html[m.start():m.start() + 60]!r}")
    for m in PROVENANCE_P.finditer(html):
        n = len(m.group(0))
        if n > PROVENANCE_CAP:
            line = html.count("\n", 0, m.start()) + 1
            out.append(f"{PAGE}:{line}: provenance paragraph is {n} chars (cap {PROVENANCE_CAP}) "
                       "- a method note does not need this; is release history creeping back?")
    return out


def check(root: Path) -> int:
    page = root / PAGE
    if not page.is_file():
        print(f"FAIL: no {PAGE} under {root} - nothing was checked, so nothing can be called clean.")
        return 1
    html = page.read_text(encoding="utf-8", errors="replace")
    if not PROVENANCE_P.search(html):
        print(f"FAIL: {PAGE} has no benchmark provenance paragraph - the gate is not looking "
              "at the page it was written for.")
        return 1
    found = problems(html)
    if found:
        print("FAIL: the homepage narrates release history (it belongs in the GitHub release notes):")
        for f in found:
            print("  " + f)
        return 1
    print(f"OK: {PAGE} carries no release narration; provenance paragraphs within {PROVENANCE_CAP} chars.")
    return 0


def self_check() -> int:
    """The gate must fail on the thing it exists to catch, and pass a clean note."""
    clean = '<p class="provenance reveal">How these were run - MMLU: n=200.</p>'
    planted = [
        clean.replace("n=200.", "n=200. 1.11.858 then fixed the updater."),
        clean.replace("n=200.", "n=200. The page now links 1.11.858."),
        '<p class="provenance reveal">' + "x" * (PROVENANCE_CAP + 1) + "</p>",
    ]
    ok = not problems(clean) and all(problems(p) for p in planted)
    print("OK: self-check - clean note passes, every planted narration fails."
          if ok else "FAIL: self-check - the gate cannot see what it exists to catch.")
    return 0 if ok else 1


if __name__ == "__main__":
    if "--self-check" in sys.argv[1:]:
        raise SystemExit(self_check())
    raise SystemExit(check(Path(sys.argv[1] if len(sys.argv) > 1 else ".")))
