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
    # ⚠️ BYTES, NOT text=True. This gate fetches RIVALS' pages, whose encoding we
    # do not control, and text=True decodes them as strict UTF-8. A page served
    # in another charset — or one whose body curl cuts mid-multibyte at the 25s
    # timeout — raised UnicodeDecodeError and took the whole gate down with it:
    #   UnicodeDecodeError: 'utf-8' codec can't decode byte 0xe2 ... invalid
    #   continuation byte
    # Measured on the live rival set. A gate that dies on someone else's
    # encoding is a gate that can never be wired into CI, which is where this
    # one has been sitting.
    r = subprocess.run(["curl", "-sL", "--max-time", "25", "-A",
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)", url],
                       capture_output=True)
    _cache[url] = (r.stdout or b"").decode("utf-8", "replace")
    return _cache[url]

#: ⚠️ TRIAGE NOTE, 2026-09-16 — READ BEFORE TRYING TO MAKE THIS WIRABLE.
#: Run against the site it reports 51 unsourced claims across 22 pages, which is
#: why it is not in gates.yml: a gate that lands red teaches people to ignore
#: the suite.
#:
#: The claims are a MIX and separating them is the real work:
#:   * a QUOTED rival price ("$8,565 at launch") must appear in a cited source;
#:   * a DERIVED figure ("$1,999 MSRP … roughly $62/GB") is arithmetic on a
#:     sourced number and can never appear verbatim anywhere.
#:
#: I tried to split them with a regex for "roughly|about|~|/GB|per million" and
#: it scored 30 of 51 — but that heuristic is WRONG, and recording why saves the
#: next attempt: it separates PER-UNIT-OR-APPROXIMATE from PLAIN, which is not
#: the same distinction. DeepSeek's "$0.14 per million input tokens" is a
#: genuine quoted price that SHOULD be sourced, and the regex called it derived.
#:
#: So there is no cheap split. A derived figure should have to show its
#: arithmetic and cite its input — a different check from string-matching a
#: corpus — and the 51 want per-page judgement, not a pattern.
#:
#: The risk is real and measured: a blind find-and-replace put four rivals'
#: prices wrong on this site for eighteen days. This gate is the class that
#: catches that. It is worth finishing, not deleting.


def readable(url: str) -> str:
    """A fetched source as a READER meets it: script and style stripped.

    ⚠️ THE CORPUS USED TO BE RAW HTML, AND RAW HTML CORROBORATES PRICES WITH
    MINIFIED JAVASCRIPT. Measured 2026-09-16: lmstudio.ai/pricing returns seven
    "dollar figures" to a regex — $1, $11, $2 — every one of them a token inside
    a bundle, and not one of them a price. A claim of "$1" or "$2" about any
    vendor would have been confirmed by a build artefact.

    It is the same rule already applied to our own copy: measure prose on
    tag-stripped text, because that is the text that exists for a reader. A
    source whose prices live only in a script has not published them anywhere
    this gate can read.
    """
    return visible(fetch(url))


def fetch_all(urls: list[str]) -> list[str]:
    """Fetch in parallel, because serial 25s timeouts are why this is unwired.

    The gate is correct and has never run in CI: at one 25s curl per cited URL
    it took over two minutes, and a slow gate wired carelessly is how a suite
    stops being run at all. The work is entirely network wait, so the fix is
    concurrency rather than fewer checks — the same URLs, the same timeout, the
    same answers, in the time of the slowest one instead of the sum.

    Bounded at 8: enough to collapse the wall time, few enough not to look like
    a burst to any one host. Results come back in the caller's order, so the
    corpus a page is checked against does not depend on which host answered
    first — an order-dependent corpus would make this gate flaky rather than
    fast.
    """
    if not urls:
        return []
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=min(8, len(urls))) as pool:
        return list(pool.map(readable, urls))


def visible(html: str) -> str:
    body = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", html)
    return re.sub(r"(?s)<[^>]+>", " ", body)

def prices(text: str) -> list[str]:
    # $N or $N.NN; dedupe, drop ours
    found = re.findall(r"\$\d+(?:\.\d{2})?", text)
    return sorted({p for p in found if p not in OURS})

