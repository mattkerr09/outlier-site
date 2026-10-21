#!/usr/bin/env python3
"""The founding price switches off at the moment the offer ends, and nothing may show it after.

WHY. FOUNDINGOUTLIER (50% off Pro Lifetime, 24 uses) and FOUNDINGBUNDLE ($428) both end at the moment in
data/founding_offer.json. Dodo refuses an expired code, so a page that still shows the founding price after
that moment offers a price nobody can get, to exactly the person who was ready to buy. A switch that waits
for someone to remember the date is how that would happen, so the pages carry the date themselves:

  * every page that loads the shared offer bar (founding.js, served by the lead worker) has a dated guard
    right before it. From the end date on, the guard sets window.__kcFounding, the bar's own run-once flag,
    so the bar never mounts;
  * the product boxes' founders-price spans are `hidden` in the HTML and their reveal script shows them
    only before the end date AND while the worker reports seats left;
  * the home page's Lifetime card says $249 in the HTML itself. Its script applies the founders price only
    before the end date and while seats are left, so a visitor without JavaScript, and every crawler that
    reads raw HTML, gets the regular price.

Every date in a page is a literal and every one must equal "ends" in data/founding_offer.json.

WHAT FAILS
  always   a page loads founding.js without the dated guard right before it; a guard, a reveal script or
           the home card's script carries no end date or a different one; founding-price text a visitor
           reads in the raw HTML (outside hidden elements and scripts; JSON-LD counts, crawlers read it).
           A text file (llms.txt) may state the offer only on a line that names the end date.
  over     once the end date has passed, or with --live once the worker reports no seats left: ANY
           founding-offer markup left in a served file, hidden or not (the codes, the offer prices, the
           bar and its guard, the reveal spans, "founders price", "founding seats"). The switch keeps
           visitors safe at the moment itself; this makes the leftovers go. The hourly scheduled run
           checks the date with nobody pushing, so it goes red within the first hour after the offer ends
           if anything is left.

    python3 scripts/founding_offer_gate.py [root] [--live] [--now 2026-11-25T02:00:00Z]
    python3 scripts/founding_offer_gate.py --self-check
"""
from __future__ import annotations

import datetime as dt
import html.parser
import json
import pathlib
import re
import sys
import tempfile
import urllib.request

#: fewer pages than this means the scan broke, not that the site shrank (meta_gate probes an empty tree)
MIN_PAGES = 50
BAR = re.compile(r'<script\b[^>]*\bsrc="https://kerr-lead-agent\.kerrco\.workers\.dev/founding\.js"[^>]*>\s*</script>')
GUARD = re.compile(r'<script data-founding-ends="([^"]*)">(.*?)</script>\s*$', re.S)
PBOX_SCRIPT = re.compile(r"<script data-pbox-script>(.*?)</script>", re.S)
SCRIPT = re.compile(r"<script\b[^>]*>(.*?)</script>", re.S)
DATE_LIT = re.compile(r'Date\.parse\("([^"]+)"\)')
#: code, not pages: the gates and generators name the codes on purpose
SKIP_DIRS = {".git", ".github", "scripts", "node_modules"}
SERVED = {".html", ".htm", ".txt", ".xml", ".json", ".md"}
UA = {"User-Agent": "kerr-ops/1.0 (founding_offer_gate)"}


def load(root: pathlib.Path) -> dict:
    d = json.loads((root / "data" / "founding_offer.json").read_text(encoding="utf-8"))
    d["_end"] = dt.datetime.fromisoformat(d["ends"].replace("Z", "+00:00"))
    return d


def price_patterns(offer: dict) -> list[re.Pattern]:
    """What a founding PRICE looks like in text. 'Founders Lifetime' alone is the Dodo product's name, sold at
    $249 too, so it is not one; the founders price, the codes and the offer's own figures are."""
    pats = [re.compile(r"\bfounders?['’]?\s+price\b", re.I), re.compile(r"\bfounding\s+price\b", re.I),
            re.compile(r"\bfirst\s+\d+\s+buyers\b", re.I)]
    for o in offer["offers"]:
        pats.append(re.compile(r"\b" + re.escape(o["code"]) + r"\b"))
        pats += [re.compile(re.escape(p) + r"(?![\d])") for p in o.get("prices", [])]
    return pats


def leftover_patterns(offer: dict) -> list[re.Pattern]:
    """Once the offer is over, none of this may be left in a served file, hidden or not."""
    return price_patterns(offer) + [
        re.compile(r"kerr-lead-agent\.kerrco\.workers\.dev/founding"),   # the bar, and the seat reads
        re.compile(r"\bdata-pbox-founding\b"), re.compile(r"\bdata-founding\b"), re.compile(r"data-founding-ends"),
        re.compile(r"\bfounding\s+(?:seats?|offer)\b", re.I),
    ]


