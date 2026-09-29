#!/usr/bin/env python3
"""Put a product box on every page that answers a question but offers no way to act on it.

    python3 scripts/product_box.py [--check]          # the dead-end pages
    python3 scripts/product_box.py --seo [--check]    # /seo/: the box after the Quick answer
    python3 scripts/product_box.py --bare [--check]   # the price + Buy under a bare Download
    python3 scripts/product_box.py --std-cta [--check]  # "See Pro" -> Buy Pro in the standard end block

WHY (CEO, 2026-09-28/29 — ops/search/WHAT-WORKS-2026-09-28.md, checklist item 1). A page
that answers the question and then only offers the menu's Download button is a dead end.
The box: Download free + the price with its pay-in-four beside it + the founders line +
Buy + requirements + the refund promise — right after the part that answers the question,
and again at the end.

HOW IT STAYS HONEST
- The founders line is NOT hard-coded as available: it is a hidden mount filled by one small
  script that asks the same /founding endpoint the site's bar uses and shows the line only
  while seats remain (soldOut hides it). The static price is the regular one.
- class="pbox" is chrome to visible_dateline_gate and seo_lint (like "cta" and "related"),
  so adding it never makes a page claim new content.
- Idempotent: a page that already has a box (data-pbox) is left alone; --check writes nothing.
- The four title-test arms are skipped until 2026-10-13, and so are legal pages, stubs,
  404 and verification files.

/seo/ (--seo): every article under /seo/ already ends in a Download button, but on 28 of them
that button was the first one, sitting after 60% of the page. --seo puts the box right after
the Quick answer on every /seo/ article (not the withdrawn noindex page, not the hubs). The
renderer's template (_seo_build/templates/_base.html) emits the SAME bytes through box(),
STYLE and SCRIPT below, so a later render keeps the box instead of re-dating the pages.

A bare Download (--bare): a page whose in-article button is a Download with no price and no
Buy (the /seo/ articles' last button, the /seo/ hubs, /learn/can-you-run-claude-locally/) gets
the price line, Buy and the refund promise directly under that Download, as a box of its own
(end_box). It is its own <div class="pbox">, not a link inside the Download's paragraph,
because the dateline gates strip that div as chrome, and a bare "Buy Pro" in the article text
would read to them as new content.
"""
from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
HUB = "https://kerr-affiliate-hub.kerrco.workers.dev"
REPO = "https://github.com/Outlier-host/outlier-app-releases/releases/download"

#: Pages that answer a question with no in-article Download/Buy (measured 2026-09-29).
TARGETS_BOTH = [
    "data/outlier-tier-benchmarks-2026-08/index.html",
    "learn/397b-model-on-64gb-mac/index.html",
    "learn/4-bit-vs-2-bit-quantization/index.html",
    "learn/chat-coding-vs-agentic-coding/index.html",
    "learn/free-tier-vs-paid-tier-mmlu/index.html",
    "learn/i-was-wrong-about-our-own-ram-requirement/index.html",
    "learn/shrinking-a-mac-app-bundle/index.html",
    "vs/lm-studio-alternative/index.html",
    "vs/when-ollama-is-enough/index.html",
    "seo/learn/why-ai-agents-narrate-instead-of-acting/index.html",
]
#: A reference page: one box at the end, not in the middle of the docs.
TARGETS_END_ONLY = ["developers/index.html"]
#: Pages that already end in a priced Download block: the box after the answer only.
#: /vs/mac-mini-vs-mac-studio-local-ai/ is where /run/local-ai-m1-m2-m3-m4-mac-studio/ (17
#: visitors) redirects. The CEO, 09-29, said to keep that redirect and let the target carry the box.
TARGETS_ANSWER_ONLY = ["vs/mac-mini-vs-mac-studio-local-ai/index.html"]
#: Never before 2026-10-13 (title test).
ARMS = ("vs/mlx-vs-llama-cpp/", "vs/mac-vs-nvidia-gpu-local-ai/",
        "vs/apple-intelligence-vs-local-ai/", "vs/local-ai-vs-claude-code/")

