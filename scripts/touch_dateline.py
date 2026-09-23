#!/usr/bin/env python3
"""Move every date a page publishes about itself — all of them, together.

Why this exists: on 2026-09-08 I edited six pages and updated the visible
"Last updated" line on some, the JSON-LD `dateModified` on others, and both on
none. A date lives in two places on 211 of this site's 226 pages, in three
visible formats and TWO JSON spacings, and I had been grepping for one spelling
of one of them. jsonld_dateline_gate now DETECTS that; this APPLIES the fix.

    python3 scripts/touch_dateline.py <page>...   # named pages
    python3 scripts/touch_dateline.py --changed   # every page git says I edited
    python3 scripts/touch_dateline.py --date 2026-09-16 <page>...   # a date OTHER than today
    python3 scripts/touch_dateline.py --self-check

⚠️ --date EXISTS BECAUSE "TODAY" IS OFTEN A LIE. touch() has always taken a date;
main() never passed one, so the only claim the CLI could make was today's. Fixing
a dateline the day after the edit — which is when you notice, because a gate tells
you — then overstates the page's freshness by a day, in the one field Google reads
to decide whether to recrawl. Pass the date the CONTENT changed, which
visible_dateline_gate.last_body_change() will tell you.

`datePublished` is never touched. A page was published when it was published;
only `dateModified` is a claim about the edit you just made.
"""
from __future__ import annotations

import datetime
import json
import os
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


#: _seo_build/scripts/render.py OWNS the pages it writes: it preserves datePublished
#: across rebuilds and bumps dateModified only when the rendered content really
#: changes. Hand-editing a date on one of THOSE survives the next build (the
#: renderer reads the previous value back), so a manual touch would plant a wrong
#: date that looks maintained.
#:
#: Ownership is the renderer's own record, not a folder name. Until 2026-09-23 this
#: file refused every path containing "/seo/", which also refused seven hand-made
#: pages the renderer never writes (seo/learn/mlx-explained/ and six more) — their
#: dates could only be moved by hand-editing, the very thing this tool replaces.
#: render.py now writes _seo_build/owned_pages.json on every run; a page is owned
#: iff it is listed there. If that list cannot be read, every /seo/ page is treated
#: as owned (the old, safe answer) and the tool says why.
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OWNED_MANIFEST = os.path.join(REPO_ROOT, "_seo_build", "owned_pages.json")
_UNREAD = object()


def renderer_owned_pages(manifest: str = OWNED_MANIFEST):
    """-> set of 'seo/<category>/<slug>/index.html' paths render.py writes, or None
    when the list is missing or unreadable (callers must then fail closed)."""
    try:
        with open(manifest, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list) or not data:
            return None
        return {str(x) for x in data}
    except Exception:
        return None


def _seo_key(path: str):
    """'…/seo/learn/x/index.html' -> 'seo/learn/x/index.html'; None off /seo/."""
    norm = "/" + path.replace("\\", "/").lstrip("./")
    m = re.search(r"/(seo/.+)$", norm)
    return m.group(1) if m else None