#: Hosts that appear on every page as furniture rather than as evidence. A price
#: must never be corroborated against one.
NOT_SOURCES = ("outlier.host", "builtbykerr.com")


def cited(html: str) -> list[str]:
    """External URLs a page offers as SOURCES — not every external href on it.

    ⚠️ THE BYLINE LINK WAS IN HERE AND IT PASSED A PRICE THE GATE HAD NEVER
    SEEN. Measured 2026-09-16: /vs/lm-studio-alternative/ claims LM Studio sells
    a "$20USD / month" tier. lmstudio.ai renders its prices in JavaScript, so
    curl sees none of them — but the author link at the foot of every page,
    builtbykerr.com, happens to carry "$20–$50/mo" in a table about consulting
    rates. The gate matched that and reported the claim corroborated. A
    different company, a different product, a range rather than a price: any
    $20 claim on any page would have passed the same way.

    A corroborating corpus has to be made of things the page is citing AS
    EVIDENCE. The author's own site is furniture.
    """
    us = set(re.findall(r'href="(https?://[^"]+)"', html))
    return sorted(u for u in us if not any(h in u for h in NOT_SOURCES))

def check(path: str, html: str | None = None) -> list[str]:
    h = html if html is not None else open(path, encoding="utf-8", errors="replace").read()
    srcs = cited(h)
    corpus = "\n".join(fetch_all(srcs))
    if not srcs:
        # Cites nothing external at all. The instinct is to hand this to
        # rival_price_source_gate ("N pages cite no vendor pricing URL") and
        # skip. I CHECKED THAT HANDOFF BEFORE TRUSTING IT, and it does not
        # hold: of the 14 pages here citing nothing, exactly two state a rival
        # price -- outlier-vs-gemini ($9.99) and outlier-vs-windsurf ($20/$40/
        # $80/$200) -- and BOTH are baselined in that gate. Skipping them here
        # would have dropped them through both gates at once.
        #
        # So: skip only when there is genuinely nothing to check. A page that
        # prices a rival while citing nothing is reported HERE, by name.
        rivals = prices(visible(h))
        if not rivals:
            return ["SKIP " + path]
        return [f"{path}: prices a rival ({', '.join(rivals)}) and cites no external source"]
    if not corpus.strip():
        # It DOES cite sources and every fetch came back empty. Unlike the case
        # above this is my problem: an empty corpus would pass every price
        # vacuously, which is the exact failure this file exists to prevent.
        return [f"{path}: cites {len(srcs)} url(s) but NONE returned content -- cannot check"]
    # ⚠️ A SOURCE THAT RENDERS ITS PRICES IN JAVASCRIPT CANNOT CORROBORATE
    # ANYTHING, AND SAYING SO IS NOT THE SAME AS SAYING THE PRICE IS WRONG.
    # Measured 2026-09-16: curl returns 63,800 bytes of lmstudio.ai/pricing
    # containing "Bionic" twenty-one times and NOT ONE dollar figure. The page
    # really does say "$20USD / month" and "$100USD / month" — a reader sees
    # them, curl does not. Reported as a failure, the repair a maintainer
    # reaches for is deleting a true statement about someone else's product.
    # So: a corpus with no dollar figure at all is UNCHECKABLE, a third state,
    # exactly as "could not reach the vendor" is not "the seat was released".
    # Which cited sources came back with no price in them AT ALL? Those cannot
    # corroborate anything, and a failure that does not say so reads as "your
    # price is wrong" when the truth is "I could not see it". Named per source,
    # because the union hides it: one source full of dollar figures masks
    # another that rendered none.
    blind = [u for u, t in zip(srcs, [readable(u) for u in srcs])
             if t.strip() and not re.search(r"\$\d", t)]
    base = _baseline().get(_key(path), {})
    seen = prices(visible(h))
    der = derived(seen)
    bad = [p for p in seen if not _in_corpus(p, corpus) and p not in base and p not in der]
    note = ""
    if blind:
        note = (f" -- NOTE: {', '.join(blind)} returned content but not one "
                f"dollar figure, so its prices are rendered client-side and "
                f"fetching cannot confirm or deny this")
    return [f"{path}: {p} appears in no cited source{note}" for p in bad]