STYLE = """<style data-pbox-style>
.pbox{margin:1.6rem 0;padding:1rem 1.15rem;border:1px solid rgba(127,127,127,.35);border-radius:12px}
.pbox p{margin:.3rem 0}
.pbox .pbox-price{font-weight:600}
.pbox .pbox-btns{display:flex;flex-wrap:wrap;gap:.6rem;margin:.7rem 0 .5rem}
.pbox .pbox-btns a{display:inline-block;padding:.55rem 1.05rem;border-radius:9px;text-decoration:none;font-weight:600}
.pbox .pbox-dl{background:#0071e3;color:#fff}
.pbox .pbox-buy{border:1px solid currentColor}
.pbox .pbox-req{font-size:.85rem;opacity:.75}
</style>
"""

SCRIPT = """<script data-pbox-script>
(function(){var m=document.querySelectorAll('[data-pbox-founding]');if(!m.length)return;
fetch('https://kerr-lead-agent.kerrco.workers.dev/founding?site=outlier.host').then(function(r){return r.json()})
.then(function(d){if(!d||d.soldOut)return;m.forEach(function(e){e.hidden=false;});}).catch(function(){});})();
</script>
"""


#: The refund promise in terms.html's own words. Every box and end block says the same thing.
REFUND = "Refund window: 14 days, no questions asked."


def current_version() -> str:
    s = (ROOT / "index.html").read_text(encoding="utf-8")
    m = re.search(r"releases/download/v(\d+\.\d+\.\d+)/Outlier-\1-arm64\.dmg", s)
    if not m:
        raise SystemExit("could not read the current version from index.html")
    return m.group(1)


def page_tag(rel: str) -> str:
    rel = re.sub(r"/index\.html$", "", rel)
    rel = re.sub(r"\.html$", "", rel)
    return re.sub(r"[^a-z0-9-]+", "-", rel.lower()).strip("-")[:80] or "page"


#: The hub keeps 60 characters of a tag: checkout_link_gate reads it back from the 303's
#: metadata_src, and a 61-character /seo/ tag came back cut, so the sale would not name its
#: page and spot. The page part is shortened, never the "-box-<spot>" that says which box sold.
SRC_MAX = 60


def box(tag: str, spot: str, version: str, src: str | None = None) -> str:
    """The product box. `src` overrides the counting tag (typed_url_pages.py: "pricing-page")."""
    suffix = f"-box-{spot}"
    src = src or (tag[:SRC_MAX - len(suffix)].rstrip("-") + suffix)
    dmg = f"{REPO}/v{version}/Outlier-{version}-arm64.dmg"
    return (
        f'<div class="pbox" data-pbox="{spot}">\n'
        f'<p class="pbox-price">Outlier Pro: $249 once &middot; or 4 &times; $62.25'
        f'<span data-pbox-founding hidden> &middot; founders price $124.50 while seats last</span></p>\n'
        f'<p class="pbox-btns"><a class="pbox-dl" href="{HUB}/dl/outlier?src={src}&amp;to={dmg}" rel="nofollow">Download free</a> '
        f'<a class="pbox-buy" href="{HUB}/buy/outlier?src={src}" rel="nofollow">Buy Pro</a></p>\n'
        f'<p class="pbox-req">Free to start (Nano and Lite). macOS 26+, Apple silicon. '
        f'{REFUND}</p>\n'
        f'</div>\n'
    )


def end_box(tag: str, version: str, requirements: bool = True) -> str:
    """The price line, Buy and the refund promise, for under a Download that is already there.

    `requirements=False` where the Download's own small print already says free / M1 or newer /
    macOS 26+ (the /seo/ articles), so the box does not say it twice."""
    suffix = "-box-end"
    src = tag[:SRC_MAX - len(suffix)].rstrip("-") + suffix
    req = ("Free to start (Nano and Lite). macOS 26+, Apple silicon. " if requirements else "")
    return (
        f'<div class="pbox" data-pbox="end">\n'
        f'<p class="pbox-price">Outlier Pro: $249 once &middot; or 4 &times; $62.25'
        f'<span data-pbox-founding hidden> &middot; founders price $124.50 while seats last</span></p>\n'
        f'<p class="pbox-btns"><a class="pbox-buy" href="{HUB}/buy/outlier?src={src}" rel="nofollow">Buy Pro</a></p>\n'
        f'<p class="pbox-req">{req}{REFUND}</p>\n'
        f'</div>\n'
    )


