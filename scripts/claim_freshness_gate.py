#!/usr/bin/env python3
"""No claim about another company's price, plan or feature may sit unread for long.

    python3 scripts/claim_freshness_gate.py .                 # the gate (CI and the offline runner)
    python3 scripts/claim_freshness_gate.py . --list          # every claim set: page, rival, date, age
    python3 scripts/claim_freshness_gate.py --self-check      # prove it can fail
    python3 scripts/claim_freshness_gate.py . --today 2026-12-01   # judge the site as of another day

THE RULE (CEO, 2026-10-20). A competitor price or feature claim over 45 days old blocks the deploy; over 30 days
it warns. Every /vs/ and /best/ page that quotes a rival's price, plan or feature carries a checked-on date for
each set of claims it makes. Docket's verify_claim_freshness.py is the same rule over its own claim table; this is
the version for a site whose claims live in hand-written HTML rather than in a table.

THE MARKUP. A claim set is any element carrying `data-claims-checked="YYYY-MM-DD"`, and its text must say that
date to the reader, because a date only the machine can see is not a promise made to anyone:

    <span class="byline" data-claims-checked="2026-10-19" data-claims-set="Cline">Cline prices and plans checked 2026-10-19</span>

`data-claims-set` names the rival(s) the date covers. A page that talks about two rivals read on two different days
carries two elements. The date means ONE thing: on that day the rival's own public page was read and every price,
plan and limit stated in this claim set matched it. Moving the date without reading the page is the one way to
defeat this gate, and no script can see it; the comparison pages cite the page they were read against.

WHAT FAILS (exit 1)
  stale       a claim set whose date is more than 45 days before today (UTC)
  undated     a page that quotes a rival's price, plan or feature and carries no claim set
  malformed   a date that is not a real YYYY-MM-DD, is in the future, or is not written in the element's text
  stale-text  a visible "checked / verified / as of <date>" statement about a rival, outside any claim set, whose
              date is more than 45 days old. The attribute cannot launder a sentence that still says July.
  exempt      an exempt page that now quotes a rival's price or carries a rival comparison (the list cannot hide a
              page), a listed page that is gone, or a list that grew past EXEMPT_MAX
WHAT WARNS (exit 0): a claim set between 30 and 45 days old.

WHICH PAGES "QUOTE A RIVAL". Default-deny: every page under vs/, best/ and seo/vs/ needs a claim set, unless it is
in claim_freshness_exempt.json (pages about open-weight model families, file formats and concepts, with the
reason written down). Proximity to a vendor name is not used; it was tried by rival_price_source_gate and produced
571 findings, none of them useful. A page is a rival-claim page when ANY of these holds, none of which needs a name
list that rots:
  price   a money figure in its visible text that is not one of Kerr's own prices (product-facts.json)
  table   a table that names Outlier and something else on one axis: that table IS the comparison
  slug    vs/outlier-vs-<rival>/, a page whose whole subject is one rival
  seo     a page the renderer writes under seo/vs/ (_seo_build/owned_pages.json): "Outlier vs <category>" pages whose
          categories are competitors.csv rows, dated per category in that file. A hand-made page there is judged
          like any other (price, table, slug) and is default-deny too

    A GATE THAT CANNOT FAIL ON ITS OWN BUG IS A COMMENT. --self-check builds a tree with a fresh, an aging, a stale
    and an undated page (and the malformed, hidden-date, exempt and stale-text cases) and demands each verdict. The
    default run does it first, so a run that proves nothing cannot print PASS.
"""
from __future__ import annotations

import datetime as dt
import json
import re
import sys
import tempfile
from html.parser import HTMLParser
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

#: The one place the rule's numbers live. A claim set older than FAIL_DAYS stops the deploy.
WARN_DAYS = 30
FAIL_DAYS = 45
#: Vacuity floor. The site has ~85 pages in scope; a scan that finds fewer than this looked at the wrong tree.
MIN_PAGES = 40
#: The exempt list may shrink. Adding a page to it silences this gate for that page, so the size is pinned.
EXEMPT_MAX = 4
EXEMPT_FILE = HERE / "claim_freshness_exempt.json"

SCOPE_GLOBS = ("vs/*/index.html", "best/*/index.html", "seo/vs/*/index.html")
#: Hub pages (vs/index.html ...) list and describe the pages below them; they are checked for prices only.
HUB_FILES = ("vs/index.html", "best/index.html", "seo/vs/index.html")

