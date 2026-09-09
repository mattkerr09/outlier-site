#!/usr/bin/env python3
"""The date the CRAWLER reads — the other half of visible_dateline_gate.

visible_dateline_gate exists because the human-readable "Last updated" line had
rotted while the machine-readable one was maintained. Its docstring says so:
"The renderer keeps `dateModified` in JSON-LD honest ... so every check that
reads JSON-LD reports this site accurate."

Measured 2026-09-08, that premise is FALSE. Of 226 pages carrying a JSON-LD
`dateModified`, **155 declare a date more than 30 days older than the page's last
body-text change**, the worst by 111 days. Nothing had ever checked it, because
the gate that would have was built on the assumption that this axis was fine.

That is the one-axis class in its purest form: a two-axis format, a check on one
axis, and a green board. The two gates are now a pair — same corpus, same
body-text comparison, opposite axis.

WHY IT MATTERS MORE THAN THE VISIBLE ONE. A reader who sees a stale "Last
updated" may shrug. Google reads `dateModified` to decide whether a page is worth
recrawling, and a page that has declared May since May is a page it has been told
not to revisit. Our own Search Console reading shows 12 crawled-and-declined URLs.

WHAT IS NOT A VIOLATION. All three refinements are inherited from
visible_dateline_gate by importing its logic rather than reimplementing it —
two implementations of one comparison is how the pair drifts apart:
  1. compare against the last BODY-TEXT change, not the last commit. A bulk
     mechanical commit (a version-pointer sweep, a crumb edit) touches a file
     without altering a word. Measured both ways here: commit dates gave 158
     over the threshold, body-text gave 155.
  2. <title>/<meta> churn is not body text.
  3. datePublished is never touched — that one does not move.

MATCH BOTH SPACINGS. 140 pages write `"dateModified":"..."` and 86 write
`"dateModified": "..."`. A regex for one of them reads clean over the other 62%
of the site — which is exactly how this went unmeasured for so long.

RATCHET. The backlog is baselined; only NEW or WORSENED divergence fails. Edit the
baseline BY REMOVAL ONLY.

⚠️ DO NOT "FIX THE BACKLOG" BY REWRITING dateModified. I built that backfill on
2026-09-09 and threw it away, one command before running it on 149 pages. The
count is real; what it MEANS is not what the number looks like.

  - 132 of the 149 dated to a single day, 2026-08-25. That was `5f992e2e`, a CSS
    fix for tables overflowing on phones across "125 content pages". It changed no
    prose. The old line-scanning detector counted it because it strips TAGS and
    then accepts any 25+ char segment — and a <style> block's CSS is text BETWEEN
    tags. Fixed: last_body_change now compares visible_text_of (script/style
    removed WHOLE) at the commit and its parent.
  - After that fix the count barely moved, 149 -> 147, and 105 pages simply
    re-concentrated on 2026-08-24 — `1d7e826a`, "Email capture on the remaining
    184 pages". That one DID change visible text. It is still not a content
    update; it is a form inserted into every page's chrome.

So even a correct visible-text comparison cannot tell an article edit from a
sitewide chrome insertion, because both change visible text on every page.
Rewriting these datelines would tell Google that 147 pages of content had
changed when what changed was a table's overflow rule and a subscribe box —
the exact false freshness claim the 30-day grace exists to prevent.

A dateline may only be moved on evidence that THAT PAGE'S OWN prose changed.
Scoping the comparison to <article> is the obvious next step and is only a
partial answer: 178 of 248 pages have one.

    python3 scripts/jsonld_dateline_gate.py               # check
    python3 scripts/jsonld_dateline_gate.py --self-check  # prove it can fail
    python3 scripts/jsonld_dateline_gate.py --rebaseline  # after a renderer fix
"""
from __future__ import annotations

import datetime
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from visible_dateline_gate import last_body_change  # ONE implementation, not two

BASELINE = os.path.join(os.path.dirname(__file__), "jsonld_dateline_baseline.json")
#: The staleness rule and the vacuity floor are SHARED with visible_dateline_gate — they
#: answer the same question about the same corpus, so two copies would drift. See
#: dateline_policy.py for why this is a predicate rather than a number.
from dateline_policy import GRACE_DAYS, MIN_PAGES, is_stale   # noqa: F401  (GRACE_DAYS in messages)

#: Both spacings. The whole point.
DATEMOD = re.compile(r'"dateModified"\s*:\s*"(\d{4}-\d{2}-\d{2})"')


