#!/usr/bin/env python3
"""The date a reader sees, not the one a crawler reads.

This gate was written believing the renderer kept `dateModified` in JSON-LD
honest, so that only the human-readable line had rotted. **That premise was
measured on 2026-09-08 and is FALSE**: 155 of 226 pages declare a `dateModified`
more than 30 days behind their own last body-text change, the worst by 111 days.
Both axes had rotted; only this one was ever checked. See
`jsonld_dateline_gate.py`, which is this gate's pair — same corpus, same
body-text comparison, the other axis. Measured 2026-09-08, the visible half: 151 of 163 pages carried
a VISIBLE "Last updated <date>" line more than 30 days older than the page's last
body-text change, the worst by 106 days. A reader checking whether our
competitor-pricing page was current was told it had not moved since May; its body
changed on 2026-09-02, correcting a rival's price.

The machine-readable date was maintained. The human-readable one was hand-written
into each page and nothing regenerated it. Only the second is a promise.

WHAT COUNTS AS A VIOLATION, and three things that are NOT one. Each of these
changed the count while the finding was being measured, and each was caught by
opening a flagged case rather than trusting a total:

  1. Compare against the last BODY-TEXT change, not the last commit. Bulk
     mechanical commits — stripping UTMs, adding Related blocks, hub links —
     touch a file without altering a word a reader sees.
  2. Ignore <title> and <meta description>. They are long prose between tags, so
     a naive visible-text diff counts them, but they are SERP text and not page
     text. This over-fired during the original measurement.
  3. A scoped claim is not a page claim. "updated April 12, 2025" on the Aider
     page is about Aider; "As of July 2026: Basic $0, Pro $16" is a pricing
     snapshot. Neither is falsified by editing our prose. Nineteen first-pass
     hits were this, which is why only a PAGE-LEVEL dateline counts here — one
     immediately followed by the article opening.

RATCHET. 151 pages are already wrong and fixing them is a renderer change, not a
gate's job. So the backlog is baselined and only NEW or WORSENED divergence
fails. Edit the baseline BY REMOVAL ONLY.

    python3 scripts/visible_dateline_gate.py            # check
    python3 scripts/visible_dateline_gate.py --self-check  # prove it can fail
"""
from __future__ import annotations

import datetime
import html
import json
import os
import re
import subprocess
import sys

BASELINE = os.path.join(os.path.dirname(__file__), "visible_dateline_baseline.json")
GRACE_DAYS = 30
MIN_PAGES = 50

MONTHS = {m.lower()[:3]: i + 1 for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July",
     "August", "September", "October", "November", "December"])}

#: A PAGE-level dateline: "Updated <date>" sitting in the furniture, immediately
#: before the article opens. An "as of" inside a paragraph is a scoped claim.
DATELINE = re.compile(
    r"(?i)\bUpdated\s+([A-Za-z]{3,9}\s+\d{0,2},?\s*20\d\d|20\d\d-\d\d-\d\d)\s*(?=Quick answer|Disclosure|$)")
HEADISH = re.compile(r"<(title|meta|link|script|style)\b", re.I)


def claim_date(text: str):
    m = re.search(r"([A-Za-z]{3,9})\s+(\d{1,2}),?\s+(20\d\d)", text)
    if m and m.group(1).lower()[:3] in MONTHS:
        return datetime.date(int(m.group(3)), MONTHS[m.group(1).lower()[:3]], int(m.group(2)))
    m = re.search(r"(20\d\d)-(\d\d)-(\d\d)", text)
    if m:
        return datetime.date(*map(int, m.groups()))
    m = re.search(r"([A-Za-z]{3,9})\s+(20\d\d)", text)
    if m and m.group(1).lower()[:3] in MONTHS:
        return datetime.date(int(m.group(2)), MONTHS[m.group(1).lower()[:3]], 1)
    return None


def visible_text(path: str) -> str:
    s = open(path, encoding="utf-8", errors="replace").read()
    body = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", s, flags=re.S)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", body)))