MONEY = re.compile(r"[$€£]\d[\d,]*(?:\.\d+)?")
ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")
MONTHS = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october",
          "november", "december"]
_MONTH_RE = "|".join(m.capitalize() for m in MONTHS)
#: "checked 2026-07-23", "as of July 2026", "verified on 23 July 2026", "read on October 19, 2026"
STAMP = re.compile(
    r"(?i)\b(?:re-?checked|checked|verified|re-?read|as of|retrieved|accessed|last checked)\s+(?:on\s+)?"
    r"(?P<d>\d{4}-\d{2}-\d{2}"
    rf"|\d{{1,2}}\s+(?:{_MONTH_RE})\s+\d{{4}}"
    rf"|(?:{_MONTH_RE})\s+\d{{1,2}},?\s+\d{{4}}"
    rf"|(?:{_MONTH_RE})\s+\d{{4}})")
#: A dated sentence that is about OUR measurements or OUR price is not a claim about a rival.
OURS_WORDS = re.compile(r"(?i)\b(?:outlier|measured|benchmark|swe-bench|humaneval|mmlu|we|our)\b|\bi (?:ran|measured|tested)\b")

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
SKIP_TEXT = {"script", "style", "noscript", "head", "template", "svg"}
CHROME = {"nav", "footer"}


def parse_date(text: str) -> dt.date | None:
    """An ISO date, '23 July 2026', 'July 23, 2026' or 'July 2026' (the 1st: the oldest the claim could be)."""
    t = text.strip().replace(",", "")
    try:
        if ISO.match(t):
            return dt.date.fromisoformat(t)
        parts = t.split()
        if len(parts) == 3 and parts[1].lower() in MONTHS:
            return dt.date(int(parts[2]), MONTHS.index(parts[1].lower()) + 1, int(parts[0]))
        if len(parts) == 3 and parts[0].lower() in MONTHS:
            return dt.date(int(parts[2]), MONTHS.index(parts[0].lower()) + 1, int(parts[1]))
        if len(parts) == 2 and parts[0].lower() in MONTHS:
            return dt.date(int(parts[1]), MONTHS.index(parts[0].lower()) + 1, 1)
    except ValueError:
        return None
    return None


def says_date(text: str, d: dt.date) -> bool:
    """Does the element's visible text state date `d` in a form a reader recognises?"""
    low = text.lower()
    forms = {d.isoformat(), f"{d.day} {MONTHS[d.month - 1]} {d.year}", f"{MONTHS[d.month - 1]} {d.day}, {d.year}",
             f"{MONTHS[d.month - 1]} {d.day} {d.year}"}
    return any(f in low for f in forms)


