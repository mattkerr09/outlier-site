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

The host serves these files verbatim — verified 2026-08-18, local and deployed
index.html were byte-identical at sha256 b8d29032. So an exact hash comparison is
the right instrument; no normalisation, nothing to tune. (This site is NOT served
by GitHub Pages; see README. An earlier version of this docstring said it was.)

WHAT "THE SITE IS THE COMMIT" HAS TO MEAN. Matching the files that exist is only
half of it. A file deleted from the repo is unpublished only if the host stops
serving it, and nothing above could ever see that: every check starts from a path
that is present at HEAD. outlier.host served a superseded IndexNow key file — a
standing authorisation for whoever holds it to submit URLs for this host — and
this gate would have printed PASS beside it forever. So deletions are checked too,
from git history rather than from a list somebody remembers to update.

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
import time
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

#: Files deleted from the repo must stop being served. Suffixes the host will
#: serve as-is; a deletion of anything else cannot be a publication problem.
SERVABLE_SUFFIXES = (".html", ".txt", ".xml", ".png", ".jpg", ".svg", ".json", ".css", ".js", ".ico", ".md")
#: A deletion pushed minutes ago has not had time to propagate, and flagging it
#: would make every removal red until the sync ran. Older than this and "still
#: served" is no longer explainable by lag.
GRACE_S = 45 * 60
#: How far back to look for deletions. Bounded so the gate stays fast.
LOG_DEPTH = 400


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


def status(url: str) -> int | None:
    """Status code only. A deleted file is a question about presence, not bytes."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA}, method="GET")
        with urllib.request.urlopen(req, timeout=45) as r:
            return r.getcode()
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return None


def check_deletions() -> tuple[int, list[tuple[str, str, float]], int]:
    """Every path deleted in the last LOG_DEPTH commits and never re-added.

    Derived from history rather than from a hand-kept list, so a file someone
    removes tomorrow is covered without anyone remembering to add it here.
    """
    out = subprocess.run(
        ["git", "log", f"-{LOG_DEPTH}", "--diff-filter=D", "--name-only", "--format=%x00%ct"],
        capture_output=True, text=True).stdout
    when: dict[str, int] = {}
    ts = None
    for line in out.split("\n"):
        if line.startswith("\x00"):
            ts = int(line[1:])
            continue
        path = line.strip()
        if path and ts is not None and path.endswith(SERVABLE_SUFFIXES):
            when.setdefault(path, ts)  # most recent deletion of that path

    now = time.time()
    confirmed, still_served, in_flight = 0, [], 0
    for path, t in sorted(when.items()):
        if at_head(path) is not None:
            continue  # deleted once, then re-added
        age = now - t
        if age < GRACE_S:
            in_flight += 1
            continue
        url = SITE + "/" + (path[: -len("index.html")] if path.endswith("index.html") else path)
        code = status(url)
        if code == 200:
            still_served.append((path, url, age / 3600))
            print(f"  [SERVED] {url} — deleted, still 200")
        elif code is None:
            print(f"  [?] {url} — no answer, not counted either way")
        else:
            confirmed += 1
            print(f"  [gone] {url} ({code})")
    return confirmed, still_served, in_flight


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
        # TWO fetches, because this edge can serve an OLDER copy after having
        # served a newer one. Measured 2026-09-07: the home page verified live
        # with a change at 22:47, answered WITHOUT it at 23:10 (129,940 bytes),
        # and answered with it again at 23:12 (130,684). Six consecutive probes
        # in between were identical, so it is not per-request randomness — it is
        # nodes disagreeing, and a single sample cannot see that.
        #
        # Disagreement is reported as its OWN state rather than folded into
        # pass/fail: "stale" and "inconsistent" need different responses. Stale
        # means wait; inconsistent means the edge is mid-propagation and any
        # verdict from one sample is luck.
        live = fetch(SITE + url_path)
        live2 = fetch(SITE + url_path)
        if live is not None and live2 is not None and sha(live) != sha(live2):
            fails.append(
                f"{path}: the edge served TWO DIFFERENT copies of {url_path} within one run "
                f"({len(live)} bytes then {len(live2)} bytes). Not stale — inconsistent. Any "
                f"single-sample verification of this path right now is luck; re-run once it settles.")
            continue
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
    # The other half of "the site is the commit": what was deleted must be gone.
    gone, still_served, in_flight = check_deletions()
    if still_served:
        for path, url, age_h in still_served:
            fails.append(
                f"{path}: deleted from the repo but still served at {url} (200).\n"
                f"       Removed {age_h:.1f}h ago, well past the {GRACE_S // 60}m sync window.\n"
                f"       A file is unpublished only when the host stops serving it.")

    if fails:
        print(f"\nFAIL ({len(fails)}):")
        for f in fails:
            print(f"  {f}")
        return 1
    if gone:
        print(f"\nPASS — {checked} served files byte-match HEAD, and {gone} file(s) deleted from")
        print("       the repo are confirmed gone from the host. The site is the commit,")
        print("       in both directions.")
    else:
        print(f"\nPASS — all {checked} served files byte-match HEAD.")
        print("       Deletions: NOT MEASURED — no removal in the last "
              f"{LOG_DEPTH} commits is both still absent at HEAD and older than "
              f"{GRACE_S // 60}m. This half of the claim was not tested.")
    if in_flight:
        print(f"\n  note: {in_flight} recent deletion(s) inside the {GRACE_S // 60}m window,")
        print("        not checked yet — they will be on the next run.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# CORRECTION to the commit that added the two-fetch check (1fb00efc). It cited
# "129,940 bytes" for a response that lacked the new links. That number was a
# Python len(str) — CHARACTERS — compared against byte counts from wc -c and
# len(live). The same response measures 130,684 bytes and 130,393 characters:
# 291 multi-byte characters, mostly em dashes. So the three-version enumeration
# in that message was wrong; two of its numbers were not comparable.
#
# What survives, on unit-safe evidence: a content check found 0 of 3 new links in
# a response at 23:10 and 3 of 3 two minutes later (a boolean, not a size), and
# this gate measured 130,590 served bytes against 130,684 at HEAD — both byte
# counts, from len() over bytes. The edge did serve an older copy after serving a
# newer one. The oscillation is real; my arithmetic for it was not.
#
# NEVER compare a Python len(str) to wc -c. One counts characters, the other
# counts bytes, and on this site they differ by ~291 on every page.
