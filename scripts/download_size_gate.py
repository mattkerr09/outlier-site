#!/usr/bin/env python3
"""Every "NNN MB" the site says about the download must be the release record's figure.

    python3 scripts/download_size_gate.py <root>          # offline: claims vs seo/_data/release.json
    python3 scripts/download_size_gate.py --live <root>   # also: the record vs the published GitHub asset
    python3 scripts/download_size_gate.py --self-check    # proves it fails on a wrong figure

2026-10-24 (CEO audit): the site said "290 MB" in ~250 places while the 1.11.960 DMG was 276,293,500 bytes. The
figure was typed by hand and nothing compared it with a release. This fails when:
  * the record is missing, or names a version other than the one the homepage advertises;
  * its dmg_mb is not its own dmg_bytes in decimal megabytes;
  * any current-size claim (scripts/download_size.py SHAPES) shows another figure;
  * fewer than MIN_CLAIMS claims are found — a scan that finds nothing has checked nothing;
  * --live: the record's byte count is not the published asset's.
"""
from __future__ import annotations

import pathlib
import re
import shutil
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import download_size as ds  # noqa: E402  (one definition of a size claim)

#: 2026-10-24 the site carried ~250 claims; under this the scan has broken, not the site.
MIN_CLAIMS = 50


def check(root: pathlib.Path, live: bool = False) -> list[str]:
    bad = []
    try:
        rec = ds.load(root)
    except FileNotFoundError:
        return [f"no release record at {ds.RECORD} — scripts/bump_site_version.py writes it"]
    except ValueError as e:
        return [f"{ds.RECORD} is not JSON: {e}"]
    idx = root / "index.html"
    m = re.search(r'"softwareVersion":\s*"([\d.]+)"', idx.read_text(encoding="utf-8", errors="replace")) if idx.is_file() else None
    if not m:
        bad.append("cannot read the advertised version from index.html")
    elif m.group(1) != rec.get("version"):
        bad.append(f"the record is for {rec.get('version')} but the site advertises {m.group(1)}")
    if rec.get("dmg_mb") != ds.mb(int(rec.get("dmg_bytes") or 0)):
        bad.append(f"dmg_mb {rec.get('dmg_mb')} is not {rec.get('dmg_bytes')} bytes in MB ({ds.mb(int(rec.get('dmg_bytes') or 0))})")
    found = ds.claims(root)
    print(f"download_size_gate: {len(found)} size claim(s); the record says {rec.get('dmg_mb')} MB for v{rec.get('version')}")
    if len(found) < MIN_CLAIMS:
        bad.append(f"only {len(found)} size claims found (expected >= {MIN_CLAIMS}) — the scan is likelier broken than the site")
    wrong = {}
    for p, fig in found:
        if fig != rec.get("dmg_mb"):
            wrong.setdefault(fig, []).append(str(p.relative_to(root)))
    for fig, ps in sorted(wrong.items()):
        bad.append(f"{len(ps)} claim(s) say {fig} MB, not {rec.get('dmg_mb')} MB: {', '.join(sorted(set(ps))[:5])}")
    if live and rec.get("version"):
        n = ds.fetch_release_bytes(rec["version"])
        if n != rec.get("dmg_bytes"):
            bad.append(f"the published Outlier-{rec['version']}-arm64.dmg is {n:,} bytes; the record says {rec.get('dmg_bytes'):,}")
    return bad


def self_check() -> int:
    """Copy the real site, plant one wrong figure, and demand a FAIL; the untouched copy must pass."""
    root = pathlib.Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory() as t:
        t = pathlib.Path(t)
        for rel in [ds.RECORD, pathlib.Path("index.html")]:
            (t / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(root / rel, t / rel)
        fig = ds.load(t)["dmg_mb"]
        pages = "".join(f"<a>Download free ({fig} MB)</a>\n" for _ in range(MIN_CLAIMS))
        (t / "a.html").write_text(pages, encoding="utf-8")
        if check(t):
            print("SELF-CHECK FAIL: a clean tree did not pass:", check(t)); return 1
        (t / "b.html").write_text(f"<p>macOS 15+ (free update) &middot; {fig + 14} MB</p>", encoding="utf-8")
        if not any(f"{fig + 14} MB" in b for b in check(t)):
            print("SELF-CHECK FAIL: a wrong figure passed"); return 1
    print("download_size_gate self-check: PASS (clean passes, a wrong figure fails)")
    return 0


def main(argv: list[str]) -> int:
    if "--self-check" in argv:
        return self_check()
    args = [a for a in argv if not a.startswith("--")]
    root = pathlib.Path(args[0] if args else ".")
    bad = check(root, live="--live" in argv)
    for b in bad:
        print(f"  FAIL: {b}")
    print("download_size_gate: " + ("FAIL" if bad else "PASS"))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