def changed_body_text(diff: str) -> bool:
    for line in diff.split("\n"):
        if not line or line[0] not in "+-" or line[:3] in ("+++", "---"):
            continue
        if HEADISH.search(line):          # refinement 2
            continue
        for seg in re.sub(r"<[^>]*>", "\x00", line[1:]).split("\x00"):
            seg = seg.strip()
            if len(seg) >= 25 and not seg.startswith(("http", "utm_")):
                return True
    return False


def last_body_change(path: str):
    log = subprocess.run(["git", "log", "-8", "--format=%H %ad", "--date=short", "--", path],
                         capture_output=True, text=True).stdout.split("\n")
    for line in log:
        if not line.strip():
            continue
        h, d = line.split()[0], line.split()[1]
        diff = subprocess.run(["git", "show", h, "--", path],
                              capture_output=True, text=True).stdout
        if changed_body_text(diff):       # refinement 1
            return datetime.date.fromisoformat(d)
    return None


def survey(site_root: str = "."):
    """Walk `site_root` so meta_gate can point this at an empty tree.

    meta_gate refuses to accept a gate it cannot aim: a gate that ignores argv[1]
    can only ever be probed against the real site, and "it passed on the real site"
    proves nothing about whether it CAN fail. It caught this one the day it was
    written, which is the whole point of having a gate over the gates.
    """
    out = {}
    for root, dirs, files in os.walk(site_root):
        if any(x in root for x in (".git", "_seo_build", "scripts", "node_modules")):
            continue
        for f in files:
            if not f.endswith(".html") or ".pre" in f:
                continue
            p = os.path.join(root, f).replace("./", "")
            m = DATELINE.search(visible_text(p))   # refinement 3
            if not m:
                continue
            claim = claim_date(m.group(0))
            if not claim:
                continue
            body = last_body_change(p)
            if not body:
                continue
            out[p] = (claim, body, (body - claim).days)
    return out


def main() -> int:
    self_check = "--self-check" in sys.argv
    roots = [a for a in sys.argv[1:] if not a.startswith("-")]
    site_root = roots[0] if roots else "."
    found = survey(site_root)
    if len(found) < MIN_PAGES:
        print(f"FAIL: surveyed {len(found)} dated page(s) under {site_root!r}, "
              f"expected at least {MIN_PAGES}.")
        print("      A gate that checked nothing prints the same word as a clean one.")
        return 1

    if self_check:
        # Prove the instrument fires: a claim a decade stale must be a violation.
        probe = datetime.date(2016, 1, 1)
        today = datetime.date.today()
        assert (today - probe).days > GRACE_DAYS, "self-check probe is not stale"
        print(f"self-check: a 2016 dateline against a {today} body change is "
              f"{(today - probe).days} days stale — the comparison fires. OK")

    baseline = {}
    if os.path.exists(BASELINE):
        baseline = json.load(open(BASELINE))

    new, worse = [], []
    for p, (claim, body, gap) in sorted(found.items()):
        if gap <= GRACE_DAYS:
            continue
        if p not in baseline:
            new.append((p, claim, body, gap))
        elif gap > baseline[p] + GRACE_DAYS:
            worse.append((p, claim, body, gap, baseline[p]))

    print(f"visible_dateline_gate: {len(found)} page-level dateline(s); "
          f"{sum(1 for v in found.values() if v[2] > GRACE_DAYS)} diverge by more than {GRACE_DAYS} days")
    print(f"visible_dateline_gate: {len(baseline)} baselined, not enforced — "
          f"see {os.path.basename(BASELINE)}")

    if new or worse:
        print(f"\nFAIL ({len(new)} new, {len(worse)} worsened):")
        for p, c, b, g in new[:10]:
            print(f"  {p}: says 'Updated {c}', body last changed {b} ({g} days).")
            print("       A reader is told this page has not moved since then. It has.")
        for p, c, b, g, was in worse[:10]:
            print(f"  {p}: divergence grew {was} -> {g} days.")
        return 1
    print("\nPASS — no new or worsened divergence between what a page says and when it changed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
