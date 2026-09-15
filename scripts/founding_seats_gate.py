#!/usr/bin/env python3
"""The seat count on the page must equal the seat count in Dodo.

    python3 scripts/founding_seats_gate.py [root]

WHY. `founding_seats.py --inject` writes a real number into index.html at commit time,
which makes it right on the day and wrong the moment the next seat sells. A scarcity
claim is the one number on the site a buyer can check against reality by buying, so
"derived once" is not the same as "true now". This is the half that keeps it true.

IT FAILS WHEN IT CANNOT CHECK. No API key, no reachable API, no bar on the page — all
non-zero. A gate that goes quiet when its instrument is missing is how a stale number
lives for a month: every run says nothing and nothing looks wrong. The one thing it must
never do is report clean without having compared two numbers.
"""
from __future__ import annotations

import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import founding_seats as fs  # noqa: E402

BAR_RE = re.compile(r'data-founding-left="(\d+)"')


def main(root: str = ".") -> int:
    base = pathlib.Path(root)
    pages = [p for p in base.rglob("index.html") if ".git" not in p.parts]
    if not pages:
        print(f"FAIL: no index.html under {root!r} — nothing was checked, so this is "
              f"not a pass.", file=sys.stderr)
        return 1

    onpage = [(p, int(m.group(1))) for p in pages
              for m in [BAR_RE.search(p.read_text(encoding="utf-8", errors="ignore"))] if m]
    if not onpage:
        print(f"FAIL: no founding-seat bar found under {root!r}. It was removed once "
              f"already (Matthew noticed on 2026-09-15); this gate exists so the next "
              f"removal is not silent.", file=sys.stderr)
        return 1

    key = fs.key()
    if not key:
        print("FAIL: DODO_API_KEY not available, so the page's seat count could not be "
              "checked against Dodo. A gate that cannot compare must not report clean.",
              file=sys.stderr)
        return 1
    try:
        live = fs.CAP - fs.sold(key)
    except Exception as e:
        print(f"FAIL: could not read Dodo ({e}). Not a pass — the number on the page is "
              f"unverified, which is the state this gate exists to make visible.",
              file=sys.stderr)
        return 1

    bad = [(p, n) for p, n in onpage if n != live]
    if bad:
        for p, n in bad:
            print(f"FAIL: {p} says {n} of {fs.CAP} seats left; Dodo says {live}. "
                  f"Re-run: python3 scripts/founding_seats.py --inject", file=sys.stderr)
        return 1
    print(f"founding_seats_gate: ok — {len(onpage)} page(s) say {live} of {fs.CAP}, "
          f"and so does Dodo")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "."))
