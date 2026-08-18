#!/usr/bin/env python3
"""Every download URL on the site must actually resolve to a file.

THE SIBLING GATE DOES NOT COVER THIS, DELIBERATELY. download_version_gate.py compares the version
NAMED in each URL against the latest published tag, and its docstring is explicit that status
codes cannot do that job: GitHub keeps old assets forever, so a URL pointing at a release from
fifty versions ago returns a perfectly healthy 200. Right call for that gate — but it means the
site is checked for naming the right version and never for the asset being there.

The failure that slips between them: a release publishes as v1.11.790 with the asset named
slightly differently (Outlier-1.11.790.dmg instead of Outlier-1.11.790-arm64.dmg), or an upload
that failed partway. Every URL on the site names v1.11.790, the version gate PASSES, and every
download button on outlier.host 404s. Naming the right version and pointing at a real file are two
different properties, and each gate only proves one.

⚠️ WHY A STATUS CHECK IS TRUSTWORTHY HERE WHEN IT IS WORTHLESS FOR THE CHECKOUT. checkout_gate.py
records that an invented Polar token returns 200, because Polar redirects unknown tokens to its
marketing homepage — so no status code discriminates. GitHub release assets are not like that: a
missing asset genuinely 404s. That is a claim about a third party, so this gate does not assume
it, it PROVES it every run with a bogus filename on the same host and tag. If the control ever
returns 200 the gate FAILS and says the method has stopped working, rather than reporting a clean
site it can no longer see.

Measured 2026-08-18:
    Outlier-1.11.790-arm64.dmg  -> 200, 301792005 bytes
    Outlier-NoSuchFile-999.dmg  -> 404          (the control)

    python3 scripts/download_reachable_gate.py [root]
"""
from __future__ import annotations

import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from download_version_gate import UA, scan  # noqa: E402  — one definition of "a download URL"

TIMEOUT = 60


def head(url: str) -> int:
    """Status for `url`, following redirects. 0 means the request itself failed."""
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return 0


#: Directories that are BUILD INPUT, not served pages. _seo_build/templates/_base.html carries
#: `…/download/v{{ app_version }}/…`, which is a Jinja placeholder, not a URL — the first run of
#: this gate reported it as a broken download button. Scanning build sources alongside published
#: output is the same mistake as testing the dev binary instead of the bundled one: check what is
#: SERVED. (download_version_gate.py never hit this because its regex requires a version-shaped
#: string, so the placeholder cannot match it.)
NOT_SERVED = ("_seo_build", "node_modules", ".git")


def urls_from(root: Path) -> list[str]:
    """Rebuild the full URL for every download link on a PUBLISHED page."""
    out = []
    for p in sorted(root.rglob("*.html")):
        if any(part in NOT_SERVED for part in p.parts):
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        import re
        for m in re.finditer(r'https://github\.com/[^"\'\s]+/releases/download/[^"\'\s]+', text):
            out.append(m.group(0))
    return sorted(set(out))


def main(root_arg: str = ".") -> int:
    root = Path(root_arg)
    if not scan(root):
        print("FAIL: the shared scanner found no download URLs at all — this gate would pass")
        print("      on an empty set, which reads exactly like a healthy site.")
        return 1

    urls = urls_from(root)
    if not urls:
        print("FAIL: no download URLs matched — nothing was checked")
        return 1
    print(f"distinct download URLs: {len(urls)}")

    # THE CONTROL FIRST. A 200-for-everything host makes every line below meaningless, and a gate
    # that cannot tell the difference must not report a pass.
    sample = urls[0]
    bogus = sample.rsplit("/", 1)[0] + "/Outlier-NoSuchFile-999.dmg"
    ctl = head(bogus)
    if ctl == 200:
        print(f"FAIL: the control returned 200 — a bogus filename is being served.\n"
              f"      {bogus}\n"
              f"      Status codes no longer discriminate on this host, so this gate cannot\n"
              f"      prove anything and must not report a pass.")
        return 1
    if ctl == 0:
        print(f"FAIL: the control request could not be made at all — network or host problem.\n"
              f"      Refusing to report on reachability without a working method.")
        return 1
    print(f"control (bogus filename) -> {ctl}  ✓ missing files really do fail")

    bad = []
    for u in urls:
        st = head(u)
        if st != 200:
            bad.append(f"{st or 'no response'}  {u}")
        else:
            print(f"  [ok] {st}  {u.rsplit('/', 1)[-1]}")
    if bad:
        print(f"\nFAIL — {len(bad)} download URL(s) do not resolve:")
        for b in bad:
            print(f"    {b}")
        print("\n  Every one of these is a Download button that gives the visitor nothing.")
        return 1
    print(f"\nPASS — all {len(urls)} download URLs resolve, and the control proves a missing "
          f"one would not")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "."))
