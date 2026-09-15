#!/usr/bin/env python3
"""A page may promise no seat cap, or count seats. Never both.

    python3 scripts/seat_claim_gate.py [root]

WHY THIS EXISTS, and it is a mistake of mine from 2026-09-15. Asked to restore a
founding-seat bar, I derived the count honestly from Dodo, gated it, verified it live —
and shipped a page that says "23 of 25 founding seats left" directly above a Pro card
that says "No seat cap, no countdown". Every gate passed. The number was right. The page
contradicted itself, which is worse than either claim being wrong, because a reader
cannot tell which half to believe and there is no way to resolve it from the page.

The order was withdrawn minutes later for exactly this reason: the no-cap promise is a
deliberate, recorded position (RULES.md ~line 328), and I had not checked the record
before writing a number onto the page.

So this gate does not care which way the business decides. It cares that the page only
says one of them. If a seat count is ever restored, this still holds -- and the count is
additionally checked against Dodo, so "derived, not typed" survives the decision.
"""
from __future__ import annotations

import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

NO_CAP = re.compile(r"no seat cap|no countdown", re.I)
#: A seat COUNT, not the words "seat cap" -- the no-cap sentence contains those words.
COUNTS = re.compile(r'data-founding-left="\d+"|\bdata-founding\b'
                    r'|\b\d+\s+of\s+\d+\b[^<]{0,30}seats?\s+left'
                    r'|\bseats?\s+left\b|\bseats?\s+remaining\b', re.I)

#: A COUNT CAN BE RENDERED RATHER THAN WRITTEN, and my first version could not see one.
#: Measured 2026-09-15: outlier.host served THREE seat claims at once - my hardcoded bar
#: (23 of 25), a shared worker widget reading Dodo's FOUNDING1 code (22 of 25, a pool
#: shared with Crisp), and the sentence "No seat cap, no countdown". This gate read the
#: static HTML, found no "seats left" string because the widget fills itself in at
#: runtime, and reported clean. Matching the widget's `data-founding` attribute is what
#: makes the claim visible to a checker that never executes the page.
#:
#: BASELINE IS EMPTY AGAIN, AND THAT IS THE POINT. index.html carried the widget AND a
#: "No seat cap, no countdown" sentence while Matthew decided; that pair was recorded here
#: rather than left failing, because a gate red for days pending a decision is a gate
#: nobody reads. He decided on 2026-09-15 — 25 seats per app, each with its own code — the
#: sentence was rewritten to match, and the exemption came straight back out. A baseline is
#: a note about a decision in flight, never a permanent hole.
BASELINE: set[str] = set()


def main(root: str = ".") -> int:
    base = pathlib.Path(root)
    pages = [p for p in base.rglob("*.html") if ".git" not in p.parts]
    if not pages:
        print(f"FAIL: no .html under {root!r} — nothing was checked, so this is not a "
              f"pass.", file=sys.stderr)
        return 1

    both, counting, held = [], [], []
    for p in pages:
        s = p.read_text(encoding="utf-8", errors="ignore")
        has_nocap, has_count = bool(NO_CAP.search(s)), bool(COUNTS.search(s))
        if has_nocap and has_count:
            if str(p.relative_to(base)) in BASELINE:
                held.append(p)
                continue
            both.append(p)
        elif has_count:
            counting.append(p)

    if both:
        for p in both:
            print(f"FAIL: {p} promises no seat cap AND counts seats. A reader cannot "
                  f"tell which is true, and neither can a checker.", file=sys.stderr)
        return 1

    # A RENDERED count is fine — the widget reads the worker, which reads the store, so
    # it cannot drift. A HARDCODED one is the thing to catch: it is a second source, and a
    # second source of truth is a contradiction generator rather than a backup. That is
    # exactly how index.html came to carry three different seat claims on 2026-09-15.
    if counting:
        import re as _re
        hard = [(p, m.group(1)) for p in counting
                for m in [_re.search(r'data-founding-left="(\d+)"',
                                     p.read_text(encoding="utf-8", errors="ignore"))] if m]
        if hard:
            try:
                import founding_seats as fs
                live = str(fs.founding().get("left"))
            except Exception:  # noqa: BLE001
                live = None
            for p, n in hard:
                extra = f" The worker says {live}." if live else ""
                print(f"FAIL: {p} hardcodes {n} seats left. The widget already renders the "
                      f"worker's number; a second count on the page is a contradiction, "
                      f"not a backup.{extra}", file=sys.stderr)
            return 1
        print(f"seat_claim_gate: ok — {len(counting)} page(s) carry the founding widget, "
              f"none hardcodes a count, and none also promises no seat cap")
        return 0

    if held:
        # SAYING "none counts seats" here would be false: the baselined page DOES
        # count them, it is simply not failing yet. A gate must never describe as
        # clean the thing it skipped.
        for p in held:
            print(f"seat_claim_gate: BASELINED — {p} both promises no seat cap and "
                  f"carries a seat count (the shared founding widget). Awaiting "
                  f"Matthew's decision; not failing, not clean.")
        print(f"seat_claim_gate: ok — {len(pages)} page(s) checked; {len(held)} known "
              f"contradiction(s) baselined, no new one")
        return 0
    print(f"seat_claim_gate: ok — {len(pages)} page(s) checked; none counts seats, so "
          f"the site's no-seat-cap promise stands unopposed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "."))
