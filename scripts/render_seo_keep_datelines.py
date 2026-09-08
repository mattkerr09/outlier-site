#!/usr/bin/env python3
"""Render /seo/ and then UNDO the pages the render only re-datestamped.

⚠️ WHY THIS EXISTS. `_seo_build/scripts/render.py` rewrites every page it owns on
every run, stamping today's date into `dateModified`, the visible byline and the
sitemap's `<lastmod>`. On 2026-09-08 a one-category prose fix that legitimately
changed SIX pages came out as **49 modified files** — 43 of them carrying nothing but
a new date and a new version string.

Publishing that would be a false freshness signal on 43 pages whose text did not
change, which is exactly what `scripts/jsonld_dateline_gate.py` exists to catch and
what the standing "fix-on-edit only, never bulk-run touch_dateline.py" rule forbids.
The trap is that the build looks like it succeeded: nothing errored, and the diff is
all real file content.

⇒ A BUILD THAT REGENERATES EVERYTHING REPORTS EVERY PAGE AS CHANGED. Diff the
CONTENT, not the file list.

This wrapper renders, reverts every page whose diff is date/version churn ONLY, and
moves `<lastmod>` for just the pages whose body actually moved.

Usage:  python3 scripts/render_seo_keep_datelines.py [--dry-run]
Run from the outlier-site repo root. Requires a clean-ish tree: it will refuse if
seo/ or sitemap.xml already has uncommitted changes, because it cannot then tell your
edits from the render's.
"""
import argparse
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TODAY = __import__("datetime").date.today().isoformat()


def git(*args, check=True):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True,
                          text=True, check=check).stdout


def is_churn(diff_line: str) -> bool:
    """A changed line that carries only a dateline or a version byline."""
    return ('"dateModified"' in diff_line
            or ("Last updated" in diff_line and re.search(r"Outlier v\d+\.\d+\.\d+", diff_line)))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true",
                    help="report what would be reverted, change nothing")
    args = ap.parse_args()

    dirty = git("status", "--short", "--", "seo/", "sitemap.xml").strip()
    if dirty:
        print("REFUSING: seo/ or sitemap.xml already has uncommitted changes.\n"
              "This script cannot tell your edits from the render's. Commit or stash first:\n"
              + dirty)
        return 2

    r = subprocess.run([sys.executable, "_seo_build/scripts/render.py"],
                       cwd=ROOT, capture_output=True, text=True)
    # render.py exits non-zero on its own pre-existing shingle ERRORS; that is a
    # separate standing problem and must not silently abort this wrapper. Report it.
    if r.returncode != 0:
        print(f"note: render.py exited {r.returncode} (it has standing shingle errors); "
              f"continuing, since the pages were still written")

    changed = [f for f in git("diff", "--name-only", "--", "seo/").split() if f]
    real, churn = [], []
    for f in changed:
        d = git("diff", "-U0", "--", f)
        lines = [l for l in d.splitlines()
                 if l[:1] in "+-" and not l.startswith(("+++", "---"))]
        (churn if lines and all(is_churn(l) for l in lines) else real).append(f)

    print(f"rendered: {len(changed)} page(s) modified")
    print(f"  real content change : {len(real)}")
    print(f"  date/version churn  : {len(churn)}")
    for f in real:
        print("     REAL ", f)
    if args.dry_run:
        print("\n--dry-run: reverting nothing")
        return 0

    if churn:
        git("checkout", "--", *churn)
    git("checkout", "--", "sitemap.xml")

    moved = 0
    if real:
        sm = ROOT / "sitemap.xml"
        s = sm.read_text()
        for f in real:
            url = "https://outlier.host/" + f[: -len("index.html")]
            pat = re.compile(r"(<loc>" + re.escape(url) + r"</loc>\s*<lastmod>)\d{4}-\d{2}-\d{2}(</lastmod>)")
            s, n = pat.subn(lambda m: m.group(1) + TODAY + m.group(2), s)
            moved += n
            if not n:
                print(f"  ⚠️ no sitemap entry for {url}")
        sm.write_text(s)

    print(f"\nreverted {len(churn)} churn-only page(s); sitemap lastmod moved for {moved}/{len(real)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