def survey(site_root: str = "."):
    """-> {relpath: days_stale} for every page whose declared date lags its body."""
    out = {}
    checked = 0
    for dirpath, dirnames, filenames in os.walk(site_root):
        dirnames[:] = [d for d in dirnames if d not in (".git", "node_modules", "scripts")]
        for fn in filenames:
            if fn != "index.html":
                continue
            path = os.path.join(dirpath, fn)
            rel = os.path.relpath(path, site_root)
            try:
                s = open(path, encoding="utf-8", errors="replace").read()
            except OSError:
                continue
            m = DATEMOD.search(s)
            if not m:
                continue
            checked += 1
            body = last_body_change(path)
            if body is None:
                continue
            _declared = datetime.date.fromisoformat(m.group(1))
            days = (body - _declared).days
            if is_stale(_declared, body):
                out[rel] = days
    return out, checked


def main(argv):
    root = "."
    for a in argv[1:]:
        if not a.startswith("--"):
            root = a
    found, checked = survey(root)

    if "--rebaseline" in argv:
        json.dump(dict(sorted(found.items())), open(BASELINE, "w"), indent=1)
        print(f"jsonld_dateline_gate: baselined {len(found)} page(s)")
        return 0

    # A check that read nothing reads exactly like a clean one.
    if checked < MIN_PAGES:
        print(f"FAIL: only {checked} page(s) had a JSON-LD dateModified — expected "
              f">= {MIN_PAGES}. The parser or the corpus moved; this run proves nothing.",
              file=sys.stderr)
        return 1

    baseline = json.load(open(BASELINE)) if os.path.exists(BASELINE) else {}
    new, worse = [], []
    for rel, days in sorted(found.items()):
        if rel not in baseline:
            new.append((rel, days))
        elif days > baseline[rel]:
            worse.append((rel, days, baseline[rel]))

    print(f"jsonld_dateline_gate: {checked} page(s) with a JSON-LD dateModified; "
          f"{len(found)} lag their body text by more than {GRACE_DAYS} days")
    print(f"jsonld_dateline_gate: {len(baseline)} baselined, not enforced — see "
          f"{os.path.basename(BASELINE)}")
    if not new and not worse:
        return 0
    print(f"\nFAIL ({len(new)} new, {len(worse)} worsened):", file=sys.stderr)
    for rel, days in new:
        print(f"  {rel}: dateModified is {days} days behind the last body change.\n"
              f"       A crawler is told this page has not moved since then. It has.",
              file=sys.stderr)
    for rel, days, was in worse:
        print(f"  {rel}: {was} -> {days} days behind.", file=sys.stderr)
    return 1


def self_check():
    """The gate must fail on its own bug. Plant a stale date, assert it fires."""
    import tempfile, shutil, subprocess
    src = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
        work = os.path.join(tmp, "site")
        shutil.copytree(src, work, ignore=shutil.ignore_patterns(".git", "node_modules"))
        subprocess.run(["git", "init", "-q"], cwd=work)
        subprocess.run(["git", "add", "-A"], cwd=work, capture_output=True)
        subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t",
                        "commit", "-qm", "base"], cwd=work, capture_output=True)
        # baseline the fixture FIRST — a 1-page fixture trips its own vacuity guard
        page = None
        for dp, dn, fns in os.walk(work):
            if "index.html" in fns and DATEMOD.search(
                    open(os.path.join(dp, "index.html"), encoding="utf-8", errors="replace").read()):
                page = os.path.join(dp, "index.html"); break
        assert page, "no page with a dateModified in the fixture"
        s = open(page, encoding="utf-8").read()
        planted = DATEMOD.sub('"dateModified":"2019-01-01"', s, count=1)
        assert planted != s, "PLANT DID NOT LAND — the check would have proved nothing"
        open(page, "w", encoding="utf-8").write(
            planted.replace("</body>", "<p>A sentence long enough to count as a real body-text change.</p></body>"))
        subprocess.run(["git", "add", "-A"], cwd=work, capture_output=True)
        subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t",
                        "commit", "-qm", "plant"], cwd=work, capture_output=True)
        # last_body_change() shells out to git with NO cwd, so it queries whatever
        # repo the process is standing in. Surveying an absolute /tmp path from the
        # real checkout asked THIS repo about a file it has never seen, got no
        # history, and skipped every page -- the gate read 226 pages and found
        # nothing, which looks exactly like clean. Stand in the fixture instead.
        here = os.getcwd()
        try:
            os.chdir(work)
            found, checked = survey(".")
        finally:
            os.chdir(here)
        rel = os.path.relpath(page, work)
        if rel in found:
            print(f"self-check PASS: planted a 2019 date and the gate saw it "
                  f"({found[rel]} days, {checked} pages read)")
            return 0
        print(f"self-check FAIL: planted a stale date and the gate did NOT see it "
              f"({checked} pages read). The gate cannot fail; it proves nothing.",
              file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(self_check() if "--self-check" in sys.argv else main(sys.argv))
