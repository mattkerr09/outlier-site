#!/usr/bin/env python3
"""Block new absolute promises about the agent's honesty and self-checking.

    python3 scripts/honesty_claim_gate.py --self-check
    python3 scripts/honesty_claim_gate.py .

Read body text, titles, descriptions, social cards and every JSON-LD string.
Absolute words and honesty terms must share a sentence and be at most 12 words
apart. Two assertion/oracle promises from the 2026-11-09 audit have explicit
patterns too. This is a prose check, not proof that the app behaves honestly.

The baseline records exact file/sentence pairs, not whole exempt pages. Old
hits warn; new sentences fail. Remove fixed entries and never grow the list.
"""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
import tempfile
from html.parser import HTMLParser
from pathlib import Path

BASELINE_FILE = Path(__file__).with_name("honesty_claim_baseline.json")
BASELINE_MAX = 0  # 2026-11-09: the one hit at the start was reworded; nothing is baselined.
MIN_PAGES = 20  # Same wrong-root protection as faq_schema_visible_gate.
MAX_GAP = 12

ABSOLUTE = re.compile(r"\b(?:never|won't|can't|cannot|always|guaranteed)\b", re.I)
HONESTY = re.compile(
    r"\b(?:fak(?:e|es|ing)|cheat(?:s|ing)?|lie|lies|lying)\b"
    r"|\bgam(?:e|es|ing)\s+(?:its\s+(?:own\s+)?scoreboard|the\s+tests)\b"
    r"|\bsays?\s+(?:[\"']?it(?:'s|\s+is)[\"']?\s+)?[\"']?done\b"
    r"|\bclaims?\s+success\b|\bgreen\s+(?:check|bar)\b", re.I)
SPECIAL = re.compile(
    r"\bonly\s+claims?\s+success\b|\bwithout\s+faking\b"
    r"|\b(?:can't|cannot|won't|never)\s+['\"]?pass['\"]?\s+by\s+rewriting\s+"
    r"(?:a|the)\s+correct\s+assertion\b"
    r"|\ban?\s+external\s+check\s+(?:has\s+)?(?:already\s+)?certified\s+"
    r"(?:the\s+)?old\s+assertion\b", re.I)
QUOTED = re.compile(r'"[^"\n]+"|(?<!\w)\'(?:[^\'\n]|(?<=\w)\'(?=\w))+\'(?!\w)')
QUOTE_BEFORE = re.compile(
    r"\b(?:(?:do\s+not|don't|never)\s+(?:say|write|claim|promise|use)"
    r"|avoid\s+(?:saying|writing|claiming|promising|using|phrases?|claims?)"
    r"|(?:forbidden|banned)\s+(?:phrase|claim)|what\s+not\s+to\s+say)"
    r"\s*(?:the\s+(?:phrase|claim)\s*)?(?:(?:like|such\s+as)\s*)?[:;,]?\s*$", re.I)
QUOTE_AFTER = re.compile(
    r"^\s*(?:is\s+)?(?:an?\s+)?(?:example\s+of\s+)?"
    r"(?:what\s+not\s+to\s+say|(?:a\s+)?(?:forbidden|banned)\s+(?:phrase|claim))\b", re.I)

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
SKIP_TEXT = {"head", "script", "style", "noscript", "template", "svg"}
BLOCK = {"address", "article", "aside", "blockquote", "body", "br", "dd", "div", "dl", "dt", "figcaption",
         "figure", "footer", "h1", "h2", "h3", "h4", "h5", "h6", "header", "hr", "li", "main", "nav",
         "ol", "p", "pre", "section", "table", "td", "th", "tr", "ul"}
HIDDEN_STYLE = re.compile(r"(?:^|;)\s*(?:display\s*:\s*none|visibility\s*:\s*hidden)\s*(?:!important\s*)?(?:;|$)", re.I)


