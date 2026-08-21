#!/usr/bin/env python3
"""A tracker may not exist on this site unless the privacy policy discloses it.

Why this exists
---------------
The Meta pixel and the privacy rewrite shipped in one commit. Nothing stops a
later edit from tidying the policy — shortening a list, restoring a cleaner
sentence — and leaving the tracker in place. The result would be a page promising
no cross-site tracking while setting `_fbp`, on a site whose entire pitch is that
nothing leaves your machine. That is the worst version of the claim-vs-reality
defect this repo keeps finding, because it is the one a regulator reads.

So the coupling is enforced in both directions:

    pixel present  ->  policy MUST name the pixel, name `_fbp`, and must NOT
                       carry any of the retired absolute claims
    pixel absent   ->  policy must not claim a pixel is running

Why the retired sentences are listed by their exact text
--------------------------------------------------------
Each was TRUE before the pixel and false after, and each fails differently:

  "no cross-site tracking"     described Plausible but read as a site-wide promise
  "One conditional cookie"     a COUNTING claim -- `_fbp` makes it wrong, and so
                               would any replacement count
  "no cookie is set"           said cookies depend on arriving via affiliate link;
                               `_fbp` is set however you arrive
  "two scripts above"          a UNIQUENESS claim; the pixel is a third

A count or a uniqueness claim is a liability the moment anything is added. This
gate refuses them by exact string rather than trying to judge prose.

What this gate CANNOT tell you
------------------------------
That the pixel actually fires. A wrong id still loads fbevents.js, still returns
200, still defines `fbq` — every signal green while Meta records nothing. The only
discriminator is whether `_fbp` gets set in a real browser on the live site. That
is a post-deploy check against the deployed page, not something a static scan can
do, and it is stated here so nobody reads a PASS as proof the pixel works.
"""
import re
import sys
from pathlib import Path

PIXEL_ID = "1592291422272376"
POLICY = "privacy.html"

# Text that became false when the pixel landed. Exact strings, not judgement.
RETIRED = [
    "no cross-site tracking",
    "One conditional cookie",
    "no cookie is set",
    "two scripts above",
]

# What an honest disclosure has to name.
REQUIRED = ["Meta pixel", "_fbp"]

MIN_PAGES = 120


def main(root_arg: str = ".") -> int:
    root = Path(root_arg)
    policy = root / POLICY
    if not policy.is_file():
        print(f"FAIL: {POLICY} not found — cannot verify disclosure.")
        return 1

    pages, carrying = 0, []
    for f in sorted(root.rglob("*.html")):
        rel = f.relative_to(root).as_posix()
        if "_seo_build" in rel:
            continue
        pages += 1
        if PIXEL_ID in f.read_text(errors="replace"):
            carrying.append(rel)

    if pages < MIN_PAGES:
        print(f"FAIL: only {pages} pages scanned, expected >= {MIN_PAGES}. "
              f"A short scan is a broken scan, not a clean site.")
        return 1

    ptext = policy.read_text(errors="replace")
    problems = []

    if carrying:
        for phrase in RETIRED:
            if phrase in ptext:
                problems.append(
                    f"{POLICY} still says {phrase!r}, which the pixel makes false. "
                    f"Replace the sentence — do not append a caveat to it.")
        for phrase in REQUIRED:
            if phrase not in ptext:
                problems.append(
                    f"{POLICY} does not mention {phrase!r}, but the pixel is live on "
                    f"{len(carrying)} page(s). A tracker must be named to be disclosed.")
    else:
        if any(p in ptext for p in REQUIRED):
            problems.append(
                f"{POLICY} discloses a Meta pixel, but no page carries id {PIXEL_ID}. "
                f"Either the tag was dropped and the policy now overstates what runs, "
                f"or the id changed and this gate is checking a stale one.")

    print(f"pages scanned: {pages} | pages carrying the pixel: {len(carrying)}")
    if carrying:
        print("  " + ", ".join(carrying[:8]) + (" ..." if len(carrying) > 8 else ""))

    if problems:
        print(f"\nFAIL ({len(problems)}):")
        for p in problems:
            print(f"  {p}")
        return 1

    print("\nPASS — the pixel and its disclosure agree.")
    print("NOTE: this proves the tag and the policy match. It does NOT prove the")
    print("pixel fires — a wrong id loads, returns 200 and defines fbq with nothing")
    print("recorded. Check `_fbp` in a browser on the live site for that.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "."))