class Visible(html.parser.HTMLParser):
    """The text a visitor reads in the raw HTML: not inside a script/style/template/noscript, not inside an element
    carrying the hidden attribute. JSON-LD is kept: search engines and answer engines read it as the page's claims."""
    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
    SKIP = {"script", "style", "template", "noscript"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack: list[tuple[str, bool]] = []
        self.out: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in self.VOID:
            return
        a = dict(attrs)
        ld = tag == "script" and (a.get("type") or "").lower() == "application/ld+json"
        self.stack.append((tag, "hidden" in a or (tag in self.SKIP and not ld)))

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                return

    def handle_data(self, data):
        if not any(off for _, off in self.stack):
            self.out.append(data)


def visible_text(src: str) -> str:
    p = Visible()
    p.feed(src)
    p.close()
    return " ".join(p.out)


def served_files(root: pathlib.Path):
    for p in sorted(root.rglob("*")):
        rel = p.relative_to(root)
        if p.is_file() and p.suffix.lower() in SERVED and not (set(rel.parts) & SKIP_DIRS) \
                and rel.as_posix() != "data/founding_offer.json":
            yield rel, p.read_text(encoding="utf-8", errors="ignore")


def wiring(rel: str, src: str, ends: str) -> list[str]:
    bad = []
    for m in BAR.finditer(src):
        g = GUARD.search(src[:m.start()])
        if not g:
            bad.append(f"{rel}: loads founding.js with no dated guard right before it")
        elif g.group(1) != ends or DATE_LIT.findall(g.group(2)) != [ends] or "window.__kcFounding=1" not in g.group(2):
            bad.append(f"{rel}: the bar's guard ends {g.group(1)!r} / {DATE_LIT.findall(g.group(2))}, not {ends!r}")
    if "data-pbox-founding" in src:
        blocks = PBOX_SCRIPT.findall(src)
        if not blocks:
            bad.append(f"{rel}: founders-price spans with no reveal script")
        for b in blocks:
            if DATE_LIT.findall(b) != [ends] or "if(!(now<end))return;" not in b or b.find("now<end") > b.find("fetch("):
                bad.append(f"{rel}: the founders-price reveal is not dated {ends} before it asks the worker")
    for b in SCRIPT.findall(src):
        if "[data-lifetime-card]" in b and DATE_LIT.findall(b) != [ends]:
            bad.append(f"{rel}: the Lifetime card's script is not dated {ends}")
    return bad


def seats_left(offer: dict) -> bool:
    req = urllib.request.Request(offer["worker"], headers=UA)
    with urllib.request.urlopen(req, timeout=20) as r:
        d = json.loads(r.read().decode())
    if not isinstance(d.get("left"), int):
        raise ValueError(f"the worker's answer has no seat count: {d}")
    print(f"worker: {d.get('code')} left={d['left']} of={d.get('of')} soldOut={d.get('soldOut')}")
    return d["left"] > 0 and not d.get("soldOut")


def check(root: pathlib.Path, now: dt.datetime, live: bool) -> int:
    files = list(served_files(root))
    pages = [f for f in files if f[0].suffix.lower() in (".html", ".htm")]
    print(f"founding_offer_gate: examined {len(pages)} page(s), {len(files)} served file(s)")
    if len(pages) < MIN_PAGES or not (root / "index.html").is_file():
        print(f"FAIL: {len(pages)} page(s) is fewer than {MIN_PAGES}, or there is no index.html. The scan is "
              f"likelier broken than the site. Not reporting clean.")
        return 1
    try:
        offer = load(root)
    except (OSError, ValueError, KeyError) as e:
        print(f"FAIL: data/founding_offer.json is missing or unreadable ({e}). It is the one source for the end date.")
        return 1
    ends = offer["ends"]
    over, why = now >= offer["_end"], f"the end date {ends} has passed"
    if live and not over:
        try:
            if not seats_left(offer):
                over, why = True, "the worker reports no founding seats left"
        except Exception as e:   # noqa: BLE001 — any failure to read is a failure to know
            print(f"FAIL: could not read the founding worker ({e}). Whether seats are left is unknown, not 'yes'.")
            return 1
    bad: list[str] = []
    if over:
        print(f"the founding offer is OVER: {why}")
        for rel, src in files:
            hits = sorted({m.group(0) for p in leftover_patterns(offer) for m in p.finditer(src)})
            if hits:
                bad.append(f"{rel}: still carries {', '.join(hits[:6])}")
    else:
        print(f"the founding offer is on until {ends}; checking the switch is wired and nothing static shows the price")
        pats, day = price_patterns(offer), ends[:10]
        for rel, src in files:
            if rel.suffix.lower() in (".html", ".htm"):
                bad += wiring(rel.as_posix(), src, ends)
                hits = sorted({m.group(0) for p in pats for m in p.finditer(visible_text(src))})
                if hits:
                    bad.append(f"{rel}: shows {', '.join(hits)} in the HTML itself; reveal it from a dated script instead")
            else:
                for n, line in enumerate(src.split("\n"), 1):
                    hits = sorted({m.group(0) for p in pats for m in p.finditer(line)})
                    if hits and day not in line:
                        bad.append(f"{rel}:{n}: states {', '.join(hits)} on a line that does not name the end date {day}")
    if bad:
        print(f"\nFAIL ({len(bad)}):")
        for b in bad[:60]:
            print(f"  {b}")
        if len(bad) > 60:
            print(f"  … and {len(bad) - 60} more")
        if over:
            print("\nTake the founding offer off: the bar and its guard, the reveal spans and script, the card's founders "
                  "branch, and the llms.txt line; then any prose that still promises founding seats.")
        return 1
    print("PASS: " + ("nothing founding is left" if over else f"the switch is wired to {ends} and nothing static shows the price"))
    return 0


def self_check() -> int:
    """The gate must fail on each way the switch can be missing, and pass on a wired page and a clean one."""
    ends = "2026-11-25T01:26:00Z"
    guard = (f'<script data-founding-ends="{ends}">(function(){{var end=Date.parse("{ends}"),now=Date.now();'
             f'if(!(now<end))window.__kcFounding=1;}})();</script>\n')
    bar = '<script src="https://kerr-lead-agent.kerrco.workers.dev/founding.js" defer></script>\n'
    reveal = ('<script data-pbox-script>(function(){var m=1;var end=Date.parse("%s"),now=Date.now();'
              'if(!(now<end))return;fetch("x")})();</script>\n')
    span = '<p>$249<span data-pbox-founding hidden> founders price $124.50</span></p>\n'
    card = ('<div data-lifetime-card>$249</div><script>var c=document.querySelector("[data-lifetime-card]");'
            'var end=Date.parse("%s");</script>\n')
    offer = json.dumps({"ends": ends, "worker": "http://127.0.0.1:9/", "offers": [
        {"code": "FOUNDINGOUTLIER", "prices": ["$124.50", "$31.13"]}, {"code": "FOUNDINGBUNDLE", "prices": ["$428"]}]})
    before, after = dt.datetime(2026, 11, 1, tzinfo=dt.timezone.utc), dt.datetime(2026, 11, 25, 2, tzinfo=dt.timezone.utc)
    wired = guard + bar + span + reveal % ends
    clean = "<p>Pro Lifetime: $249 once.</p>\n"
    cases = [  # (name, home page, other page, llms line, when, expected exit)
        ("wired, before the end", wired + card % ends, wired, f"founders price $124.50 until {ends[:10]}", before, 0),
        ("bar with no guard", bar + card % ends, wired, "", before, 1),
        ("guard with another date", guard.replace(ends, "2026-12-01T00:00:00Z") + bar + card % ends, wired, "", before, 1),
        ("reveal with no date", wired + card % ends, guard + bar + span + reveal.replace('if(!(now<end))return;', '') % ends, "", before, 1),
        ("card script not dated", wired + card % "2027-01-01T00:00:00Z", wired, "", before, 1),
        ("visible founders price", wired + card % ends + "<p>Buy for $124.50</p>", wired, "", before, 1),
        ("visible code in JSON-LD", wired + card % ends + '<script type="application/ld+json">{"d":"FOUNDINGOUTLIER"}</script>', wired, "", before, 1),
        ("undated llms line", wired + card % ends, wired, "the first 25 buyers pay $124.50", before, 1),
        ("bundle price shown", wired + card % ends + "<p>All three for $428</p>", wired, "", before, 1),
        ("leftovers after the end", wired + card % ends, wired, f"founders price $124.50 until {ends[:10]}", after, 1),
        ("hidden span left after the end", clean, clean + span, "", after, 1),
        ("clean after the end", clean, clean, "Pro Lifetime: $249 once.", after, 0),
    ]
    wrong = []
    for name, home, other, llms, when, want in cases:
        with tempfile.TemporaryDirectory() as t:
            r = pathlib.Path(t)
            (r / "data").mkdir()
            (r / "data" / "founding_offer.json").write_text(offer)
            (r / "index.html").write_text(home)
            (r / "llms.txt").write_text(llms + "\n")
            for i in range(MIN_PAGES):
                (r / f"p{i}.html").write_text(other)
            import contextlib, io
            with contextlib.redirect_stdout(io.StringIO()):
                got = check(r, when, live=False)
        print(f"  {'ok ' if got == want else 'BAD'} {name}: exit {got} (want {want})")
        if got != want:
            wrong.append(name)
    if wrong:
        print(f"SELF-CHECK FAILED: {wrong}")
        return 1
    print(f"self-check: {len(cases)} cases, the gate fails on every missing switch and passes the wired and clean trees")
    return 0


def main(argv: list[str]) -> int:
    if "--self-check" in argv:
        return self_check()
    now = dt.datetime.now(dt.timezone.utc)
    if "--now" in argv:
        now = dt.datetime.fromisoformat(argv[argv.index("--now") + 1].replace("Z", "+00:00"))
    args = [a for i, a in enumerate(argv) if not a.startswith("--") and (i == 0 or argv[i - 1] != "--now")]
    return check(pathlib.Path(args[0] if args else "."), now, live="--live" in argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
