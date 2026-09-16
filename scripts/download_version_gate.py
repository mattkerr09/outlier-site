#!/usr/bin/env python3
"""Every Download button on the site must name the CURRENT published release.

Written 2026-08-18, after 50 pages under /seo/ were found serving
v1.11.477 while the live release was v1.11.788 — roughly three hundred versions
of drift, including every price string corrected the night before. Those pages
are the ones search traffic lands on, so a new visitor's first act was to
download an app quoting $99 lifetime against a $249 checkout.

WHY THE EXISTING CHECKS COULD NOT SEE IT
GitHub keeps old release assets forever, so
  .../releases/download/v1.11.477/Outlier-1.11.477-arm64.dmg
returns 200. Every link checker on this site reported healthy. The defect is not
a broken link, it is a WORKING link to the wrong artifact, and no amount of
status-code checking will ever surface that. The only way to catch it is to
compare each URL against what is actually published today.

WHAT IT CHECKS
  1. every download URL names the latest published tag
  2. the tag segment and the filename segment agree with each other (they drifted
     apart once already: byline said 1.11.628 while the button said 1.11.477)
  3. the three places index.html states the current version in PROSE rather than
     in an href — the nav badge, the hero trust line, and the JSON-LD
     softwareVersion that search engines read. 68b5a062 fixed exactly this: the
     page advertised 788 in words beside a 790 button, and a gate that only reads
     hrefs reported PASS throughout.

     It does NOT touch the version numbers in the benchmark rows ("0/50 · blind ·
     all 50 patches empty · v1.11.788") or the methodology line. Those are
     provenance — which build produced which score — and bumping them to the
     current release would turn a true record into a false claim. That is why
     each prose site is matched by an exact anchor instead of a blanket
     "every version must be current" sweep.
  4. it actually found some URLs, and every prose anchor still matches — see below

THE VACUITY GUARD IS NOT OPTIONAL. A scan that finds zero URLs prints exactly
what a clean scan prints. Three separate instruments lied by returning empty
during the session that produced this file: macOS has no `timeout` binary so the
whole command was "not found", an escaped grep in a shell loop matched nothing,
and `git add` on a gitignored path staged nothing while exiting 0. So this gate
fails when the URL count falls below MIN_URLS rather than congratulating itself.

    python3 scripts/download_version_gate.py
"""
from __future__ import annotations

import datetime as _dt

import json
import re
import sys
import urllib.request
from pathlib import Path

REPO = "Outlier-host/outlier-app-releases"
API = f"https://api.github.com/repos/{REPO}/releases/latest"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120"

#: Below this, assume the scan broke rather than that the site got smaller.
MIN_URLS = 40

DL_RE = re.compile(
    r"releases/download/v(\d+\.\d+\.\d+)/Outlier-(\d+\.\d+\.\d+)-arm64\.dmg"
)

#: Places index.html asserts the CURRENT downloadable version in prose. Each entry
#: must match at least once: a pattern that stops matching has silently stopped
#: covering its site, which reads identically to a clean pass.
PROSE_SITES = [
    ("nav badge",           re.compile(r'class="nav-ver">v(\d+\.\d+\.\d+)')),
    ("hero trust line",     re.compile(r'class="trust[^"]*">v(\d+\.\d+\.\d+)\s*&middot;|class="trust[^"]*">v(\d+\.\d+\.\d+)\s*·')),
    ("JSON-LD softwareVersion", re.compile(r'"softwareVersion":\s*"(\d+\.\d+\.\d+)"')),
]


def latest_tag() -> str:
    req = urllib.request.Request(API, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)["tag_name"].lstrip("v")


def scan(root: Path):
    hits = []
    for p in sorted(root.rglob("*.html")):
        if ".git" in p.parts:
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for tag_v, file_v in DL_RE.findall(text):
            hits.append((p, tag_v, file_v))
    return hits


#: /seo/ is deliberately pinned to an older build while a titles experiment
#: reads out, which made this gate fail on EVERY ship — and a gate that always
#: fails is a gate nobody reads. CI has been red on "Point the site at 1.11.830"
#: and "...831" for exactly this reason, so a genuinely new failure would have
#: gone unnoticed. The frozen set is therefore expected rather than fatal.
#:
#: ⚠️ IT EXPIRES ON ITS OWN, AND THAT IS THE WHOLE POINT. A permanent exemption
#: would mean the freeze ending silently leaves 54 pages stale with nothing to
#: complain — trading a noisy gate for a blind one. After this date the frozen
#: pages fail like any other, and the message says the freeze has lapsed.
SEO_FREEZE_UNTIL = _dt.date(2026, 9, 22)
SEO_FREEZE_PREFIX = "seo/"


