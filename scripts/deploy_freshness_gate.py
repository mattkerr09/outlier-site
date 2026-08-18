#!/usr/bin/env python3
"""What is committed is not what is served. This checks the served copy.

Every other gate in this directory reads the working tree. All four can be green
while outlier.host serves something else entirely — a push that GitHub Pages
never rebuilt, a build that failed after the commit landed, a CDN holding an old
copy. The repo would be correct and the customer would still be reading the old
page, and nothing here would say so.

That is not hypothetical for this project. It is recorded that fifty pages served
a DMG roughly three hundred versions stale while every checker reported green,
and that a 200 can be the wrong artifact rather than the right one.

HOW IT DECIDES, and why it compares against HEAD rather than the working copy:
a mismatch has two very different causes and they need different fixes.

    deployed != HEAD          -> the deploy is behind. Push, or wait for Pages.
    working copy != HEAD      -> you have uncommitted edits. Not a deploy fault.

Comparing the live file to the file on disk conflates them: mid-edit, it would
scream "deploy is stale" when nothing is wrong with the deploy. So the
comparison is always deployed-vs-HEAD, and uncommitted local edits are reported
separately as information, not as failure.

GitHub Pages serves these files verbatim — verified 2026-08-18, local and
deployed index.html were byte-identical at sha256 b8d29032. So an exact hash
comparison is the right instrument; no normalisation, nothing to tune.

THE CONTROL. A gate that fetches a URL and compares hashes fails open in the
most ordinary way imaginable: if the fetch quietly returns something unexpected
and every comparison mismatches, that reads as "everything stale" — but if a
path is wrong and the file is skipped, it reads as PASS on zero checks. So this
refuses to pass unless it actually compared MIN_FILES, and it proves per run
that a mismatch is detectable by hashing a deliberately altered copy.

    python3 scripts/deploy_freshness_gate.py
"""
from __future__ import annotations

import hashlib
import subprocess
import sys
import urllib.request

SITE = "https://outlier.host"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120"

#: Path in the repo -> URL path on the live site. Chosen to span the deploy:
#: the hand-edited homepage, a renderer-generated page, and a binary asset. A
#: partial deploy that updated one and not the others is the thing to catch.
FILES = {
    "index.html": "/",
    "seo/how-to/install-outlier-on-mac/index.html": "/seo/how-to/install-outlier-on-mac/",
    "og-card.png": "/og-card.png",
}
MIN_FILES = 3


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def at_head(path: str) -> bytes | None:
    try:
        return subprocess.run(["git", "show", f"HEAD:{path}"], capture_output=True, check=True).stdout
    except subprocess.CalledProcessError:
        return None


def fetch(url: str) -> bytes | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=45) as r:
            return r.read()
    except Exception:
        return None


def main() -> int:
    # Vacuity control: prove a mismatch is detectable at all, this run.
    probe = b"<html>x</html>"
    if sha(probe) == sha(probe + b" "):
        print("FAIL: hashing cannot distinguish different bytes. Instrument is broken.")
        return 1

    checked, fails, dirty = 0, [], []
    for path, url_path in FILES.items():
        head_bytes = at_head(path)
        if head_bytes is None:
            fails.append(f"{path}: not present at HEAD — is the path right?")
            continue
        live = fetch(SITE + url_path)
        if live is None:
            fails.append(f"{path}: could not fetch {SITE}{url_path}")
            continue

        checked += 1
        h_head, h_live = sha(head_bytes), sha(live)
        same = h_head == h_live
        print(f"  [{'ok' if same else 'STALE'}] {url_path}")
        if not same:
            fails.append(
                f"{path}: served copy does not match HEAD.\n"
                f"       HEAD   {h_head[:16]}  ({len(head_bytes)} bytes)\n"
                f"       served {h_live[:16]}  ({len(live)} bytes)\n"
                f"       The commit landed; the deploy did not. Nothing in the repo will show this.")

        # Reported, never failed on — an uncommitted edit is not a deploy fault.
        try:
            disk = open(path, "rb").read()
            if sha(disk) != h_head:
                dirty.append(path)
        except OSError:
            pass

    if dirty:
        print(f"\n  note: uncommitted local edits in {', '.join(dirty)} — not a deploy problem,")
        print("        and deliberately not a failure. The comparison above used HEAD.")

    if checked < MIN_FILES:
        print(f"\nFAIL: compared {checked} file(s), expected {MIN_FILES}.")
        print("      A gate that checked nothing prints the same word as a clean one.")
        return 1
    if fails:
        print(f"\nFAIL ({len(fails)}):")
        for f in fails:
            print(f"  {f}")
        return 1
    print(f"\nPASS — all {checked} served files byte-match HEAD; the site is the commit.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
