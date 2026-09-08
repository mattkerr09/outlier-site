#!/usr/bin/env python3
"""Move every date a page publishes about itself — all of them, together.

Why this exists: on 2026-09-08 I edited six pages and updated the visible
"Last updated" line on some, the JSON-LD `dateModified` on others, and both on
none. A date lives in two places on 211 of this site's 226 pages, in three
visible formats and TWO JSON spacings, and I had been grepping for one spelling
of one of them. jsonld_dateline_gate now DETECTS that; this APPLIES the fix.

    python3 scripts/touch_dateline.py <page>...   # named pages
    python3 scripts/touch_dateline.py --changed   # every page git says I edited
    python3 scripts/touch_dateline.py --self-check

`datePublished` is never touched. A page was published when it was published;
only `dateModified` is a claim about the edit you just made.
"""
from __future__ import annotations

import datetime
import re
import subprocess
import sys

TODAY = datetime.date.today().isoformat()

#: Both spacings. 140 pages write one, 86 the other; a regex for either alone
#: reads clean over the rest of the site.
JSONLD = re.compile(r'("dateModified"\s*:\s*")(\d{4}-\d{2}-\d{2})(")')

#: Every visible shape in the corpus, measured rather than assumed:
#: 165 "Last updated YYYY-MM-DD", 44 "Updated YYYY-MM-DD", 3 "Updated Month D, YYYY".
VISIBLE = [
    re.compile(r'(Last updated )(\d{4}-\d{2}-\d{2})'),
    re.compile(r'(?<!Last )(Updated )(\d{4}-\d{2}-\d{2})'),
    re.compile(r'(?<!Last )(Updated )([A-Z][a-z]+ \d{1,2}, \d{4})'),
]
MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]


def long_form(iso: str) -> str:
    d = datetime.date.fromisoformat(iso)
    return f"{MONTHS[d.month - 1]} {d.day}, {d.year}"


#: _seo_build/scripts/render.py OWNS the /seo/ subtree: it preserves datePublished
#: across rebuilds and bumps dateModified only when the rendered content really
#: changes. Hand-editing a date there survives the next build (the renderer reads
#: the previous value back), so a manual touch would plant a wrong date that looks
#: maintained. Only 3 of the 155 baselined pages are under /seo/ — the backlog is
#: the hand-written corpus, which is exactly what this tool is for.
RENDERER_OWNED = "/seo/"


def touch(path: str, today: str = TODAY) -> dict:
    """-> {'jsonld': n, 'visible': n, 'changed': bool}. Never writes datePublished."""
    norm = "/" + path.replace("\\", "/").lstrip("./")
    if RENDERER_OWNED in norm:
        return {"jsonld": 0, "visible": 0, "changed": False, "skipped": "renderer-owned"}
    with open(path, encoding="utf-8") as f:
        s = before = f.read()

    pub_before = re.findall(r'"datePublished"\s*:\s*"(\d{4}-\d{2}-\d{2})"', s)

    s, n_json = JSONLD.subn(lambda m: m.group(1) + today + m.group(3), s)

    n_vis = 0
    for rx in VISIBLE:
        repl = (lambda m: m.group(1) + long_form(today)) if "," in rx.pattern \
            else (lambda m: m.group(1) + today)
        s, k = rx.subn(repl, s)
        n_vis += k

    pub_after = re.findall(r'"datePublished"\s*:\s*"(\d{4}-\d{2}-\d{2})"', s)
    assert pub_before == pub_after, f"{path}: datePublished MOVED — refusing to write"

    if s != before:
        with open(path, "w", encoding="utf-8") as f:
            f.write(s)
    return {"jsonld": n_json, "visible": n_vis, "changed": s != before}


def changed_pages() -> list[str]:
    out = subprocess.run(["git", "diff", "--name-only", "HEAD"],
                         capture_output=True, text=True).stdout.split()
    return [p for p in out if p.endswith("index.html")]


def self_check() -> int:
    """Every shape must move, and datePublished must not. Assert the plant landed."""
    import tempfile, os
    cases = {
        "no-space json + Last updated":
            '<p>Last updated 2020-01-01</p><script>{"datePublished":"2019-05-05","dateModified":"2020-01-01"}</script>',
        "spaced json + Updated iso":
            '<p>Updated 2020-01-01</p><script>{"datePublished": "2019-05-05", "dateModified": "2020-01-01"}</script>',
        "long visible form":
            '<p>Updated January 1, 2020</p><script>{"datePublished":"2019-05-05","dateModified":"2020-01-01"}</script>',
    }
    ok = True
    with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
        for name, body in cases.items():
            p = os.path.join(tmp, "index.html")
            open(p, "w", encoding="utf-8").write(body)
            r = touch(p, "2026-09-08")
            got = open(p, encoding="utf-8").read()
            moved_json = '"dateModified":"2026-09-08"' in got or '"dateModified": "2026-09-08"' in got
            moved_vis = "2026-09-08" in got or "September 8, 2026" in got
            kept_pub = "2019-05-05" in got
            stale = "2020-01-01" in got
            good = moved_json and moved_vis and kept_pub and not stale
            ok &= good
            print(f"  {'ok  ' if good else 'FAIL'} {name}: json={r['jsonld']} visible={r['visible']} "
                  f"published_kept={kept_pub} stale_left={stale}")
        # counter-control: a page with no dates must report zero, not crash
        p = os.path.join(tmp, "index.html")
        open(p, "w", encoding="utf-8").write("<p>nothing here</p>")
        r = touch(p, "2026-09-08")
        none_ok = r["jsonld"] == 0 and r["visible"] == 0 and not r["changed"]
        ok &= none_ok
        print(f"  {'ok  ' if none_ok else 'FAIL'} page with no dates: reports zero, writes nothing")
    print("self-check", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main(argv) -> int:
    if "--self-check" in argv:
        return self_check()
    paths = changed_pages() if "--changed" in argv else [a for a in argv[1:] if not a.startswith("--")]
    if not paths:
        print("nothing to do (no pages named, and git reports no edited index.html)")
        return 0
    for p in paths:
        r = touch(p)
        if r.get("skipped"):
            print(f"  {'SKIPPED':<16} {p}  (_seo_build/scripts/render.py owns this page)")
            continue
        state = "updated" if r["changed"] else "already current"
        print(f"  {state:<16} {p}  (jsonld x{r['jsonld']}, visible x{r['visible']})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