#: The bare Downloads outside /seo/'s articles (measured 2026-09-29: an in-article Download
#: with no price and no Buy or pricing link beside it). The /seo/ articles are found by bare_targets().
BARE_OTHER = [
    "seo/index.html", "seo/how-to/index.html", "seo/learn/index.html",
    "seo/run/index.html", "seo/vs/index.html",
    "learn/can-you-run-claude-locally/index.html",
]
_SMALL_PRINT = re.compile(r'\s*<p style="font-size:0\.8rem;[^"]*">.*?</p>', re.S)


def insert_end(s: str, rel: str, version: str) -> str:
    """The end box directly under the page's bare Download (and under its small print)."""
    tag = page_tag(rel)
    m = re.search(r'<a class="cta"[^>]*href="[^"]*/dl/outlier[^"]*"[^>]*>.*?</a>', s, re.S)
    if m:
        at, requirements = m.end(), True
        sp = _SMALL_PRINT.match(s, at)
        if sp:
            at, requirements = sp.end(), False
    else:
        d = None
        for c in re.finditer(r'<div class="cta">', s):
            e = _div_end(s, c.start())
            if e > 0 and "/dl/outlier" in s[c.start():e]:
                d = e
                break
        if d is None:
            raise ValueError(f"{rel}: no bare Download found")
        at, requirements = d, True
    out = s[:at] + "\n" + end_box(tag, version, requirements) + s[at:]
    return _style_and_script(out)


def bare_targets() -> list[str]:
    """The /seo/ articles (their last button is the bare Download) plus BARE_OTHER, less any
    page that already has an end box."""
    out = []
    for p in sorted((ROOT / "seo").glob("*/*/index.html")):
        s = p.read_text(encoding="utf-8")
        if 'data-pbox="answer"' in s and 'data-pbox="end"' not in s:
            out.append(str(p.relative_to(ROOT)))
    for rel in BARE_OTHER:
        if 'data-pbox="end"' not in (ROOT / rel).read_text(encoding="utf-8"):
            out.append(rel)
    return out


#: The standard end block ("Try Outlier free" + this price line + Download free + "See Pro"),
#: on 166 articles (div.cta) and 7 hubs (div.cta-band). CEO, 2026-09-29: "See Pro" (to /#pricing,
#: one click short of checkout) becomes Buy Pro through the hub. The refund goes in, in terms.html's
#: words. The founders half moves into the /founding-driven hidden span, so no page hard-codes
#: $124.50 / 4 x $31.13 once the seats are gone.
STD_PRICE_OLD = ("Free: Nano + Lite. Pro: $249 once &middot;&nbsp;or&nbsp;4&nbsp;&times;&nbsp;$62.25; "
                 "$124.50 for the first 25 &middot;&nbsp;or&nbsp;4&nbsp;&times;&nbsp;$31.13. macOS 26+. "
                 "In the US, Klarna or Afterpay at checkout: four payments, two weeks apart.")
STD_PRICE_NEW = ("Free: Nano + Lite. Pro: $249 once &middot;&nbsp;or&nbsp;4&nbsp;&times;&nbsp;$62.25"
                 "<span data-pbox-founding hidden>; $124.50 for the first 25 &middot;&nbsp;or&nbsp;4&nbsp;"
                 "&times;&nbsp;$31.13</span>. macOS 26+. In the US, Klarna or Afterpay at checkout: four "
                 "payments, two weeks apart. " + REFUND)
_STD_SEE_STYLE = ('style="background:transparent;color:var(--text);box-shadow:inset 0 0 0 1px '
                  'var(--border);margin:.5rem 0 0 .5rem"')
STD_SEE_OLD = f'<a class="btn" href="https://outlier.host/#pricing" {_STD_SEE_STYLE}>See Pro</a>'
#: The homepage's no-subscription line says the same founders price, statically.
HOME_OLD = ("Pro: every model, $249 once &middot;&nbsp;or&nbsp;4&nbsp;&times;&nbsp;$62.25 &mdash; or $124.50 "
            "for the first 25 &middot;&nbsp;or&nbsp;4&nbsp;&times;&nbsp;$31.13. No subscription, no per-token cost.")
