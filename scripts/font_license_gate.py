#!/usr/bin/env python3
"""Every font file this public repository serves must be listed, unchanged, with an open licence.

WHY (2026-11-23, CEO fix 131, found by Article Studio's scan of our public repos): fonts/ held seven Indian Type Foundry
files (Clash Display and Satoshi, from Fontshare). The ITF Free Font License, section 02, does not allow them in a public
repository, and this one is public (mattkerr09/outlier-site). They were named by hash (0f2b9a926c.woff2 ...), so a check by
file name could never see them: only the file's own name table said "Indian Type Foundry". They were replaced by Plus
Jakarta Sans (SIL OFL 1.1).

So the rule here does not guess from names. fonts/fonts_manifest.json lists every font file with its family, licence and
sha256, read from the file's own name table when it was added. This gate fails when:
  - a font file (.woff2 .woff .ttf .otf) anywhere in the repo is not in the manifest;
  - a listed file's bytes changed (its sha256 differs);
  - a listed licence is not OFL-1.1 or Apache-2.0, or its licence text file is missing;
  - the manifest lists a file that is not there.
Adding a font means reading its name table (nameID 0/1/8/13, OS/2 vendor) and listing it; an ITF file cannot be listed
honestly, because no open licence covers it.

    python3 scripts/font_license_gate.py [root]
"""
import hashlib
import json
import pathlib
import sys

OPEN = {"OFL-1.1", "Apache-2.0"}
EXT = (".woff2", ".woff", ".ttf", ".otf")
SKIP = {".git", "node_modules"}


def check(root):
    root = pathlib.Path(root)
    manifest = json.loads((root / "fonts" / "fonts_manifest.json").read_text(encoding="utf-8"))["files"]
    bad = []
    found = sorted(p for p in root.rglob("*") if p.suffix.lower() in EXT and not SKIP.intersection(p.parts))
    for p in found:
        rel = p.relative_to(root).as_posix()
        entry = manifest.get(p.name) if p.parent == root / "fonts" else None
        if entry is None:
            bad.append(f"{rel}: a font file not in fonts/fonts_manifest.json (read its name table and list it with its licence)")
            continue
        if hashlib.sha256(p.read_bytes()).hexdigest() != entry["sha256"]:
            bad.append(f"{rel}: its bytes changed since it was listed (re-read its licence and update the manifest)")
        if entry["license"] not in OPEN:
            bad.append(f"{rel}: licence {entry['license']!r} is not an open licence this public repo may hold")
        if not (root / entry["license_text"]).is_file():
            bad.append(f"{rel}: licence text {entry['license_text']} is missing")
    for name in manifest:
        if not (root / "fonts" / name).is_file():
            bad.append(f"fonts/{name}: listed in the manifest but not in the repo (drop the entry)")
    return found, bad


def main(argv):
    found, bad = check(argv[1] if len(argv) > 1 else pathlib.Path(__file__).resolve().parents[1])
    if bad:
        print(f"FAIL: {len(bad)} font licence problem(s):")
        for b in bad:
            print("  " + b)
        return 1
    print(f"PASS: {len(found)} font file(s), each listed with an open licence and unchanged")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
