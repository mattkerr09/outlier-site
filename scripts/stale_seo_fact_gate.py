#!/usr/bin/env python3
"""The /seo/ generator and the pages it built must not carry three facts that stopped being true.

WHY THIS EXISTS. _seo_build/scripts/render.py typed its own sentences: the old $249 price, "macOS 26" as the
requirement, and the build the pages were last stamped with. By 2026-11-04 a fresh render would have walked ten
how-to guides back to the old price and an OS floor the app does not have (the app runs on macOS 15), and 47 built
pages still said "Outlier v1.11.945" when the shipped build was 1.11.990. Each fact has a gate on the pages it was
found on (checkout_price, macos_floor, download_version); none of them read the GENERATOR, so a re-render could put
a fixed page back. This one reads both: the generator's sources (_seo_build/) and every built file under seo/.

It FAILS (exit 1) on any of:
  * the old price "$249", except where the same passage says outright that it is a FORMER price. A sentence-ending
    "$249." counts: the generator's own sentence was "... Lifetime Licence at $249." and a lookahead that let a
    full stop through would have passed the very line this gate was written for. "$249.50", "$249,000" and "$2490"
    are other numbers and pass.
  * "macOS 26" as Outlier's requirement. "macOS 26.3.1" (the test Mac's own version) passes.
  * "1.11.945".

It REFUSES (exit 1, a different message) on a tree it cannot call clean: no generator, or fewer built pages than a
real checkout has. A gate that scans nothing prints the same "0 found" as a clean site; this one will not.

    python3 scripts/stale_seo_fact_gate.py [root]
    python3 scripts/stale_seo_fact_gate.py --self-check
"""
from __future__ import annotations

import contextlib
import io
import re
import sys
import tempfile
from pathlib import Path

SOURCE_DIR = "_seo_build"
BUILT_DIR = "seo"
GENERATOR = "_seo_build/scripts/render.py"
#: /seo/ has 61 pages today. Far below that means the wrong directory, a failed checkout or a deleted tree, not
#: a site that got clean. Low enough that retiring a handful of pages never trips it.
MIN_PAGES = 20
EXTS = {".py", ".html", ".json", ".csv", ".txt", ".md", ".js", ".css", ".yml", ".yaml", ".xml"}
MAX_BYTES = 5_000_000

#: (label, pattern). The first is not the pattern first handed over for this gate, which was r"\$249(?![\d,.])":
#: that lookahead excludes a following "." and so lets "at $249." (a sentence end) through.
CHECKS = [
    ("old price $249", re.compile(r"\$249(?!\d|[.,]\d)")),
    ("macOS 26 as the requirement", re.compile(r"macOS 26(?!\.\d)")),
    ("build 1.11.945", re.compile(r"1\.11\.945")),
]

#: A passage that SAYS the price is a former one: "the former price", "old price", "price was", "was $249",
#: "formerly $249", "used to cost". Looked for within ±160 characters of the match, tags stripped.
FORMER = re.compile(
    r"\b(?:former(?:ly)?|previous(?:ly)?|old|earlier|original|retired)\b[^.]{0,40}\bprice\b"
    r"|\bprice\b[^.]{0,30}\b(?:was|used to be)\b"
    r"|\b(?:was|used to be|used to cost|formerly)\s+\$249",
    re.I)
TAG = re.compile(r"<[^>]+>")


def _is_former_price(text: str, m: re.Match) -> bool:
    region = TAG.sub(" ", text[max(0, m.start() - 160): m.end() + 160])
    return bool(FORMER.search(region))


def scan_file(rel: str, text: str) -> list[str]:
    out = []
    for label, rx in CHECKS:
        for m in rx.finditer(text):
            if label.startswith("old price") and _is_former_price(text, m):
                continue
            line = text.count("\n", 0, m.start()) + 1
            ctx = text[max(0, m.start() - 40): m.end() + 40].replace("\n", " ")
            out.append(f"{rel}:{line}: {label}: ...{ctx}...")
    return out


def walk(root: Path):
    for d in (SOURCE_DIR, BUILT_DIR):
        base = root / d
        if not base.is_dir():
            continue
        for p in sorted(base.rglob("*")):
            if p.is_file() and p.suffix.lower() in EXTS and p.stat().st_size <= MAX_BYTES:
                yield p


def check(root: Path, min_pages: int = MIN_PAGES) -> int:
    if not (root / GENERATOR).is_file():
        print(f"REFUSE: no {GENERATOR} under {root} - the generator was not found, so nothing it writes can be "
              "called clean.")
        return 1
    pages = [p for p in (root / BUILT_DIR).rglob("*.html")] if (root / BUILT_DIR).is_dir() else []
    if len(pages) < min_pages:
        print(f"REFUSE: {len(pages)} built page(s) under {root / BUILT_DIR} (a real tree has at least {min_pages}) - "
              "this is not the tree the gate was written for, and a scan of nothing reads exactly like a clean one.")
        return 1
    found, scanned = [], 0
    for p in walk(root):
        scanned += 1
        found += scan_file(str(p.relative_to(root)), p.read_text(encoding="utf-8", errors="replace"))
    if found:
        print(f"FAIL: {len(found)} stale fact(s) in the /seo/ generator or the pages it built "
              f"({scanned} files, {len(pages)} pages scanned):")
        for f in found[:60]:
            print("  " + f)
        if len(found) > 60:
            print(f"  ... and {len(found) - 60} more")
        print("Fix the source in _seo_build/scripts/render.py (read the price from data/product-facts.json, the floor "
              "from data/binary-requirements.json, the version from index.html) and the page it built.")
        return 1
    print(f"OK: {scanned} files, {len(pages)} built pages: no $249, no macOS 26 requirement, no 1.11.945.")
    return 0


