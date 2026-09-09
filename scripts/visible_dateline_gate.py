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
#: Shared with jsonld_dateline_gate — same question, same corpus, one rule.
from dateline_policy import GRACE_DAYS, MIN_PAGES, is_stale   # noqa: F401

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


def visible_text_of(s: str) -> str:
    """The notion of 'body text' used everywhere: script/style blocks removed WHOLE."""
    body = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", s, flags=re.S)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", body))).strip()


#: Captures the FIRST <article>…</article> region. Non-greedy so a page with two
#: articles takes the first rather than swallowing everything between them.
_ARTICLE_RE = re.compile(r"<article\b[^>]*>(.*?)</article>", re.S | re.I)


def article_text_of(s: str) -> str:
    """The page's ARTICLE text if it has one, else its whole visible text.

    WHY THIS EXISTS. Comparing whole-page visible text cannot tell an article edit from
    a sitewide chrome insertion — both change visible text on every page. Measured
    2026-09-09: after fixing the CSS-counts-as-prose bug, jsonld_dateline's count barely
    moved (149 -> 147) and 105 pages simply re-concentrated on 2026-08-24, which was
    `1d7e826a` "Email capture on the remaining 184 pages" — a subscribe form inserted
    into every page's chrome. That is not a content update, and dating 105 pages to it
    would have been a mass false freshness claim.

    Scoping to <article> removes shared chrome from the comparison for the pages that
    have one. It is a PARTIAL answer and says so: 178 of 248 pages carry an <article>,
    and the rest fall back to whole-page text and keep the old ambiguity. A partial fix
    that is honest about its coverage beats a whole-page comparison that is quietly wrong
    everywhere.
    """
    m = _ARTICLE_RE.search(s)
    return _norm_churn(visible_text_of(m.group(1) if m else s))


#: Version strings and datelines are CHURN, not content — and they live INSIDE the
#: article, not in the chrome. Measured 2026-09-09: 15 of 16 sampled seo/vs pages carry
#: "Outlier v1.11.NNN" inside <article>, so every ship (three on 2026-09-09 alone)
#: registered as an article content change on those pages and pushed their declared
#: dateline "stale" against an edit that was only a version number.
#:
#: Normalised for COMPARISON only — never for output — so a pure version bump or dateline
#: touch compares equal while any real prose change still differs.
_CHURN_RE = re.compile(r"v?\d+\.\d+\.\d+|\d{4}-\d{2}-\d{2}")


def _norm_churn(t: str) -> str:
    return _CHURN_RE.sub("<>", t)


def has_article(s: str) -> bool:
    return _ARTICLE_RE.search(s) is not None


def visible_text(path: str) -> str:
    return visible_text_of(open(path, encoding="utf-8", errors="replace").read())


def changed_body_text(diff: str) -> bool:
    """⚠️ LINE-SCANNING KEPT ONLY FOR THE FIXTURES. Do NOT use it to date a commit.

    It strips TAGS (`<[^>]*>`) and accepts any remaining segment of 25+ chars. But a
    <style> block's CSS and comments are TEXT BETWEEN TAGS, and HEADISH only skips
    the line carrying the opening `<style`; every interior line sails through. So a
    pure stylesheet edit reads as a body-text change.

    That is not hypothetical. `5f992e2e` ("125 content pages slid sideways on a phone
    when a table was too wide") edited only CSS inside <style>, and this function
    dated 132 pages to it. Those 132 are most of jsonld_dateline_gate's headline 149,
    and I nearly used them to rewrite 149 `dateModified` values — announcing to Google
    that 132 pages of content had changed when only a table's overflow rule had. The
    grace period exists to prevent exactly that false freshness claim.

    `compare_visible(before, after)` is the honest test: it reuses visible_text_of,
    which removes script/style blocks WHOLE, instead of approximating it a second
    time. One notion of body text, not two.
    """
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