def _in_corpus(price: str, corpus: str) -> bool:
    """Is this exact price in the corpus — not merely a prefix of a bigger one?

    ⚠️ THIS WAS A SUBSTRING TEST AND IT PASSED A PRICE IT HAD NEVER SEEN.
    Measured 2026-09-16 on /vs/lm-studio-alternative/: "$20" was accepted
    because the byline link to builtbykerr.com contains "$20–$50/mo" in a table
    about consulting rates. An unrelated site, a different currency context, a
    range rather than a price — and the gate called LM Studio's subscription
    corroborated. Any claim of $20 would have passed, right or wrong, as long as
    SOME cited page held a longer number starting the same way.

    So the match must end at a digit boundary. A price may still be followed by
    a currency word or a slash ("$20USD / month"), which is why this checks the
    next character rather than using \b — \b after a digit would accept "$200".
    """
    for m in re.finditer(re.escape(price), corpus):
        tail = corpus[m.end():m.end() + 3]
        # A digit continues the number. So does ".NN" (cents) or ",NNN"
        # (thousands) — but a bare "." is a full stop and "$20." is a match,
        # which the first version of this got wrong and the control caught.
        if tail[:1].isdigit():
            continue
        if tail[:1] in ".," and tail[1:3].isdigit():
            continue
        return True
    return False


def derived(found: list[str]) -> set[str]:
    """Figures this page COMPUTED, which by construction appear on no vendor page.

    Not a new heuristic: derived_price_gate.py already established the
    discriminator for this site, and established that a word-proximity one does
    not work -- it wrongly flagged Msty's "$149/yr" and Poe's "$49.99/year",
    both of which ARE on the vendor's own pricing page. The discriminator is the
    arithmetic itself: a figure is derived when another figure on the SAME page
    multiplies to it exactly. Reusing it rather than inventing a second rule --
    two heuristics for one question is how they drift apart.
    """
    vals = {p: float(p[1:]) for p in found}
    out: set[str] = set()
    for big, bv in vals.items():
        for small, sv in vals.items():
            if sv <= 0 or small == big:
                continue
            q = bv / sv
            # x12 ONLY -- the discriminator derived_price_gate.py actually
            # validated (annual = monthly x 12). A first version here allowed
            # any multiple 2..36 and promptly swallowed xAI's $300, which that
            # gate's own docstring records as QUOTED and unverified: $30 x 10
            # happens to appear on the page. Widening a proven rule without
            # re-validating it is how a gate starts hiding the thing it exists
            # to find. x24 and x36 are two- and three-year totals, same shape.
            if abs(q - round(q)) < 1e-9 and round(q) in (12, 24, 36):
                out.add(big)
                break
    return out


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

def _expand(args: list[str]) -> list[str]:
    """Accept page paths OR a site root, so meta_gate can aim this at a tree.

    meta_gate enumerates scripts/*_gate.py and proves each one REFUSES to report
    clean on an empty tree. It caught this file the day it was written: taking
    only explicit page paths meant it could not be pointed anywhere, so the
    empty-input probe proved nothing about it. A gate that cannot be aimed
    cannot be audited.
    """
    import pathlib
    out: list[str] = []
    for a in args:
        p = pathlib.Path(a)
        if p.is_dir():
            out += [str(x) for x in sorted(p.rglob("vs/**/index.html"))]
        else:
            out.append(a)
    return out


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or args[0] == "--self-check":
        sys.exit(self_check())
    args = _expand(args)
    if not args:
        # Refusing to report clean on nothing is the whole point of meta_gate.
        print("FAIL — no /vs/ pages found under the given root; nothing was checked.")
        sys.exit(1)
    out: list[str] = []
    for p in args:
        out += check(p)
    skips = [o for o in out if o.startswith("SKIP ")]
    fails = [o for o in out if not o.startswith("SKIP ")]
    for f in fails:
        print(f)
    if skips:
        print(f"\nskipped {len(skips)} page(s) citing no external source "
              f"(rival_price_source_gate's business, not this one)")
    print(f"{'FAIL' if fails else 'PASS'} — {len(args)} page(s), "
          f"{len(fails)} unsourced price claim(s), {len(skips)} skipped.")
    sys.exit(1 if fails else 0)