def main(root_arg: str = ".") -> int:
    root = Path(root_arg)
    try:
        current = latest_tag()
    except Exception as e:
        print(f"FAIL: could not read the latest release from GitHub: {e}")
        print("      (refusing to pass without knowing what is published)")
        return 1

    hits = scan(root)
    print(f"latest published release: v{current}")
    print(f"download URLs found:      {len(hits)}")

    if len(hits) < MIN_URLS:
        print(f"\nFAIL: only {len(hits)} download URLs found, expected >= {MIN_URLS}.")
        print("      The scan is more likely broken than the site. Not reporting clean.")
        return 1

    stale = [(p, t, f) for p, t, f in hits if t != current or f != current]
    mismatched = [(p, t, f) for p, t, f in hits if t != f]

    if mismatched:
        print(f"\nFAIL: tag and filename disagree in {len(mismatched)} URL(s):")
        for p, t, f in mismatched[:10]:
            print(f"  {p}: /v{t}/ but Outlier-{f}-arm64.dmg")
    if stale:
        print(f"\nFAIL: {len(stale)} download URL(s) do not name v{current}:")
        seen: dict[str, int] = {}
        for _, t, _f in stale:
            seen[t] = seen.get(t, 0) + 1
        for v, n in sorted(seen.items(), key=lambda kv: -kv[1]):
            print(f"  {n:>4} page(s) still on v{v}")
        # ⚠️ A DELIBERATELY FROZEN SET CAMOUFLAGES A FORGOTTEN PAGE.
        # /seo/ is held at an older build on purpose while a titles experiment
        # reads out, so this gate is EXPECTED to fail — and an expected failure
        # is one nobody reads. On 2026-09-16 that hid `thank-you.html`, the page
        # a customer lands on AFTER PAYING, five versions stale at v1.11.827,
        # sitting inside a count of "55 page(s) still on v1.11.827" whose other
        # 54 entries were frozen on purpose. Nothing was broken; the number was
        # simply never read, because it always says the same thing.
        #
        # So the two groups are printed apart, and the NOT-frozen ones first and
        # in full. A page outside /seo/ that has gone stale is nobody's decision
        # — it is an oversight, and it should be the first thing on screen.
        _frozen = [h for h in stale if str(h[0]).startswith("seo/")]
        _loose = [h for h in stale if not str(h[0]).startswith("seo/")]
        if _loose:
            print(f"\n  NOT frozen — {len(_loose)} page(s) nobody decided to hold back:")
            for p_, t_, _f in _loose:
                print(f"       {p_} -> v{t_}")
        if _frozen:
            print(f"\n  under seo/ — {len(_frozen)} page(s), frozen deliberately while the")
            print( "  titles experiment reads out; expected, and listed second for that reason:")
            for p_, t_, _f in _frozen[:6]:
                print(f"       {p_} -> v{t_}")
            if len(_frozen) > 6:
                print(f"       … and {len(_frozen) - 6} more under seo/")
        print("\n  These URLs almost certainly return 200 — GitHub keeps old assets.")
        print("  A link checker cannot catch this; that is why this gate exists.")

    # --- prose sites: the half an href-only gate cannot see -------------------
    prose_fails = []
    index = root / "index.html"
    if not index.exists():
        prose_fails.append(f"index.html not found at {index} — prose checks did not run")
    else:
        text = index.read_text(encoding="utf-8", errors="ignore")
        for label, rx in PROSE_SITES:
            found = [g for m in rx.finditer(text) for g in m.groups() if g]
            if not found:
                prose_fails.append(
                    f"{label}: pattern matched NOTHING. Either the markup changed or the "
                    f"line was removed — either way this site is no longer covered, which "
                    f"looks exactly like passing. Re-point the anchor.")
                continue
            bad = [v for v in found if v != current]
            print(f"  prose {label:<24} v{found[0]}" + ("  <- STALE" if bad else ""))
            if bad:
                prose_fails.append(f"{label}: says v{bad[0]}, current release is v{current}")

    if prose_fails:
        print(f"\nFAIL: {len(prose_fails)} prose version problem(s):")
        for f in prose_fails:
            print(f"  {f}")
        print("\n  These are words, not links, so the download-URL check above cannot see them.")

    _today = _dt.date.today()
    _frozen_ok = _today <= SEO_FREEZE_UNTIL
    _blocking = [h for h in stale
                 if not (_frozen_ok and str(h[0]).startswith(SEO_FREEZE_PREFIX))]
    if _frozen_ok and len(_blocking) < len(stale):
        print(f"\n  ({len(stale) - len(_blocking)} stale page(s) under {SEO_FREEZE_PREFIX} are "
              f"EXEMPT until {SEO_FREEZE_UNTIL} — deliberate freeze, not a defect.)")
    elif not _frozen_ok and any(str(h[0]).startswith(SEO_FREEZE_PREFIX) for h in stale):
        print(f"\n  THE {SEO_FREEZE_PREFIX} FREEZE LAPSED ON {SEO_FREEZE_UNTIL} — those pages "
              f"now count. Re-point them or move the date deliberately.")

    if _blocking or mismatched or prose_fails:
        return 1
    if stale:
        print(f"\nPASS — every page outside the {SEO_FREEZE_PREFIX} freeze names v{current} "
              f"({len(stale)} frozen page(s) still on an older build, by decision)")
    else:
        print(f"\nPASS — {len(hits)} download URLs and {len(PROSE_SITES)} prose sites all name v{current}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "."))