class Page(HTMLParser):
    """One pass: visible text (chrome, scripts, styles out), text outside code/pre for money, claim-set elements."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[str] = []
        self.text: list[str] = []
        self.prose: list[str] = []          # visible text outside <code>/<pre>
        self.sets: list[dict] = []
        self._open: list[dict] = []         # claim-set elements still open

    def _skipping(self) -> bool:
        return any(t in SKIP_TEXT or t in CHROME for t in self.stack)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag not in VOID:
            self.stack.append(tag)
        if "data-claims-checked" in a:
            rec = {"date": (a.get("data-claims-checked") or "").strip(), "label": (a.get("data-claims-set") or "").strip(),
                   "text": [], "depth": len(self.stack), "tag": tag}
            if tag in VOID:
                self.sets.append({**rec, "text": ""})
            else:
                self._open.append(rec)
        if tag == "br":
            self._emit(" ")

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        # close the nearest matching open tag (tolerates the sloppy markup hand-written pages carry)
        if tag in self.stack:
            while self.stack:
                top = self.stack.pop()
                while self._open and self._open[-1]["depth"] > len(self.stack):
                    rec = self._open.pop()
                    rec["text"] = re.sub(r"\s+", " ", "".join(rec["text"])).strip()
                    self.sets.append(rec)
                if top == tag:
                    break

    def _emit(self, s: str) -> None:
        if self._skipping():
            return
        self.text.append(s)
        if "code" not in self.stack and "pre" not in self.stack:
            self.prose.append(s)
        for rec in self._open:
            rec["text"].append(s)

    def handle_data(self, data):
        self._emit(data)

    def close(self):
        super().close()
        while self._open:
            rec = self._open.pop()
            rec["text"] = re.sub(r"\s+", " ", "".join(rec["text"])).strip()
            self.sets.append(rec)


def read_page(path: Path) -> Page:
    p = Page()
    p.feed(path.read_text(encoding="utf-8", errors="replace"))
    p.close()
    return p


def squash(parts: list[str]) -> str:
    return re.sub(r"\s+", " ", "".join(parts)).strip()


def ours() -> set:
    """Kerr's own prices (Outlier's, its siblings', pay-in-4 quarters) from the other rival-price gate, so the two
    gates cannot disagree about which dollar figure is ours."""
    from rival_price_in_source_gate import OURS  # noqa: E402
    return set(OURS)


def cells(row: str) -> list[str]:
    import html
    return [html.unescape(re.sub(r"<[^>]+>", " ", c)).strip()
            for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, re.S | re.I)]


def has_comparison_table(raw: str) -> bool:
    """A table that names Outlier on one axis and something else on the same axis is the comparison itself."""
    for tbl in re.findall(r"<table.*?</table>", raw, re.S | re.I):
        rows = re.findall(r"<tr.*?</tr>", tbl, re.S | re.I)
        if len(rows) < 2:
            continue
        head = cells(rows[0])
        firsts = [(cells(r) or [""])[0] for r in rows[1:]]
        for axis in (head[1:], firsts):
            named = [c for c in axis if c]
            if any(re.search(r"(?i)\boutlier\b", c) for c in named) and any(
                    not re.search(r"(?i)\boutlier\b", c) for c in named):
                return True
    return False


def rival_figures(prose: str, mine: set) -> list[str]:
    out = []
    for m in MONEY.finditer(prose):
        fig = m.group(0).rstrip(",")
        if fig not in mine:
            out.append(fig)
    return out


def load_exempt() -> dict:
    if not EXEMPT_FILE.exists():
        return {}
    d = json.loads(EXEMPT_FILE.read_text(encoding="utf-8"))
    return {k: v for k, v in d.items() if not k.startswith("_")}


def pages_in_scope(root: Path) -> list[Path]:
    found = []
    for g in SCOPE_GLOBS:
        found += sorted(root.glob(g))
    return found


def owned_pages(root: Path) -> set:
    """Pages the seo renderer writes. Unreadable manifest: every seo/vs page counts as generated (the safe answer)."""
    m = root / "_seo_build" / "owned_pages.json"
    try:
        return set(json.loads(m.read_text(encoding="utf-8")))
    except (OSError, ValueError):
        return {p.relative_to(root).as_posix() for p in root.glob("seo/vs/*/index.html")}


def why_rival_page(rel: str, raw: str, prose: str, mine: set, owned: set) -> list[str]:
    """The reasons this page counts as quoting a rival; empty means it does not (and may be exempt)."""
    why = []
    figs = rival_figures(prose, mine)
    if figs:
        why.append(f"price {figs[0]}" + (f" +{len(figs) - 1}" if len(figs) > 1 else ""))
    if has_comparison_table(raw):
        why.append("comparison table")
    if re.match(r"vs/outlier-vs-[^/]+/index\.html$", rel):
        why.append("slug outlier-vs-<rival>")
    if rel.startswith("seo/vs/") and rel in owned:
        why.append("generated seo/vs comparison")
    return why


def stale_texts(text: str, set_texts: list[str], today: dt.date) -> list[tuple]:
    """Visible 'checked/as of <date>' statements about a rival that are old, outside every claim set."""
    for st in set_texts:
        if st:
            text = text.replace(st, " ")
    out = []
    for m in STAMP.finditer(text):
        d = parse_date(m.group("d"))
        if d is None:
            continue
        age = (today - d).days
        if age <= FAIL_DAYS:
            continue
        # the clause the statement lives in: back to the last sentence/clause break, forward to the end of the date
        start = max(text.rfind(". ", 0, m.start()), text.rfind("; ", 0, m.start()), text.rfind(": ", 0, m.start()), 0)
        clause = text[start:m.end() + 80]
        if OURS_WORDS.search(clause):
            continue
        out.append((age, m.group(0), text[max(0, m.start() - 70):m.end() + 40].strip()))
    return out


def scan(root: Path, today: dt.date, exempt: dict | None = None, exempt_max: int | None = None) -> dict:
    """Judge every page. Returns {'sets': [...], 'pages': n, 'rival_pages': n, 'warn': [...], 'fail': [...]}."""
    exempt = load_exempt() if exempt is None else exempt
    exempt_max = EXEMPT_MAX if exempt_max is None else exempt_max
    mine = ours()
    owned = owned_pages(root)
    res = {"sets": [], "pages": 0, "rival_pages": 0, "warn": [], "fail": [], "why": {}}
    scoped = pages_in_scope(root)
    hubs = [root / h for h in HUB_FILES if (root / h).is_file()]
    seen_rel = set()

    if len(exempt) > exempt_max:
        res["fail"].append(f"exempt: claim_freshness_exempt.json lists {len(exempt)} pages, pinned at {exempt_max}. "
                           f"A page was ADDED, which silences this gate for it. Date the page instead, or change "
                           f"EXEMPT_MAX in the same commit and say why.")

    for path in scoped + hubs:
        rel = path.relative_to(root).as_posix()
        seen_rel.add(rel)
        is_hub = rel in HUB_FILES
        res["pages"] += 1
        raw = path.read_text(encoding="utf-8", errors="replace")
        pg = read_page(path)
        prose = squash(pg.prose)
        text = squash(pg.text)
        if is_hub:
            figs = rival_figures(prose, mine)
            need = bool(figs)
            why = [f"price {figs[0]}"] if figs else []
        else:
            why = why_rival_page(rel, raw, prose, mine, owned)
            need = True                                  # default-deny: a page here needs a date unless exempt
        page_sets = []
        for s in pg.sets:
            d = s["date"]
            label = s["label"] or "(unnamed)"
            where = f"{rel} [{label}]"
            dd = parse_date(d) if ISO.match(d) else None
            if dd is None:
                res["fail"].append(f"malformed  {where}: data-claims-checked={d!r} is not a real YYYY-MM-DD date")
                continue
            if dd > today:
                res["fail"].append(f"malformed  {where}: {d} is in the future (today is {today})")
                continue
            if not says_date(s["text"], dd):
                res["fail"].append(f"malformed  {where}: the element's text {s['text'][:60]!r} does not state {d}, "
                                   f"so the reader cannot see the date the machine reads")
                continue
            age = (today - dd).days
            rec = {"page": rel, "label": label, "date": d, "age": age}
            res["sets"].append(rec)
            page_sets.append(rec)
            if age > FAIL_DAYS:
                res["fail"].append(f"stale      {where}: checked {d}, {age} days ago (limit {FAIL_DAYS})")
            elif age > WARN_DAYS:
                res["warn"].append(f"warn       {where}: checked {d}, {age} days ago (warns past {WARN_DAYS}, "
                                   f"fails past {FAIL_DAYS})")

        if rel in exempt:
            # What a machine can still check about a human judgement: a rival's price, or a page whose whole subject is
            # one rival, is not "about open-weight models". (A table is allowed: the reason says what it compares.)
            hard = [w for w in why if not w.startswith("comparison table")]
            if hard:
                res["fail"].append(f"exempt     {rel}: listed as exempt but now has a rival claim ({'; '.join(hard)}). "
                                   f"Date it and take it off claim_freshness_exempt.json.")
            continue
        if is_hub and not why:
            continue
        if why:
            res["rival_pages"] += 1
            res["why"][rel] = why
        if not page_sets and not any("malformed" in f and rel in f for f in res["fail"]):
            if need:
                reason = "; ".join(why) if why else "no reason it is claim-free is recorded"
                res["fail"].append(f"undated    {rel}: quotes a rival's price/plan/feature ({reason}) and carries "
                                   f"no data-claims-checked date")
        for age, stamp, ctx in stale_texts(text, [s["text"] for s in pg.sets], today):
            res["fail"].append(f"stale-text {rel}: still says {stamp!r} ({age} days ago): ...{ctx}...")

    for rel in exempt:
        if rel not in seen_rel:
            res["fail"].append(f"exempt     {rel}: listed as exempt but the page does not exist; remove the entry")
    return res


# --------------------------------------------------------------------------------------------------- self-check
def _page(body: str, title: str = "x") -> str:
    return (f"<!doctype html><html><head><title>{title}</title></head><body><nav><a>Outlier</a></nav><article>"
            f"{body}</article><footer>$249 once</footer></body></html>")


def _write(root: Path, rel: str, html_text: str) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(html_text, encoding="utf-8")


def self_check(verbose: bool = False) -> int:
    """Build a tree with every verdict in it and demand each one. Returns 0 only if the gate judges all correctly."""
    today = dt.date(2026, 10, 20)

    def stamp(days: int, extra: str = "") -> str:
        d = (today - dt.timedelta(days=days)).isoformat()
        return (f'<p>ChatGPT Plus is $20 a month.</p><span class="byline" data-claims-checked="{d}" '
                f'data-claims-set="ChatGPT">ChatGPT prices checked {d}</span>{extra}')

    cases = {
        # path: (html, expected verdict prefix or None for clean, expect_warn)
        "vs/outlier-vs-fresh/index.html": (_page(stamp(5)), None, False),
        "vs/outlier-vs-aging/index.html": (_page(stamp(35)), None, True),
        "vs/outlier-vs-edge45/index.html": (_page(stamp(45)), None, True),
        "vs/outlier-vs-stale/index.html": (_page(stamp(46)), "stale ", False),
        "vs/outlier-vs-ancient/index.html": (_page(stamp(120)), "stale ", False),
        "vs/outlier-vs-undated/index.html": (_page("<p>ChatGPT Plus is $20 a month.</p>"), "undated", False),
        "vs/priced-but-undated/index.html": (_page("<p>Claude Pro costs $20.</p>"), "undated", False),
        "vs/future/index.html": (_page(stamp(-3)), "malformed", False),
        "vs/badformat/index.html": (_page('<p>$20</p><span data-claims-checked="19/10/2026">checked 19/10/2026</span>'),
                                    "malformed", False),
        "vs/hidden-date/index.html": (_page(
            '<p>$20</p><span data-claims-checked="2026-10-19">checked recently</span>'), "malformed", False),
        "vs/mislabelled-date/index.html": (_page(
            '<p>$20</p><span data-claims-checked="2026-10-19">checked 2026-07-01</span>'), "malformed", False),
        "vs/stale-sentence/index.html": (_page(stamp(2, "<p>Cline Pro price, checked 2026-07-23.</p>")),
                                         "stale-text", False),
        "vs/our-old-date/index.html": (_page(stamp(2, "<p>Outlier pricing as of 2026-07-23.</p>")), None, False),
        "vs/exempt-ok/index.html": (_page("<p>Gemma and Llama are open-weight model families.</p>"), None, False),
        "vs/exempt-priced/index.html": (_page("<p>The API costs $15 per million tokens.</p>"), "exempt", False),
        "vs/table-only/index.html": (_page(
            "<table><tr><th>Tool</th><th>Plan</th></tr><tr><td>Outlier</td><td>one price</td></tr>"
            "<tr><td>Ollama</td><td>free</td></tr></table>"), "undated", False),
        "best/roundup/index.html": (_page(stamp(10) + stamp(40)), None, True),
        "seo/vs/generated-undated/index.html": (_page("<p>Hosted APIs are logged on the provider side.</p>"),
                                                "undated", False),
        "seo/vs/generated-dated/index.html": (_page(
            f'<p>Hosted APIs.</p><span data-claims-checked="{(today - dt.timedelta(days=3)).isoformat()}" '
            f'data-claims-set="hosted APIs">checked {(today - dt.timedelta(days=3)).isoformat()}</span>'), None, False),
        # a hand-made page under seo/vs/ is not "generated", but it is still default-deny
        "seo/vs/hand-made-undated/index.html": (_page("<p>Some assistants wrap a cloud model.</p>"), "undated", False),
        "seo/vs/hand-made-exempt/index.html": (_page("<p>Some assistants wrap a cloud model.</p>"), None, False),
    }
    exempt = {"vs/exempt-ok/index.html": "open-weight models", "vs/exempt-priced/index.html": "was clean once",
              "vs/ghost/index.html": "page that no longer exists",
              "seo/vs/hand-made-exempt/index.html": "defines a category, names no product"}
    bad = []
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        for rel, (h, _v, _w) in cases.items():
            _write(root, rel, h)
        _write(root, "_seo_build/owned_pages.json",
               json.dumps(["seo/vs/generated-undated/index.html", "seo/vs/generated-dated/index.html"]))
        res = scan(root, today, exempt=exempt, exempt_max=4)
        joined = "\n".join(res["fail"])
        for rel, (_h, verdict, expect_warn) in cases.items():
            fails = [f for f in res["fail"] if f" {rel}" in f or f"{rel}:" in f or f"{rel} [" in f]
            warns = [w for w in res["warn"] if rel in w]
            if verdict is None and fails:
                bad.append(f"{rel}: should be clean, got {fails[0][:90]}")
            if verdict is not None and not any(f.startswith(verdict) for f in fails):
                bad.append(f"{rel}: should fail as {verdict!r}, got {fails or 'nothing'}")
            if expect_warn and not warns:
                bad.append(f"{rel}: should warn")
            if not expect_warn and warns:
                bad.append(f"{rel}: should not warn, got {warns[0][:90]}")
        if "ghost" not in joined:
            bad.append("an exempt entry for a page that does not exist was not reported")
        # pin: a bigger exempt list than the cap must fail
        over = scan(root, today, exempt=exempt, exempt_max=3)
        if not any("pinned at 3" in f for f in over["fail"]):
            bad.append("an exempt list over EXEMPT_MAX did not fail")
        # a tree with nothing in scope must not read as clean
        with tempfile.TemporaryDirectory() as empty:
            e = scan(Path(empty), today, exempt={})
            if e["pages"] >= MIN_PAGES:
                bad.append("an empty tree reported enough pages")
    # the real arithmetic at its edges
    assert parse_date("2026-02-30") is None and parse_date("July 2026") == dt.date(2026, 7, 1)
    assert parse_date("23 July 2026") == parse_date("July 23, 2026") == dt.date(2026, 7, 23)
    assert says_date("checked 23 July 2026", dt.date(2026, 7, 23)) and not says_date("checked", dt.date(2026, 7, 23))
    if bad:
        print("claim_freshness_gate SELF-CHECK FAILED: the gate misjudged its own fixtures:")
        for b in bad:
            print("  -", b)
        return 1
    if verbose:
        print(f"claim_freshness_gate self-check: {len(cases)} fixtures (fresh, 35 d warn, 45 d warn, 46 d fail, 120 d "
              f"fail, undated, future, malformed, hidden date, stale sentence, exempt, table, seo) each judged correctly")
    return 0


# ------------------------------------------------------------------------------------------------------- main
def main(argv: list[str]) -> int:
    argv = list(argv)
    today = dt.datetime.now(dt.timezone.utc).date()
    if "--today" in argv:                       # --today YYYY-MM-DD: judge the site as of another day
        i = argv.index("--today")
        today = dt.date.fromisoformat(argv[i + 1])
        del argv[i:i + 2]
    args = [a for a in argv if not a.startswith("--")]    # argv[1]: the site root; default the current directory
    if "--self-check" in argv:
        rc = self_check(verbose=True)
        if rc == 0:
            print("OK")
        return rc
    rc = self_check()
    if rc:
        return rc                      # a gate that misjudges its own fixtures must not judge the site
    root = Path(args[0] if args else ".").resolve()
    res = scan(root, today)

    if res["pages"] < MIN_PAGES:
        print(f"claim_freshness_gate: {res['pages']} page(s) under vs/, best/ and seo/vs/ in {root}")
        print(f"FAIL: expected at least {MIN_PAGES}. A gate that read no pages prints the same word as a clean one.")
        return 1

    sets = sorted(res["sets"], key=lambda r: -r["age"])
    if "--list" in argv:
        for r in sets:
            tag = "FAIL" if r["age"] > FAIL_DAYS else ("WARN" if r["age"] > WARN_DAYS else "ok  ")
            print(f"{tag}  {r['date']}  {r['age']:>3}d  {r['page']}  [{r['label']}]")
        for rel, why in sorted(res["why"].items()):
            if not any(s["page"] == rel for s in sets):
                print(f"NONE  ----------  ---   {rel}  ({'; '.join(why)})")

    print(f"claim_freshness_gate: {res['pages']} pages scanned; {res['rival_pages']} quote a rival's price, plan or "
          f"feature; {len(res['sets'])} claim set(s) dated; {len(load_exempt())} exempt")
    if sets:
        o = sets[0]
        print(f"claim_freshness_gate: oldest claim set {o['date']} ({o['age']} days): {o['page']} [{o['label']}]")
    for w in res["warn"]:
        print("  " + w)
    for f in res["fail"][:60]:
        print("  FAIL " + f)
    if len(res["fail"]) > 60:
        print(f"  ... and {len(res['fail']) - 60} more")
    if res["fail"]:
        print(f"FAIL: {len(res['fail'])} problem(s); a rival claim older than {FAIL_DAYS} days, or undated, blocks the "
              f"deploy. Re-read the rival's own page, correct the claim, move the date; if it cannot be confirmed, "
              f"remove the claim.")
        return 1
    print(f"PASS: every rival claim set is dated and none is older than {FAIL_DAYS} days"
          + (f" ({len(res['warn'])} between {WARN_DAYS} and {FAIL_DAYS})" if res["warn"] else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
