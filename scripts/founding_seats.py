#!/usr/bin/env python3
"""How many founding seats are left, counted from Dodo — never typed.

    python3 scripts/founding_seats.py            # print the count as JSON
    python3 scripts/founding_seats.py --inject   # write it into index.html

WHY THIS EXISTS. Matthew noticed on 2026-09-15 that outlier.host had no founding-seat
bar at all. Putting one back means putting a NUMBER on the page, and a seat count typed
by hand is wrong the moment the next seat sells — a scarcity claim that drifts is worse
than no claim, because it is checkable and a buyer who checks finds us overstating.

So the number is DERIVED. This counts succeeded payments whose product_cart contains the
founding product and subtracts from the cap. The list endpoint does NOT carry
product_cart (measured 2026-09-15 — it returns payment_id, total_amount, status,
created_at and no product attribution), so each succeeded payment is fetched
individually. With single-digit order counts that is cheap and exact; if it ever is not,
page it, do not guess.

It counts QUANTITY, not payments: one order for two seats is two seats.

IT ALSO COUNTS COMPS, AND THAT IS THE WHOLE JUDGEMENT. Measured 2026-09-15: the founding
product has TWO succeeded orders, not one — pay_0Nmu3FOXHB501N4C2MGzp at $124.50 on
09-04 (a real sale) and pay_0NltXCjE2joH5KpVHa7cM at $0.00 on 08-21 (a 100%-off comp).
Counting paid sales alone gives "24 left"; counting seats a person actually holds gives
23. A comped founding licence is a seat that is gone, so the bar says 23.

The direction of the error is the reason: understating availability costs nothing and can
always be honoured, while overstating tells a buyer a seat exists that does not, on the
one page where they are being asked to hurry. If the business means paid-only, change CAP
or filter on total_amount here — deliberately, in this file, not by typing a number into
a page.
"""
from __future__ import annotations

import json
import os
import pathlib
import re
import sys
import urllib.request

FOUNDING_PRODUCT = "pdt_0Nlgdu1f0s30YekSmpGwA"
CAP = 25
API = "https://live.dodopayments.com"


def key() -> str:
    p = pathlib.Path.home() / ".dodo/secrets.env"
    if p.exists():
        for line in p.read_text().splitlines():
            if line.startswith("DODO_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return os.environ.get("DODO_API_KEY", "")


def _get(url: str, k: str):
    r = urllib.request.Request(url, headers={"Authorization": f"Bearer {k}",
                                             "User-Agent": "kerr-ops/1.0"})
    return json.loads(urllib.request.urlopen(r, timeout=30).read())


def sold(k: str) -> int:
    n = 0
    page = 0
    while True:
        d = _get(f"{API}/payments?page_size=100&page_number={page}", k)
        items = d.get("items") or d.get("data") or []
        if not items:
            break
        for it in items:
            if it.get("status") != "succeeded":
                continue
            detail = _get(f"{API}/payments/{it['payment_id']}", k)
            for line in detail.get("product_cart") or []:
                if line.get("product_id") == FOUNDING_PRODUCT:
                    n += int(line.get("quantity") or 1)
        if len(items) < 100:
            break
        page += 1
    return n


BAR_RE = re.compile(r'<div class="founding-bar"[^>]*>.*?</div>', re.S)


def bar_html(left: int, total: int) -> str:
    return (f'<div class="founding-bar" data-founding-left="{left}">'
            f'<strong>{left} of {total}</strong> founding seats left '
            f'&middot; lifetime, one payment &middot; '
            f'<a href="#pricing">see what it includes</a></div>')


def main(argv: list[str]) -> int:
    k = key()
    if not k:
        print("DODO_API_KEY not found — refusing to emit a seat count from nothing.",
              file=sys.stderr)
        return 2
    s = sold(k)
    left = CAP - s
    if not (0 <= left <= CAP):
        print(f"REFUSING: derived {left} of {CAP} (sold {s}) — outside the cap, so the "
              f"count or the cap is wrong. A scarcity number is not guessed.", file=sys.stderr)
        return 1
    if "--inject" in argv:
        p = pathlib.Path(__file__).resolve().parent.parent / "index.html"
        html = p.read_text(encoding="utf-8")
        if BAR_RE.search(html):
            html = BAR_RE.sub(bar_html(left, CAP), html, count=1)
        else:
            # The body tag carries attributes on this page, so match it rather
            # than assuming "<body>" appears literally.
            m = re.search(r"<body[^>]*>", html)
            if not m:
                print("no <body> tag found — refusing to guess an insertion point",
                      file=sys.stderr)
                return 1
            i = m.end()
            html = html[:i] + "\n" + bar_html(left, CAP) + html[i:]
        p.write_text(html, encoding="utf-8")
        print(f"injected: {left} of {CAP} founding seats left (sold {s})")
        return 0
    print(json.dumps({"sold": s, "cap": CAP, "left": left}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