def _at(rev: str, path: str) -> str | None:
    r = subprocess.run(["git", "show", f"{rev}:{path}"], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


def compare_visible(before: str | None, after: str | None) -> bool:
    """True when the reader-visible ARTICLE text differs. A first commit counts.

    Uses article_text_of, so a sitewide header/footer/subscribe-box change does not read
    as a content edit on the 178 pages that have an <article>. Pages without one still
    compare whole-page text — see article_text_of for why that is stated rather than hidden.
    """
    if after is None:
        return False
    if before is None:
        return bool(article_text_of(after))
    return article_text_of(before) != article_text_of(after)


def last_body_change(path: str):
    log = subprocess.run(["git", "log", "-8", "--format=%H %ad", "--date=short", "--", path],
                         capture_output=True, text=True).stdout.split("\n")
    for line in log:
        if not line.strip():
            continue
        h, d = line.split()[0], line.split()[1]
        #: Compare the page's VISIBLE TEXT at this commit and its parent, rather than
        #: scanning diff lines. See changed_body_text's docstring: line-scanning counts
        #: a CSS edit as a body change and mis-dated 132 pages to one stylesheet sweep.
        rel = subprocess.run(["git", "ls-files", "--full-name", path],
                             capture_output=True, text=True).stdout.strip() or path
        if compare_visible(_at(h + "^", rel), _at(h, rel)):
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

    #: SELF-CHECK, PLANTED BEFORE THE COMPARISON SO IT RUNS THE REAL PATH.
    #:
    #: ⚠️ The previous version asserted only `(today - probe).days > GRACE_DAYS` — that
    #: 2016 is more than thirty days ago — and then printed "the comparison fires. OK".
    #: That is arithmetic on two dates, a PRECONDITION; the gate's own comparison never
    #: ran. Proved 2026-09-08 by mutation: replacing the loop's `if gap <= GRACE_DAYS:`
    #: with `if True:` — disabling staleness detection ENTIRELY — left this self-check
    #: exiting 0 and still printing that line. The comment above it claimed to "prove the
    #: instrument fires" and the instrument was never touched.
    #:
    #: Identical to the defect found the same evening in adplaybook-site's
    #: source_freshness_gate: A SELF-CHECK CAN ASSERT A PRECONDITION AND PRINT A
    #: CAPABILITY. The sentence it prints is not the sentence it tests, and no amount of
    #: reading the assertion against the implementation shows it — only the mutation does.
    SELF_PAGE = "__self_check_planted__"
    if self_check:
        probe = datetime.date(2016, 1, 1)
        today = datetime.date.today()
        assert (today - probe).days > GRACE_DAYS, \
            "self-check: the probe is not stale — it would prove nothing"
        found = dict(found)
        # ⚠️ DATE objects, not strings. survey() stores (claim: date, body: date, gap: int)
        # and this planted row used strings — harmless only while the decision read the
        # int `gap`. Moving the decision onto dateline_policy.is_stale(claim, body) would
        # have thrown TypeError on the plant. Found by the refactor, not by the tests.
        found[SELF_PAGE] = (probe, today, (today - probe).days)

    baseline = {}
    if os.path.exists(BASELINE):
        baseline = json.load(open(BASELINE))

    new, worse = [], []
    for p, (claim, body, gap) in sorted(found.items()):
        # The decision is dateline_policy's, not this gate's. `gap` is kept for the
        # message; the RULE is asked, never reimplemented.
        if not is_stale(claim, body):
            continue
        if p not in baseline:
            new.append((p, claim, body, gap))
        elif gap > baseline[p] + GRACE_DAYS:
            worse.append((p, claim, body, gap, baseline[p]))

    if self_check:
        # The property, on the observable outcome: the planted decade-stale page must
        # have been REPORTED by the ordinary comparison above.
        planted = [row for row in new if row[0] == SELF_PAGE]
        assert planted, \
            "self-check: THE COMPARISON IS DEAD — a planted 2016 dateline against a " \
            "today body change was not reported. The gate would pass a decade-stale page."
        new = [row for row in new if row[0] != SELF_PAGE]
        found = {k: v for k, v in found.items() if k != SELF_PAGE}
        print("self-check: a planted 2016 dateline was reported by the real comparison "
              "and removed from the result. OK")

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
