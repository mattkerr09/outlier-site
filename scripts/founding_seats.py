#!/usr/bin/env python3
"""How many founding seats Outlier has left — from the worker, which is the one source.

    python3 scripts/founding_seats.py            # print the worker's answer as JSON
    python3 scripts/founding_seats.py --check    # non-zero if the page and the worker disagree

WHY THIS IS NOW A READER AND NOT A COUNTER. The first version of this script counted
succeeded Dodo payments itself and injected the number into index.html. That produced a
page with THREE seat claims at once on 2026-09-15 — my injected count, the shared widget
already on the page, and a sentence promising no seat cap at all. Two of them were mine.

A second source of truth is not a safety net, it is a contradiction generator. The widget
reads the worker; the worker reads Dodo; so this script reads the worker too, and the only
number that can appear on the page is the one the widget renders.

THE SEAT DEFINITION, because counting is where copies drift (Matthew, 2026-09-15):
a seat is a PAID, NON-REFUNDED order of the product. The $0.00 order of 2026-08-21 is a
comp and holds no seat. Outlier therefore has 1 held and 24 left, not the 23 my own count
produced by treating the comp as a seat. The rule is encoded once, in the Dodo code's
usage_limit, and `left = usage_limit - times_used` — so nothing here re-derives it.
Each app has its own 25 and its own code; Outlier's is FOUNDINGOUTLIER.
"""
from __future__ import annotations

import json
import re
import sys
import urllib.request
from pathlib import Path

WORKER = "https://kerr-lead-agent.kerrco.workers.dev/founding?site=outlier.host"


def founding() -> dict:
    req = urllib.request.Request(WORKER, headers={"User-Agent": "kerr-ops/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def main(argv: list[str]) -> int:
    try:
        d = founding()
    except Exception as e:  # noqa: BLE001
        print(f"FAIL: could not read the founding worker ({e}). Refusing to emit a seat "
              f"count from anything else — a second source is how the page ended up "
              f"claiming three different things.", file=sys.stderr)
        return 1
    if "left" not in d or "of" not in d:
        print(f"FAIL: the worker did not return a seat count: {d}", file=sys.stderr)
        return 1

    if "--check" in argv:
        html = (Path(__file__).resolve().parent.parent / "index.html").read_text(encoding="utf-8")
        hard = re.findall(r'data-founding-left="(\d+)"', html)
        if hard:
            print(f"FAIL: index.html hardcodes {hard} seats left. The widget renders the "
                  f"worker's number; a second one on the page is a contradiction, not a "
                  f"backup.", file=sys.stderr)
            return 1
        print(f"founding_seats: ok — the page carries no hardcoded count; the worker says "
              f"{d['left']} of {d['of']} left ({d.get('claimed')} claimed, code "
              f"{d.get('code')})")
        return 0

    print(json.dumps(d))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
