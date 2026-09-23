#!/usr/bin/env python3
"""Move the site to a new app version: pointers AND the app-catalog snapshot.

    python3 scripts/bump_site_version.py 1.11.840 [--check]

WHY BOTH IN ONE COMMAND. tier_catalog_sync_gate compares models.csv to the app's
tier list, and in CI it can only do that through seo/_data/app_tiers.json, whose
`cut_from_version` must equal the version the site advertises. Those two facts
are set in different files, so doing them as two steps means one can be
forgotten — and the forgetting is silent until CI fails. Done together they
cannot diverge.

⚠️ POINTER SHAPES ONLY, NEVER THE BARE VERSION STRING. index.html's provenance
paragraph NARRATES the release history: "1.11.838 then fixed a step that looked
like it had worked" is correct history that a blind replace would falsify. Same
reason the app's own version bump leaves prose mentions alone. The counts below
are asserted before anything is written, and a mismatch refuses outright —
a shape that has changed shape is exactly where a blind replace does damage.

⚠️ TWO EDITS ARE LEFT TO A HUMAN ON PURPOSE, and this script names them rather
than attempting them: the sentence saying which build the page links, and the
new history sentence. Both are judgement about prose, not substitution.
"""
from __future__ import annotations

import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]

#: published path -> how many bare "old version" mentions may legitimately remain
#: (index.html keeps its history sentences; the others must reach zero).
FILES = {"index.html": 2,
         "thank-you.html": 0,
         "learn/can-you-run-claude-locally/index.html": 0}


def shapes(old: str, new: str) -> dict[str, str]:
    return {
        f'"softwareVersion": "{old}"': f'"softwareVersion": "{new}"',
        f'<span class="nav-ver">v{old}</span>': f'<span class="nav-ver">v{new}</span>',
        f"releases/download/v{old}/Outlier-{old}-arm64.dmg":
            f"releases/download/v{new}/Outlier-{new}-arm64.dmg",
        f"v{old} · notarized": f"v{new} · notarized",
    }


def sweep_download_urls(new: str, skip: set[pathlib.Path], check: bool) -> tuple[int, list]:
    """Re-point EVERY Download button on the site to `new`, using the gate's own
    finder (download_version_gate.DL_RE / scan), so the two can never disagree
    about what a download URL is.

    Why: FILES above names three pages, while the gate reads all of them. On
    2026-09-23 five hand-made /seo/ pages were still linking v1.11.827 — twenty-five
    versions stale — because no bump had ever been told they existed, and the
    /seo/ freeze had been hiding them. Only the DMG pointer (tag + filename) is
    rewritten; prose version mentions are left alone, as everywhere else here.
    -> (pages changed, [(path, new_text)]) — nothing is written here."""
    sys.path.insert(0, str(ROOT / "scripts"))
    import download_version_gate as _gate  # one definition of "a download URL"
    repl = f"releases/download/v{new}/Outlier-{new}-arm64.dmg"
    planned = []
    for p in sorted({h[0] for h in _gate.scan(ROOT)}):
        p = p if p.is_absolute() else ROOT / p
        if p in skip:
            continue
        s = p.read_text(encoding="utf-8")
        t = _gate.DL_RE.sub(repl, s)
        if t != s:
            n = len(_gate.DL_RE.findall(s)) - s.count(repl)
            print(f"  {p.relative_to(ROOT)}: {n} download URL(s) -> v{new}")
            planned.append((p, t))
    return len(planned), planned


def current_version() -> str | None:
    m = re.search(r'"softwareVersion":\s*"([\d.]+)"',
                  (ROOT / "index.html").read_text(encoding="utf-8", errors="replace"))
    return m.group(1) if m else None


def main(argv: list[str]) -> int:
    if not argv or argv[0].startswith("-"):
        print(__doc__)
        return 2
    new = argv[0]
    check = "--check" in argv
    if not re.fullmatch(r"\d+\.\d+\.\d+", new):
        print(f"FAIL: {new!r} is not a version.")
        return 1
    if "--sweep-only" in argv:
        # Repair drift without a version bump: every Download button -> `new`.
        n, planned = sweep_download_urls(new, set(), check)
        if not check:
            for p, s in planned:
                p.write_text(s, encoding="utf-8")
        print(f"  --sweep-only: {n} page(s) {'would change' if check else 'written'}.")
        return 0
    old = current_version()
    if not old:
        print("FAIL: cannot read the version the site currently advertises.")
        return 1
    if old == new:
        print(f"FAIL: the site already advertises {new}; nothing to bump.")
        return 1

    rc = 0
    planned: list[tuple[pathlib.Path, str]] = []
    for name, allowed in FILES.items():
        p = ROOT / name
        s = p.read_text(encoding="utf-8")
        before = s.count(old)
        for a, b in shapes(old, new).items():
            s = s.replace(a, b)
        left = s.count(old)
        ok = left == allowed
        print(f"  {name}: {before} -> {left} (expected {allowed}) {'OK' if ok else 'MISMATCH'}")
        if not ok:
            rc = 1
        planned.append((p, s))
    if rc:
        print("  REFUSING to write: a count did not match, so a pointer shape has "
              "changed shape. Fix the shape list rather than forcing it through.")
        return 1

    # Every OTHER page's Download button, found the way the gate finds them.
    _n, _swept = sweep_download_urls(new, {p for p, _ in planned}, check)
    planned.extend(_swept)

    if check:
        print("  --check: nothing written.")
        return 0

    for p, s in planned:
        p.write_text(s, encoding="utf-8")

    # The snapshot must carry the SAME version, or the gate refuses — which is
    # the whole point of doing these together.
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "refresh_app_tiers.py")],
                       capture_output=True, text=True)
    sys.stdout.write("  " + (r.stdout.strip() or r.stderr.strip()) + "\n")
    if r.returncode != 0:
        print("  ⚠️ POINTERS ARE WRITTEN BUT THE SNAPSHOT IS NOT. The gate will "
              "refuse until it is — that refusal is the guard working. Re-run "
              "scripts/refresh_app_tiers.py with the app reachable.")
        return 1

    print(f"\n  written. Two prose edits remain, deliberately not automated:")
    print(f"    1. the sentence saying which build the page links -> {new}")
    print(f"    2. append the {new} history sentence, LEAVING the {old} one intact")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