HOME_NEW = ("Pro: every model, $249 once &middot;&nbsp;or&nbsp;4&nbsp;&times;&nbsp;$62.25<span data-pbox-founding "
            "hidden> &mdash; or $124.50 for the first 25 &middot;&nbsp;or&nbsp;4&nbsp;&times;&nbsp;$31.13</span>. "
            "No subscription, no per-token cost.")
_FOUNDERS_SHOWN = re.compile(r"124\.50|31\.13")


def _founders_visible(s: str) -> list[str]:
    """Founders figures left in the page's text outside the hidden /founding span, the founding bar's
    data-now attribute and scripts: what a visitor would read after the seats sell out."""
    t = re.sub(r"<span data-pbox-founding hidden>[^<]*</span>", "", s)
    t = re.sub(r"(?s)<script\b.*?</script>", "", t)
    t = re.sub(r'data-now="[^"]*"', "", t)
    t = re.sub(r"(?s)<[^>]+>", " ", t)
    return [t[max(0, m.start() - 60):m.end() + 20].strip() for m in _FOUNDERS_SHOWN.finditer(t)]


def _script_only(out: str) -> str:
    if "data-pbox-script" not in out:
        b = out.rfind("</body>")
        out = out[:b] + SCRIPT + out[b:]
    return out


def std_cta(s: str, rel: str) -> str:
    """Rewrite the one standard end block on a page. Raises unless it finds exactly that block."""
    blocks = [m for m in re.finditer(r'<div class="(?:cta|cta-band)">', s)]
    hits = []
    for m in blocks:
        e = _div_end(s, m.start())
        blk = s[m.start():e]
        if STD_SEE_OLD in blk and STD_PRICE_OLD in blk and "/dl/outlier?src=" in blk:
            hits.append((m.start(), e, blk))
    if len(hits) != 1:
        raise ValueError(f"{rel}: {len(hits)} standard end blocks (want exactly 1)")
    a, e, blk = hits[0]
    if blk.count(STD_SEE_OLD) != 1 or blk.count(STD_PRICE_OLD) != 1:
        raise ValueError(f"{rel}: the block repeats its price line or button")
    tag = re.search(r"/dl/outlier\?src=([a-z0-9-]+)", blk).group(1)
    suffix = "-end"
    src = tag[:SRC_MAX - len(suffix)].rstrip("-") + suffix
    buy = f'<a class="btn" href="{HUB}/buy/outlier?src={src}" rel="nofollow" {_STD_SEE_STYLE}>Buy Pro</a>'
    new_blk = blk.replace(STD_PRICE_OLD, STD_PRICE_NEW).replace(STD_SEE_OLD, buy)
    return _script_only(s[:a] + new_blk + s[e:])


def std_cta_targets() -> list[str]:
    out = []
    for f in sorted(ROOT.rglob("*.html")):
        if ".git" in f.parts or "_seo_build" in f.parts:
            continue
        if STD_SEE_OLD in f.read_text(encoding="utf-8", errors="ignore"):
            out.append(str(f.relative_to(ROOT)))
    return out


def _div_end(s: str, start: int) -> int:
    """Index just past the </div> that closes the <div ...> opening at `start`."""
    depth, i = 0, start
    for m in re.finditer(r"<div\b|</div>", s[start:]):
        if m.group(0) == "</div>":
            depth -= 1
            if depth == 0:
                return start + m.end()
        else:
            depth += 1
    return -1


def insert(s: str, rel: str, version: str, end_only: bool, answer_only: bool = False) -> str:
    tag = page_tag(rel)
    out = s
    if not end_only:
        # 1) right after the part that answers the question
        m = re.search(r'<div class="(?:quick-answer|qa)"', out)
        if m:
            at = _div_end(out, m.start())
        else:
            a = out.find("<article")
            h = out.find("<h2", a if a >= 0 else 0)
            at = h
        if at is None or at < 0:
            raise ValueError(f"{rel}: no place after the answer")
        out = out[:at] + "\n" + box(tag, "answer", version) + out[at:]
    if answer_only:
        return _style_and_script(out)
    # 2) at the end of the content
    e = out.find("</article>")
    if e >= 0:
        wrap_close = out.rfind("</div>", 0, e)
        at = wrap_close if wrap_close > out.rfind("data-pbox=", 0, e) else e
    else:
        for marker in ('<div class="sublist"', '<div class="related"', '<div class="foot"', "</main>", "</body>"):
            at = out.find(marker)
            if at >= 0:
                break
    if at < 0:
        raise ValueError(f"{rel}: no place at the end")
    out = out[:at] + box(tag, "end", version) + out[at:]
    return _style_and_script(out)


