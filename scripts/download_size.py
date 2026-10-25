#!/usr/bin/env python3
"""The download's size, from the release record, in one place.

    python3 scripts/download_size.py [--check]     # re-sweep every size claim to seo/_data/release.json

WHY. Until 2026-10-24 every "290 MB" on the site was typed by hand — 190 Download
buttons, 53 requirement lines, a handful of FAQ answers — and the 1.11.960 DMG is
276,293,500 bytes. Nothing tied the figure to a release, so nothing noticed when
it stopped being true. Now:

  * seo/_data/release.json holds the advertised version and its DMG's byte count,
    written by scripts/bump_site_version.py from the GitHub release asset itself
    (fetch_release_bytes) — never typed;
  * SHAPES below is the one definition of "a current-size claim"; the bump sweeps
    every one of them to that record, and _seo_build/scripts/render.py reads the
    same record for the pages it generates;
  * scripts/download_size_gate.py fails the site if any claim disagrees with the
    record, or (--live) if the record disagrees with the published asset.

⚠️ SHAPES ONLY, NEVER A BARE "NNN MB". learn/ carries history ("312 to 288 MB")
that a blind replace would falsify — the same rule bump_site_version.py follows
for version strings.
"""
from __future__ import annotations

import json
import os
import pathlib
import re
import sys
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
RECORD = pathlib.Path("seo/_data/release.json")
REPO = "Outlier-host/outlier-app-releases"

#: Every way the site states the CURRENT download size. Group "mb" is the figure.
SHAPES = [
    re.compile(r"Download free \((?P<mb>\d{2,4}) MB\)"),
    re.compile(r"\(free update\) (?:&middot;|·) (?P<mb>\d{2,4}) MB"),
    re.compile(r"The DMG itself is about (?P<mb>\d{2,4}) MB"),
    re.compile(r"<code>\.dmg</code> \(about (?P<mb>\d{2,4}) MB\)"),
    re.compile(r"It is (?P<mb>\d{2,4}) MB and a signed"),
    re.compile(r"current download is about (?P<mb>\d{2,4}) MB"),
    re.compile(r"The installer is about (?P<mb>\d{2,4}) MB"),
    re.compile(r"Apple Silicon DMG · (?P<mb>\d{2,4}) MB"),
]

#: Where claims can live. _seo_build/output is the renderer's scratch copy, not served.
SKIP_DIRS = {".git", "node_modules", "output", "__pycache__"}


def mb(n_bytes: int) -> int:
    """Decimal megabytes, as Finder and the download dialog show them: 276,293,500 B -> 276."""
    return int(round(n_bytes / 1_000_000))


def load(root: pathlib.Path = ROOT) -> dict:
    return json.loads((root / RECORD).read_text(encoding="utf-8"))


def write(version: str, n_bytes: int, root: pathlib.Path = ROOT) -> dict:
    rec = {"version": version, "dmg_bytes": int(n_bytes), "dmg_mb": mb(n_bytes),
           "source": f"GitHub release v{version}, asset Outlier-{version}-arm64.dmg (its size, read at bump time)"}
    (root / RECORD).write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
    return rec


def fetch_release_bytes(version: str) -> int:
    """The published DMG's byte count, from GitHub's release record for the tag."""
    req = urllib.request.Request(f"https://api.github.com/repos/{REPO}/releases/tags/v{version}",
                                 headers={"Accept": "application/vnd.github+json", "User-Agent": "outlier-site-bump"})
    tok = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if tok:
        req.add_header("Authorization", f"Bearer {tok}")
    with urllib.request.urlopen(req, timeout=30) as r:
        rel = json.load(r)
    want = f"Outlier-{version}-arm64.dmg"
    for a in rel.get("assets") or []:
        if a.get("name") == want and int(a.get("size") or 0) > 0:
            return int(a["size"])
    raise SystemExit(f"download_size: release v{version} has no asset {want} with a size")


def files(root: pathlib.Path):
    for dirpath, dirnames, names in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for n in names:
            if n.endswith(".html"):
                yield pathlib.Path(dirpath) / n


def claims(root: pathlib.Path):
    """-> [(path, figure)] for every current-size claim under root."""
    out = []
    for p in files(root):
        s = p.read_text(encoding="utf-8", errors="replace")
        for rx in SHAPES:
            out += [(p, int(m.group("mb"))) for m in rx.finditer(s)]
    return out


def sweep(figure: int, root: pathlib.Path = ROOT) -> list[tuple[pathlib.Path, str]]:
    """Every claim -> `figure`. Returns [(path, new_text)]; nothing is written here."""
    planned = []
    for p in files(root):
        s = p.read_text(encoding="utf-8", errors="replace")
        t = s
        for rx in SHAPES:
            t = rx.sub(lambda m: m.group(0).replace(m.group("mb"), str(figure)), t)
        if t != s:
            planned.append((p, t))
    return planned


def main(argv: list[str]) -> int:
    rec = load()
    planned = sweep(rec["dmg_mb"])
    print(f"download_size: the record says {rec['dmg_mb']} MB ({rec['dmg_bytes']:,} bytes, v{rec['version']}); "
          f"{len(planned)} page(s) {'would change' if '--check' in argv else 'written'}")
    if "--check" not in argv:
        for p, t in planned:
            p.write_text(t, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