def _quiet(root: Path, **kw) -> int:
    """check() with its report swallowed: the self-check asserts on the exit code, not on the text."""
    with contextlib.redirect_stdout(io.StringIO()):
        return check(root, **kw)


def _put(root: Path, rel: str, text: str) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def self_check() -> int:
    """Each bad string, planted alone in a generator source and in a built page, must be caught; the controls that
    look similar must pass; an empty or short tree must be refused, not reported clean."""
    bad = {
        "old price $249": ["Pro is a one-time purchase: the Outlier Lifetime Licence at $249.",
                           "<p>Pro: $249 once</p>", "<li>$249, then $124.50</li>", "$249/month"],
        "macOS 26 as the requirement": ["Apple Silicon, macOS 26 or later.", "signed DMG on macOS 26+ Apple Silicon.",
                                        "Needs macOS 26."],
        "build 1.11.945": ['<p class="byline">Last updated 2026-10-19 &middot; Outlier v1.11.945</p>',
                           "releases/download/v1.11.945/Outlier-1.11.945-arm64.dmg"],
    }
    good = ["The test Mac runs macOS 26.3.1.", "Pro is $49 once. Apple Silicon, macOS 15 or later. Outlier v1.11.990.",
            "A rival charges $249.50 a year.", "A rig that costs $2490.",
            "$249,000 of GPUs.", "The former price was $249 until October.",
            "<p>It was $249 before the sale.</p>"]
    ok = True
    notes = []

    # 1. every bad string is caught by itself, labelled with its own check
    for label, samples in bad.items():
        for s in samples:
            hits = scan_file("x.html", s)
            if not any(label in h for h in hits):
                ok = False
                notes.append(f"missed [{label}]: {s!r}")
    # 2. every look-alike passes
    for s in good:
        hits = scan_file("x.html", s)
        if hits:
            ok = False
            notes.append(f"false alarm on {s!r}: {hits[0]}")

    # 3. a tiny fixture tree: one bad string in the generator source, one in each of three built pages, one clean page
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _put(root, GENERATOR, 'x = "the Outlier Lifetime Licence at $249."\n')
        _put(root, "_seo_build/templates/_base.html", "<p>macOS 26 or later</p>")
        _put(root, "seo/a/index.html", "<p>Pro is $249 once.</p>")
        _put(root, "seo/b/index.html", "<p>Requires macOS 26+.</p>")
        _put(root, "seo/c/index.html", '<p class="byline">Outlier v1.11.945</p>')
        _put(root, "seo/clean/index.html", "<p>$49 once. macOS 15 or later. macOS 26.3.1 test Mac. v1.11.990.</p>")
        _put(root, "seo/_data/release.json", '{"version": "1.11.990"}')
        found = []
        for p in walk(root):
            found += scan_file(str(p.relative_to(root)), p.read_text(encoding="utf-8"))
        wanted = {"_seo_build/scripts/render.py": "old price", "_seo_build/templates/_base.html": "macOS 26",
                  "seo/a/index.html": "old price", "seo/b/index.html": "macOS 26", "seo/c/index.html": "1.11.945"}
        for rel, what in wanted.items():
            if not any(h.startswith(rel + ":") and what in h for h in found):
                ok = False
                notes.append(f"fixture: {rel} was not flagged for {what}")
        if any(h.startswith(("seo/clean/", "seo/_data/")) for h in found):
            ok = False
            notes.append("fixture: the clean page or the release record was flagged")
        if _quiet(root, min_pages=1) != 1:
            ok = False
            notes.append("fixture: check() did not fail on a tree that carries every bad string")

    # 4. the clean fixture passes, and the empty / short trees are refused
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _put(root, GENERATOR, 'PRICE = "$49"\n')
        _put(root, "seo/clean/index.html", "<p>$49 once. macOS 15 or later.</p>")
        if _quiet(root, min_pages=1) != 0:
            ok = False
            notes.append("clean fixture: check() failed a tree with none of the three facts")
        if _quiet(root) != 1:
            ok = False
            notes.append("short tree: check() passed a tree with fewer built pages than a real checkout")
    with tempfile.TemporaryDirectory() as tmp:
        if _quiet(Path(tmp)) != 1 or _quiet(Path(tmp), min_pages=1) != 1:
            ok = False
            notes.append("empty tree: check() did not refuse")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _put(root, "seo/a/index.html", "<p>$49 once.</p>")     # pages but no generator
        if _quiet(root, min_pages=1) != 1:
            ok = False
            notes.append("no generator: check() did not refuse")

    if ok:
        print("OK: self-check - every planted $249 / macOS 26 / 1.11.945 is caught in the generator and in built "
              "pages, the look-alikes ($249.50, $2490, macOS 26.3.1, a stated former price) pass, and an empty, "
              "short or generator-less tree is refused.")
        return 0
    print("FAIL: self-check - the gate cannot see what it exists to catch:")
    for n in notes:
        print("  " + n)
    return 1


if __name__ == "__main__":
    if "--self-check" in sys.argv[1:]:
        raise SystemExit(self_check())
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    raise SystemExit(check(Path(args[0] if args else ".")))