def _style_and_script(out: str) -> str:
    """The style once in <head>, the founders script once before the last </body>."""
    if "data-pbox-style" not in out:
        h = out.find("</head>")
        out = out[:h] + STYLE + out[h:]
    if "data-pbox-script" not in out:
        b = out.rfind("</body>")
        out = out[:b] + SCRIPT + out[b:]
    return out


def seo_targets() -> list[str]:
    """Every /seo/ article with a Quick answer and no answer box yet — not a hub, not withdrawn."""
    out = []
    for p in sorted((ROOT / "seo").glob("*/*/index.html")):
        s = p.read_text(encoding="utf-8")
        if 'name="robots" content="noindex' in s or 'http-equiv="refresh"' in s.lower():
            continue
        if not re.search(r'<div class="(?:quick-answer|qa)"', s) or 'data-pbox="answer"' in s:
            continue
        out.append(str(p.relative_to(ROOT)))
    return out


def main(argv: list[str]) -> int:
    check = "--check" in argv
    version = current_version()
    changed = 0
    if "--std-cta" in argv:
        problems = []
        for rel in std_cta_targets():
            if any(a in rel for a in ARMS):
                print(f"  SKIP (title-test arm) {rel}")
                continue
            p = ROOT / rel
            try:
                new = std_cta(p.read_text(encoding="utf-8"), rel)
            except ValueError as e:
                problems.append(str(e))
                continue
            left = _founders_visible(new)
            if left:
                problems.append(f"{rel}: founders price still shown: {left[:2]}")
                continue
            changed += 1
            if not check:
                p.write_text(new, encoding="utf-8")
        home = ROOT / "index.html"
        h = home.read_text(encoding="utf-8")
        if HOME_OLD in h:
            h = _script_only(h.replace(HOME_OLD, HOME_NEW))
            changed += 1
            if not check:
                home.write_text(h, encoding="utf-8")
        for pr in problems:
            print("  NOT CHANGED", pr)
        print(f"  {changed} page(s) {'would change' if check else 'written'}; {len(problems)} refused")
        return 1 if problems else 0
    if "--bare" in argv:
        for rel in bare_targets():
            if any(a in rel for a in ARMS):
                print(f"  SKIP (title-test arm) {rel}")
                continue
            p = ROOT / rel
            new = insert_end(p.read_text(encoding="utf-8"), rel, version)
            changed += 1
            if not check:
                p.write_text(new, encoding="utf-8")
        print(f"  {changed} page(s) with a bare Download {'would change' if check else 'written'} (v{version})")
        return 0
    if "--seo" in argv:
        for rel in seo_targets():
            if any(a in rel for a in ARMS):
                print(f"  SKIP (title-test arm) {rel}")
                continue
            p = ROOT / rel
            new = insert(p.read_text(encoding="utf-8"), rel, version, False, answer_only=True)
            changed += 1
            if not check:
                p.write_text(new, encoding="utf-8")
        print(f"  {changed} /seo/ page(s) {'would change' if check else 'written'} (v{version})")
        return 0
    jobs = ([(r, False, False) for r in TARGETS_BOTH] + [(r, True, False) for r in TARGETS_END_ONLY]
            + [(r, False, True) for r in TARGETS_ANSWER_ONLY])
    for rel, end_only, answer_only in jobs:
        if any(a in rel for a in ARMS):
            print(f"  SKIP (title-test arm) {rel}")
            continue
        p = ROOT / rel
        s = p.read_text(encoding="utf-8")
        if "data-pbox=" in s:
            continue
        new = insert(s, rel, version, end_only, answer_only=answer_only)
        changed += 1
        print(f"  {rel}: {new.count('data-pbox=')} box(es)")
        if not check:
            p.write_text(new, encoding="utf-8")
    print(f"  {changed} page(s) {'would change' if check else 'written'} (v{version})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