def squash(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def normalized(text: str) -> str:
    return text.translate(str.maketrans({"’": "'", "‘": "'", "“": '"', "”": '"', "\u00a0": " "}))


def forbidden(sentence: str) -> bool:
    text = normalized(sentence)
    # Quotation alone is no exemption: a quoted marketing promise still fails.
    # Mask only a quote explicitly presented as wording to avoid.
    masked = list(text)
    for quote in QUOTED.finditer(text):
        before = QUOTE_BEFORE.search(text[:quote.start()])
        if before or QUOTE_AFTER.search(text[quote.end():]):
            start = before.start() if before else quote.start()
            # Mask the directive too: "Never say ... because a model can lie"
            # is advice to the writer, not an absolute promise about the app.
            masked[start:quote.end()] = " " * (quote.end() - start)
    text = "".join(masked)
    if SPECIAL.search(text):
        return True
    for absolute in ABSOLUTE.finditer(text):
        for honesty in HONESTY.finditer(text):
            start, end = ((absolute.end(), honesty.start()) if absolute.start() < honesty.start()
                          else (honesty.end(), absolute.start()))
            gap = text[start:end]
            if not re.search(r"[;!?]", gap) and len(re.findall(r"\b[\w']+\b", gap)) <= MAX_GAP:
                return True
    return False


def sentences(text: str) -> list[str]:
    # Block boundaries keep adjacent headings/list items from forming promises.
    # A NUL marks a tag boundary; source newlines are just HTML whitespace.
    # Periods inside a price or version are not sentence breaks.
    return [squash(s) for s in re.split(r'\x00+|(?<=[.!?])\s+(?=[^\d])', text) if squash(s)]


def json_strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for child in value:
            yield from json_strings(child)
    elif isinstance(value, dict):
        for child in value.values():
            yield from json_strings(child)


class Page(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[tuple[str, bool]] = []
        self.body: list[str] = []
        self.title: list[str] = []
        self.fields: list[tuple[str, str]] = []
        self.ld: list[str] | None = None
        self.errors: list[str] = []

    def hidden(self) -> bool:
        return any(hidden for _tag, hidden in self.stack)

    def handle_starttag(self, tag, attrs):
        a = {k: v or "" for k, v in attrs}
        if tag == "meta":
            name = (a.get("property") or a.get("name", "")).lower()
            if name == "description":
                self.fields.append(("meta", a.get("content", "")))
            elif name in {"og:title", "og:description", "twitter:title", "twitter:description"}:
                self.fields.append(("og", a.get("content", "")))
        if tag == "script" and a.get("type", "").lower().split(";")[0].strip() == "application/ld+json":
            self.ld = []
        if tag == "br":
            self.body.append(" ")
        elif tag in BLOCK:
            self.body.append("\x00")
        if tag not in VOID:
            self.stack.append((tag, "hidden" in a or bool(HIDDEN_STYLE.search(a.get("style", "")))))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if tag == "script" and self.ld is not None:
            try:
                value = json.loads("".join(self.ld))
                self.fields.extend(("jsonld", s) for s in json_strings(value))
            except ValueError as exc:
                self.errors.append(f"cannot read JSON-LD: {exc}")
            self.ld = None
        if tag in BLOCK:
            self.body.append("\x00")
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break

    def handle_data(self, data):
        tags = {t for t, _hidden in self.stack}
        if self.ld is not None and "script" in tags:
            self.ld.append(data)
        if "title" in tags:
            self.title.append(data)
        if "body" in tags and not tags.intersection(SKIP_TEXT) and not self.hidden():
            self.body.append(data)

    def close(self):
        super().close()
        if self.ld is not None:
            self.errors.append("unclosed JSON-LD script")
        self.fields.extend([("title", "".join(self.title)), ("body", "".join(self.body))])


def check_page(raw: str) -> tuple[list[tuple[str, str]], list[str]]:
    page = Page()
    page.feed(raw)
    page.close()
    hits = set()
    for field, value in page.fields:
        # JSON-LD Answer.text can itself contain HTML; scan its displayed text.
        if field == "jsonld":
            fragment = Page()
            fragment.feed("<body>" + value + "</body>")
            fragment.close()
            value = html.unescape("".join(fragment.body))
        for sentence in sentences(value):
            if forbidden(sentence):
                hits.add((field, sentence))
    return sorted(hits), page.errors


def scan(root: Path) -> tuple[list[tuple[str, str, str]], int, list[str]]:
    hits, errors = [], []
    pages = 0
    for directory, dirs, files in os.walk(root, onerror=lambda exc: errors.append(str(exc))):
        # faq_schema_visible_gate skips dot folders and node_modules; the
        # claim_freshness backlog scan also skips private build folders (_*).
        dirs[:] = sorted(d for d in dirs if not d.startswith((".", "_")) and d != "node_modules")
        for name in sorted(files):
            if not name.endswith(".html"):
                continue
            path = Path(directory) / name
            rel = path.relative_to(root).as_posix()
            try:
                found, bad = check_page(path.read_text(encoding="utf-8", errors="replace"))
            except OSError as exc:
                errors.append(f"{rel}: {exc}")
                continue
            pages += 1
            hits.extend((rel, field, sentence) for field, sentence in found)
            errors.extend(f"{rel}: {error}" for error in bad)
    return sorted(hits), pages, errors


def load_baseline(path: Path = BASELINE_FILE, limit: int = BASELINE_MAX) -> set[tuple[str, str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    entries = data["hits"]
    if not isinstance(entries, list) or len(entries) > limit:
        raise ValueError(f"baseline must be a list pinned at {limit} hits; remove fixed entries, never add hits")
    pairs = set()
    for entry in entries:
        rel, sentence = entry["file"], entry["sentence"]
        if (not isinstance(rel, str) or not isinstance(sentence, str) or not sentence
                or Path(rel).is_absolute() or ".." in Path(rel).parts or not rel.endswith(".html")):
            raise ValueError("baseline entries need a relative HTML file and exact sentence")
        pairs.add((rel, sentence))
    if len(pairs) != len(entries):
        raise ValueError("baseline contains duplicate file/sentence pairs")
    return pairs


def judge(hits: list[tuple[str, str, str]], pages: int, errors: list[str], baseline: set[tuple[str, str]],
          minimum: int = MIN_PAGES) -> tuple[list[tuple[str, str, str]], list[str]]:
    problems = list(errors)
    if pages < minimum:
        problems.append(f"only {pages} page(s) found, expected >= {minimum}: wrong root, nothing proven")
    seen = {(rel, sentence) for rel, _field, sentence in hits}
    for rel, sentence in sorted(baseline - seen):
        problems.append(f"{rel}: baseline hit is gone; remove the entry: {sentence}")
    return [h for h in hits if (h[0], h[2]) not in baseline], problems


def self_check(verbose: bool = False) -> int:
    positives = [
        "It checks its own work: and won't cheat to pass",
        "it can't quietly delete an assertion to fake a pass",
        "You can't 'pass' by rewriting a correct assertion",
        "an external check has already certified the old assertion",
        "(and never fakes a green check)",
        "only claims success it can prove",
        "repairs failed builds without faking green",
        "Outlier cannot lie.", "It always says it's done.",
        "It is guaranteed to report a green bar.", "It never games its scoreboard.",
        "It won't game the tests.", "It never cheats.", "It cannot claim success over failing tests.",
        "It can't say done over a failing test.", "It never lies.", "It is never faking a pass.",
        "Outlier won’t cheat.", 'Outlier says "it never cheats".',
        "Outlier never\ncheats.",
    ]
    negatives = [
        "never sends your code anywhere", "never leaves your Mac", "nobody has paid $49",
        "a guard rejects a test edit that weakens a good test",
        'Do not say "it never cheats".', 'Avoid saying “only claims success it can prove”.',
        '"It never fakes a green check" is an example of what not to say.',
        "Do not say 'it can't cheat' in product copy.",
        'Never say "it never cheats" because models can still lie.',
        'Avoid phrases like "it always claims success".',
        "It never plays a video game.", "It always games with friends.",
        "It never sends your code anywhere. A model can cheat.",
        "It cannot load this video game; the demo cheats.",
        "It can fake a pass.", "It sometimes claims success.",
        "It never " + "word " * 13 + "cheats.",
    ]
    bad = []
    for expected, cases in ((True, positives), (False, negatives)):
        for text in cases:
            got = bool(check_page(f"<html><body><p>{text}</p></body></html>")[0])
            if got != expected:
                bad.append(f"expected {'hit' if expected else 'clean'}: {text}")
    phrase = "Outlier never cheats."
    fields = {
        "body": "<body><p>Outlier <strong>never</strong> cheats.</p></body>",
        "title": f"<head><title>{phrase}</title></head><body></body>",
        "meta": f'<head><meta CONTENT="{phrase}" NAME="description"></head><body></body>',
        "og": f'<head><meta property="og:title" content="{phrase}"></head><body></body>',
        "jsonld": '<head><script type="application/ld+json">' + json.dumps(
            [{"@graph": [{"nested": [0, True, {"text": "Outlier <b>never</b> cheats."}]}]}])
            + '</script></head><body></body>',
    }
    for field, raw in fields.items():
        if check_page(raw) != ([(field, phrase)], []):
            bad.append(f"field not extracted correctly: {field}")
    if check_page("<body><p>Outlier never<br>cheats.</p></body>") != ([("body", phrase)], []):
        bad.append("line break hid a promise")
    for name in ("og:description", "twitter:title", "twitter:description"):
        raw = f'<meta name="{name}" content="{phrase}"><body></body>'
        if check_page(raw) != ([("og", phrase)], []):
            bad.append(f"social field not extracted: {name}")
    hidden = (f'<head><style>/* {phrase} */</style></head><body><!-- {phrase} -->'
              f'<script>const x = "{phrase}";</script><template>{phrase}</template>'
              f'<div hidden>{phrase}</div><p style="display: none">{phrase}</p>'
              f'<p style="visibility: hidden">{phrase}</p><p>never</p><p>cheats</p></body>')
    if check_page(hidden) != ([], []):
        bad.append("hidden content or separate blocks caused a hit")
    if not check_page('<script type="application/ld+json">{bad}</script>')[1]:
        bad.append("unreadable JSON-LD was silently accepted")
    if check_page("<body><p>It can&#39;t cheat.</p></body>")[0] != [("body", "It can't cheat.")]:
        bad.append("HTML entity not decoded")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "page.html").write_text(fields["body"], encoding="utf-8")
        for folder in (".git", ".cache", "node_modules", "_build"):
            (root / folder).mkdir()
            (root / folder / "ignored.html").write_text(fields["body"], encoding="utf-8")
        hits, pages, errors = scan(root)
        if hits != [("page.html", "body", phrase)] or pages != 1 or errors:
            bad.append("tree scan missed an HTML page or scanned a skipped folder")
        old = {("page.html", phrase)}
        if judge(hits, pages, errors, old, minimum=1) != ([], []):
            bad.append("existing exact sentence did not warn instead of fail")
        if not judge(hits, pages, errors, set(), minimum=1)[0]:
            bad.append("new hit did not fail")
        if not judge([("other.html", "body", phrase)], pages, [], old, minimum=1)[0]:
            bad.append("a baseline sentence was allowed on a new page")
        if not judge([("page.html", "body", "It never lies.")], pages, [], old, minimum=1)[0]:
            bad.append("a changed sentence on a baseline page was allowed")
        if not judge([], 0, [], set())[1] or not judge([], 1, [], old, minimum=1)[1]:
            bad.append("empty tree or stale baseline passed")
        if not judge([], 1, ["unreadable page"], set(), minimum=1)[1]:
            bad.append("read error passed")
        baseline_path = root / "baseline.json"
        baseline_path.write_text(json.dumps({"hits": [{"file": "page.html", "sentence": phrase}]}), encoding="utf-8")
        if load_baseline(baseline_path, limit=1) != old:
            bad.append("baseline file did not load exact pairs")
        try:
            load_baseline(baseline_path, limit=0)
        except ValueError:
            pass
        else:
            bad.append("baseline growth passed")
    if bad:
        print("honesty_claim_gate --self-check: FAIL")
        for problem in bad:
            print("  " + problem)
        return 1
    if verbose:
        print(f"honesty_claim_gate --self-check: OK; {len(positives)} positive and {len(negatives)} negative phrases; "
              "body/title/meta/social/JSON-LD, hidden content, tree scan, errors and baseline checks passed")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("root", nargs="?", type=Path, default=Path("."), help="site root, default: current directory")
    parser.add_argument("--self-check", action="store_true", help="prove the detector and baseline judge their fixtures")
    args = parser.parse_args(argv)
    rc = self_check(verbose=args.self_check)
    if rc or args.self_check:
        return rc
    try:
        baseline = load_baseline()
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"honesty_claim_gate: FAIL; cannot load baseline: {exc}")
        return 1
    hits, pages, errors = scan(args.root.resolve())
    new, problems = judge(hits, pages, errors, baseline)
    for rel, field, sentence in hits:
        mark = "WARN baseline" if (rel, sentence) in baseline else "FAIL new"
        print(f"  {mark} {rel} [{field}]: {sentence}")
    for problem in problems:
        print(f"  FAIL {problem}")
    result = "FAIL" if new or problems else "PASS"
    print(f"honesty_claim_gate: {result}; examined {pages} HTML page(s); {len(hits)} hit(s), "
          f"{len(hits) - len(new)} baselined, {len(new)} new; {len(problems)} problem(s)")
    return 1 if new or problems else 0


if __name__ == "__main__":
    sys.exit(main())
