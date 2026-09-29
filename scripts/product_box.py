#!/usr/bin/env python3
"""Put a product box on every page that answers a question but offers no way to act on it.

    python3 scripts/product_box.py [--check]

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


def box(tag: str, spot: str, version: str) -> str:
    src = f"{tag}-box-{spot}"[:80]
    dmg = f"{REPO}/v{version}/Outlier-{version}-arm64.dmg"
    return (
        f'<div class="pbox" data-pbox="{spot}">\n'
        f'<p class="pbox-price">Outlier Pro: $249 once &middot; or 4 &times; $62.25'
        f'<span data-pbox-founding hidden> &middot; founders price $124.50 while seats last</span></p>\n'
        f'<p class="pbox-btns"><a class="pbox-dl" href="{HUB}/dl/outlier?src={src}&amp;to={dmg}">Download free</a> '
        f'<a class="pbox-buy" href="{HUB}/buy/outlier?src={src}">Buy Pro</a></p>\n'
        f'<p class="pbox-req">Free to start (Nano and Lite). macOS 26+, Apple silicon. '
        f'14-day refund on Pro, no questions asked.</p>\n'
        f'</div>\n'
    )


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


def insert(s: str, rel: str, version: str, end_only: bool) -> str:
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
    # style once in <head>, the founders script once before </body>
    if "data-pbox-style" not in out:
        h = out.find("</head>")
        out = out[:h] + STYLE + out[h:]
    if "data-pbox-script" not in out:
        b = out.rfind("</body>")
        out = out[:b] + SCRIPT + out[b:]
    return out


def main(argv: list[str]) -> int:
    check = "--check" in argv
    version = current_version()
    changed = 0
    for rel, end_only in [(r, False) for r in TARGETS_BOTH] + [(r, True) for r in TARGETS_END_ONLY]:
        if any(a in rel for a in ARMS):
            print(f"  SKIP (title-test arm) {rel}")
            continue
        p = ROOT / rel
        s = p.read_text(encoding="utf-8")
        if "data-pbox=" in s:
            continue
        new = insert(s, rel, version, end_only)
        changed += 1
        print(f"  {rel}: {new.count('data-pbox=')} box(es)")
        if not check:
            p.write_text(new, encoding="utf-8")
    print(f"  {changed} page(s) {'would change' if check else 'written'} (v{version})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
