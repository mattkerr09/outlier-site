#!/usr/bin/env python3
"""A cited source is not a checked source.

`rival_price_source_gate.py` already asks whether a page pricing someone else
CITES a vendor pricing URL. On 2026-09-14 that gate passed
`/vs/outlier-vs-cline/` while the page claimed ClinePass cost "$4.99 the first
month" -- a figure that appears nowhere on cline.bot. The citation was present;
the price was not in it. **Citation presence and citation content are different
properties, and only the weaker one was gated.**

AdPlaybook's `source_freshness_gate.py` already checks the stronger property for
quoted phrases on /specs/ pages. This is that idea aimed at rival PRICES, which
is the claim class that actually failed here: a wrong price about another
company's product is a statement about their business, published under ours.

WHAT IT CHECKS. For each page: take every dollar figure in VISIBLE text that is
not one of ours, and confirm it appears in at least one external source the page
cites. Script and style are stripped first -- adapting the AdPlaybook gate's
hard-won lesson that a raw-HTML pass returns strings no human ever read.

    rival_price_in_source_gate.py <page.html> [...]   # check these pages
    rival_price_in_source_gate.py --self-check        # prove it can fail
"""
from __future__ import annotations
import re, subprocess, sys

OURS = {"$249", "$0"}                      # Outlier's own pricing, not a rival claim
_cache: dict[str, str] = {}

def fetch(url: str) -> str:
    """curl, not urllib: Cloudflare bans the urllib UA on several of these hosts."""
    if url in _cache:
        return _cache[url]
    r = subprocess.run(["curl", "-sL", "--max-time", "25", "-A",
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)", url],
                       capture_output=True, text=True)
    _cache[url] = r.stdout or ""
    return _cache[url]

def visible(html: str) -> str:
    body = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", html)
    return re.sub(r"(?s)<[^>]+>", " ", body)

def prices(text: str) -> list[str]:
    # $N or $N.NN; dedupe, drop ours
    found = re.findall(r"\$\d+(?:\.\d{2})?", text)
    return sorted({p for p in found if p not in OURS})

def cited(html: str) -> list[str]:
    us = set(re.findall(r'href="(https?://[^"]+)"', html))
    return sorted(u for u in us if "outlier.host" not in u)

def check(path: str, html: str | None = None) -> list[str]:
    h = html if html is not None else open(path, encoding="utf-8", errors="replace").read()
    srcs = cited(h)
    corpus = "\n".join(fetch(u) for u in srcs)
    if not corpus.strip():
        # An empty corpus would pass every price vacuously. That is the failure
        # mode this whole file exists to prevent, so it is an error, not a pass.
        return [f"{path}: NO SOURCE CONTENT FETCHED ({len(srcs)} urls) -- cannot check"]
    base = _baseline().get(_key(path), {})
    bad = [p for p in prices(visible(h)) if p not in corpus and p not in base]
    return [f"{path}: {p} appears in no cited source" for p in bad]


def _key(path: str) -> str:
    i = path.find("vs/")
    return path[i:] if i >= 0 else path


def _baseline() -> dict:
    import json, pathlib
    f = pathlib.Path(__file__).with_name("rival_price_in_source_baseline.json")
    if not f.exists():
        return {}
    return {k: v for k, v in json.loads(f.read_text()).items() if not k.startswith("_")}

def self_check() -> int:
    """Prove it fails on a price that is not in its source, and passes on one that is."""
    page = ('<a href="https://example.com/p">src</a>'
            '<p>RivalCorp costs $77.00 a month and $12.00 to start.</p>')
    _cache["https://example.com/p"] = "RivalCorp pricing: $12.00 to start."
    out = check("<self-check>", page)
    ok_fail = any("$77.00" in o for o in out)
    ok_pass = not any("$12.00" in o for o in out)
    print("self-check: absent price flagged  ->", "PASS" if ok_fail else "FAIL")
    print("self-check: present price allowed ->", "PASS" if ok_pass else "FAIL")
    return 0 if (ok_fail and ok_pass) else 1

if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or args[0] == "--self-check":
        sys.exit(self_check())
    fails: list[str] = []
    for p in args:
        fails += check(p)
    for f in fails:
        print(f)
    print(f"\n{'FAIL' if fails else 'PASS'} — {len(args)} page(s), {len(fails)} unsourced price claim(s).")
    sys.exit(1 if fails else 0)
