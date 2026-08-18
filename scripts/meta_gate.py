#!/usr/bin/env python3
"""Every gate must be unable to report a false clean. This checks that, by running them.

WHY THIS EXISTS. The single largest error class in this repo's session review was
twelve instances of one mistake:
*inspecting an artefact that was not the one a conclusion was drawn about*. The
corollary is that **a clean result is only as wide as the thing you pointed at** —
a check narrowed to part of a problem reports clean about that part forever.

Four separate checks in this repo shipped a green that meant nothing:
  - seo_lint filtered to index.html hid 245 findings
  - no_internal_docs_gate examined 4 extensions while 11 servable files sat unread
  - internal_link_gate read href only, missing every src asset and absolute self-URL
  - a price sweep returned empty because macOS has no `timeout`, so it never ran

Writing that down did not prevent it; three of the four were found after it was
documented. So this is executable instead: a gate that cannot fail on an empty
input is rejected in CI, whether or not its author ever read the audit.

HOW, and the subtlety that is the whole point. Pointing a gate at an empty tree
only proves something if the gate LOOKS at the tree you pointed it at. When this
file was first written, deploy_freshness_gate "passed" the empty-tree probe — not
because it lacks a guard (it has MIN_FILES = 3) but because it ignores argv[1]
and re-checked the real repo. The probe was vacuous for exactly the reason the
probe exists to catch. So reachability is checked FIRST, and a gate that cannot be
pointed anywhere must be exempted explicitly, with a reason, never skipped in
silence.

    python3 scripts/meta_gate.py
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

#: Gates that legitimately cannot take a root, with the reason and the guard that
#: substitutes for this check. Anything here is asserted, not trusted.
EXEMPT = {
    "deploy_freshness_gate.py": (
        "compares SERVED bytes against git HEAD, so it has no filesystem root to "
        "point at; it carries MIN_FILES and fails on a short compare instead",
        "MIN_FILES",
    ),
}

#: If the scan finds fewer than this, assume it broke rather than that the gates left.
MIN_GATES = 8


def run(script: Path, root: str) -> int:
    try:
        return subprocess.run([sys.executable, str(script), root],
                              capture_output=True, text=True, timeout=180).returncode
    except subprocess.TimeoutExpired:
        return -1


def main(repo: str = ".") -> int:
    root = Path(repo)
    gates = sorted((root / "scripts").glob("*_gate.py"))
    gates = [g for g in gates if g.name != "meta_gate.py"]
    print(f"gates found: {len(gates)}")
    if len(gates) < MIN_GATES:
        print(f"\nFAIL: only {len(gates)} gates found, expected >= {MIN_GATES}.")
        print("      The scan is likelier broken than the repo. Not reporting clean.")
        return 1

    fails: list[str] = []
    with tempfile.TemporaryDirectory() as empty:
        for g in gates:
            src = g.read_text(encoding="utf-8", errors="ignore")
            reachable = "argv[1]" in src

            if g.name in EXEMPT:
                reason, needle = EXEMPT[g.name]
                if needle not in src:
                    fails.append(f"{g.name}: exempt on the grounds of {needle}, which is NOT in the file")
                else:
                    print(f"  [exempt] {g.name:<26} {reason}")
                continue

            if not reachable:
                fails.append(
                    f"{g.name}: ignores argv[1], so it cannot be pointed at a test tree. "
                    f"An empty-input probe against it proves nothing — take a root, or add "
                    f"an entry to EXEMPT explaining why it cannot.")
                continue

            rc = run(g, empty)
            if rc == 0:
                fails.append(
                    f"{g.name}: EXITS 0 ON AN EMPTY TREE. It reports clean having examined "
                    f"nothing. Add a minimum-scope guard that fails when the scan finds "
                    f"less than it should.")
            else:
                print(f"  [ok]     {g.name:<26} fails correctly on an empty tree (exit {rc})")

    if fails:
        print(f"\nFAIL ({len(fails)}):")
        for f in fails:
            print(f"  {f}")
        return 1
    print(f"\nPASS — all {len(gates)} gates refuse to report clean on nothing.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "."))
