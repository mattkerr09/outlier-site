#!/usr/bin/env python3
"""Every "macOS N or later" sentence on the site must not promise LESS than the binary requires.

2026-09-21 (Crisp found it on itself first): the installed Outlier bundle's Python runtime,
libmlx and libssl carry minos 26.0 — Homebrew builds them for the build box's macOS — and
dyld refuses to load them on anything older; the site said "macOS 12+" on 99 pages. A buyer
on macOS 12–15 pays and the engine never starts. The number comes from
data/binary-requirements.json (measured from the INSTALLED bundle by vtool), never typed.

    python3 scripts/macos_floor_gate.py [root]      # exits 1 on any page promising less
"""
from __future__ import annotations
import json, pathlib, re, sys

ROOT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else ".")
FACTS = json.loads((pathlib.Path(__file__).resolve().parent.parent / "data" / "binary-requirements.json").read_text())
def _ver(v: str) -> tuple:
    """(major, minor) — padded, so "26" == "26.0" (a bare tuple compared "(26,) < (26, 0)" as True
    and flagged the sweep's own replacements as below the floor: a control caught it)."""
    parts = [int(x) for x in v.split(".")]
    return (parts[0], parts[1] if len(parts) > 1 else 0)


FLOOR = _ver(FACTS["min_macos"])
CLAIM = re.compile(r"macOS\s*(\d+(?:\.\d+)?)\s*(?:\([^)]*\)\s*)?(?:or later|or newer|and later|and up|\+)")  # v2: codename parenthetical + "and up"


OURS_MARKS = ("Outlier", "outlier", "operatingSystem", "Intel Macs are not supported", "Which Mac do I need",
              "Apple Silicon only", "Apple Silicon (M", "Mac app (Apple Silicon", "Apple Silicon, macOS", "Download",
              "Apple Silicon Mac", "Apple Silicon Macs only")  # v2 2026-09-23: install prose + "…Macs only" cells
OTHER_MARKS = ("Windows", "Linux", "iOS", "Android", "CUDA", "OS floor", "hardware floor", "llama.cpp", "MLX", "Tabnine", "Intel",
               "Grammarly", "GPT4All", "Notion", "Copilot", "this site supports")


def _is_ours(around: str) -> bool:
    """A requirement line for Outlier, not another product's (or the website's browser
    support). v3 (2026-09-23): evaluated on the ENCLOSING cell only, so a neighbour cell's
    text cannot leak in (that made Grammarly's own "macOS 11" look like ours). Apple-Silicon
    exclusivity is decided BEFORE the rival-name check, because Outlier is the only
    Apple-Silicon-only product on an outlier-vs-X page and its cell often names Windows/Linux
    only to say it does NOT run them."""
    if "Outlier" in around or "outlier" in around or "operatingSystem" in around:
        return True
    # Decisive Outlier signals — Apple-Silicon exclusivity — checked before any rival name.
    for k in ("Apple Silicon only", "Apple Silicon Macs only", "Apple Silicon Mac",
              "Apple Silicon (M", "Mac app (Apple Silicon", "Apple Silicon, macOS"):
        if k in around:
            return True
    # A rival's platform, stated POSITIVELY (not "no Windows"/"not on Linux").
    def _positive(mark: str) -> bool:
        i = around.find(mark)
        while i != -1:
            if not re.search(r"\b(no|not|neither|nor|without)\b", around[max(0, i - 50): i], re.I):
                return True
            i = around.find(mark, i + 1)
        return False
    if any(_positive(k) for k in OTHER_MARKS):
        return False
    if "Apple Silicon" in around:      # Apple-Silicon with no positive other-OS = ours
        return True
    return any(k in around for k in OURS_MARKS)

def main() -> int:
    bad = []; other = []; pages = 0; claims = 0
    for p in sorted(ROOT.rglob("*.html")):
        if "node_modules" in p.parts:
            continue
        t = p.read_text(errors="replace")
        ours = []
        for m in CLAIM.finditer(t):
            # Only OUR requirement is checked: a sentence about Outlier, or the JSON-LD
            # operatingSystem field. "Grammarly needs macOS 11 or newer" is a fact about
            # Grammarly and stays as written.
            # v2 (2026-09-23): scope to the ENCLOSING element, not a flat 160-char window.
            # In a comparison table the window caught the rival's name from an adjacent <td>
            # and misfiled Outlier's own requirement as the rival's, so "macOS 12+" survived.
            _lo = t.rfind(">", 0, m.start()); _hi = t.find("<", m.end())
            cell = t[(_lo + 1): _hi] if (_lo >= 0 and _hi >= 0 and _hi - _lo < 400) else t[max(0, m.start() - 160): m.end() + 60]
            around = cell
            if _is_ours(around):
                ours.append(m.group(1))
            else:
                other.append((str(p), m.group(1)))
        if not ours:
            continue
        pages += 1
        for v in ours:
            claims += 1
            if _ver(v) < FLOOR:
                bad.append((str(p), v))
    print(f"floor from the installed bundle: macOS {FACTS['min_macos']} ({FACTS['mach_o_files']} Mach-O files, bundle {FACTS['bundle_version']})")
    print(f"{claims} claim(s) about Outlier on {pages} page(s); {len(other)} claim(s) about other products left as written")
    if not claims:
        print("FAIL — no macOS claim found anywhere; a gate that checks nothing is not a gate")
        return 1
    if bad:
        by = {}
        for f, v in bad: by.setdefault(v, []).append(f)
        for v, fs in sorted(by.items()):
            print(f"FAIL — {len(fs)} claim(s) promise macOS {v}, below the binary's {FACTS['min_macos']}; first: {fs[0]}")
        return 1
    print("PASS — no page promises a macOS the binary refuses")
    return 0


if __name__ == "__main__":
    sys.exit(main())