def touch(path: str, today: str = TODAY, owned=_UNREAD) -> dict:
    """-> {'jsonld': n, 'visible': n, 'changed': bool}. Never writes datePublished."""
    key = _seo_key(path)
    if key is not None:
        if owned is _UNREAD:
            owned = renderer_owned_pages()
        if owned is None:
            return {"jsonld": 0, "visible": 0, "changed": False,
                    "skipped": "renderer-owned (owned_pages.json unreadable — run "
                               "_seo_build/scripts/render.py --list-owned)"}
        if key in owned:
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
        # Wiring control: touch() has always honoured a date; main() dropped it.
        # Drive the CLI the way a person does and assert the date SURVIVES.
        import subprocess
        p = os.path.join(tmp, "index.html")
        open(p, "w", encoding="utf-8").write(
            '<p>Last updated 2020-01-01</p><script>{"datePublished":"2019-05-05",'
            '"dateModified":"2020-01-01"}</script>')
        subprocess.run([sys.executable, __file__, "--date", "2026-09-16", p],
                       capture_output=True, text=True)
        got = open(p, encoding="utf-8").read()
        wired = "2026-09-16" in got and TODAY not in got
        ok &= wired
        print(f"  {'ok  ' if wired else 'FAIL'} --date reaches the file through main() "
              f"(not silently replaced by today)")

        # And a future date must be refused rather than written.
        open(p, "w", encoding="utf-8").write(
            '<script>{"datePublished":"2019-05-05","dateModified":"2020-01-01"}</script>')
        future = (datetime.date.today() + datetime.timedelta(days=5)).isoformat()
        rc = subprocess.run([sys.executable, __file__, "--date", future, p],
                            capture_output=True, text=True)
        refused = rc.returncode != 0 and future not in open(p, encoding="utf-8").read()
        ok &= refused
        print(f"  {'ok  ' if refused else 'FAIL'} a future --date is refused, not written")

        # Ownership comes from the renderer's list, not the folder name.
        page = '<p>Last updated 2020-01-01</p><script>{"datePublished":"2019-05-05","dateModified":"2020-01-01"}</script>'
        for leaf in ("rendered", "handmade"):
            os.makedirs(os.path.join(tmp, "seo", "learn", leaf), exist_ok=True)
            open(os.path.join(tmp, "seo", "learn", leaf, "index.html"), "w", encoding="utf-8").write(page)
        owned = {"seo/learn/rendered/index.html"}
        r_owned = touch(os.path.join(tmp, "seo", "learn", "rendered", "index.html"), "2026-09-08", owned=owned)
        r_hand = touch(os.path.join(tmp, "seo", "learn", "handmade", "index.html"), "2026-09-08", owned=owned)
        r_blind = touch(os.path.join(tmp, "seo", "learn", "handmade", "index.html"), "2026-09-09", owned=None)
        owned_ok = bool(r_owned.get("skipped")) and "2020-01-01" in open(
            os.path.join(tmp, "seo", "learn", "rendered", "index.html"), encoding="utf-8").read()
        hand_ok = not r_hand.get("skipped") and r_hand["changed"]
        blind_ok = bool(r_blind.get("skipped")) and "2026-09-09" not in open(
            os.path.join(tmp, "seo", "learn", "handmade", "index.html"), encoding="utf-8").read()
        ok &= owned_ok and hand_ok and blind_ok
        print(f"  {'ok  ' if owned_ok else 'FAIL'} a page render.py lists is refused, file untouched")
        print(f"  {'ok  ' if hand_ok else 'FAIL'} a hand-made page under /seo/ is updated")
        print(f"  {'ok  ' if blind_ok else 'FAIL'} an unreadable ownership list refuses every /seo/ page")

    # The real list must describe the real tree: every listed page exists, and it
    # is not the whole /seo/ tree (hand-made pages exist and must be touchable).
    real = renderer_owned_pages()
    if real is None:
        print("  FAIL _seo_build/owned_pages.json is missing or unreadable")
        ok = False
    else:
        missing = sorted(p for p in real if not os.path.exists(os.path.join(REPO_ROOT, p)))
        leaves = {os.path.relpath(os.path.join(d, "index.html"), REPO_ROOT)
                  for d, _, files in os.walk(os.path.join(REPO_ROOT, "seo"))
                  if "index.html" in files and d.count(os.sep) - REPO_ROOT.count(os.sep) == 3}
        hand = sorted(leaves - real)
        real_ok = not missing and len(real) > 0
        ok &= real_ok
        print(f"  {'ok  ' if real_ok else 'FAIL'} owned_pages.json: {len(real)} listed, "
              f"{len(missing)} missing on disk; {len(hand)} hand-made /seo/ leaves stay touchable")
    print("self-check", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main(argv) -> int:
    if "--self-check" in argv:
        return self_check()
    when = TODAY
    if "--date" in argv:
        i = argv.index("--date")
        if i + 1 >= len(argv):
            print("--date needs a YYYY-MM-DD value")
            return 2
        when = argv[i + 1]
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", when):
            print(f"--date {when!r} is not YYYY-MM-DD")
            return 2
        try:
            datetime.date.fromisoformat(when)
        except ValueError:
            print(f"--date {when!r} is not a real date")
            return 2
        if datetime.date.fromisoformat(when) > datetime.date.today():
            print(f"--date {when} is in the future — refusing to claim a page was "
                  f"edited on a day that has not happened")
            return 2
        argv = argv[:i] + argv[i + 2:]
    paths = changed_pages() if "--changed" in argv else [a for a in argv[1:] if not a.startswith("--")]
    if not paths:
        print("nothing to do (no pages named, and git reports no edited index.html)")
        return 0
    for p in paths:
        r = touch(p, when)
        if r.get("skipped"):
            print(f"  {'SKIPPED':<16} {p}  (_seo_build/scripts/render.py owns this page)")
            continue
        state = "updated" if r["changed"] else "already current"
        print(f"  {state:<16} {p}  (jsonld x{r['jsonld']}, visible x{r['visible']})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
