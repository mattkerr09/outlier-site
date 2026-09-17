#!/usr/bin/env python3
"""Every page we ask Google to index must be REACHABLE by clicking from the homepage.

The other direction from internal_link_gate. That gate asks "does every link
resolve to a file?" — the forward direction. Nothing asked the reverse: "is every
page reached by some link?" A page nobody links is invisible to a gate that only
validates the links that do exist, because there is no link to validate.

FOUND 2026-09-17. /vs/when-ollama-is-enough/ and /vs/lm-studio-alternative/ were
published on 09-16, put in the sitemap, and never added to the /vs/ hub that
lists the other 57 comparisons. The two linked each other and nothing else, so
they formed a disconnected island: in the sitemap, with no crawl path to them.
Every gate passed, because every link on them resolved fine.

⚠️ THIS GATE'S OWN INSTRUMENT IS THE RISK. The first version of this measurement,
written as a throwaway probe, reported 174 of 253 pages unreachable — including
154 pages Google has indexed, which is impossible. The cause was the link
extractor: it matched href="/slug/" and missed href="https://outlier.host/slug/",
which is how this site writes most of its internal links. A probe reporting
something dramatic is a suspect. So the sanity checks below run FIRST and this
gate REFUSES TO REPORT rather than print a scary number from a broken graph —
a gate that cannot check must not report clean, and must not report alarm either.

SCOPE is the sitemap, not the disk. A page we have not asked Google to index is
not an orphan, it is unpublished. /seo/run/run-code-on-m4-pro-macbook-pro/ is
unreachable and not in the sitemap; that is a separate question, not this one.

Baseline: edit BY REMOVAL ONLY, same rule as the dateline gates.

Python 3.9.6 — the site gates run on the system interpreter.
"""
import sys          # before ROOT below, which reads argv
import json
import pathlib
import re
from collections import deque

#: The tree to check. argv[1] lets meta_gate.py point this at a test tree and
#: confirm it fails on an empty one — a gate that cannot be aimed somewhere else
#: cannot be proved to fail, and an unprovable gate is decoration.
ROOT = pathlib.Path(sys.argv[1]).resolve() if len(sys.argv) > 1 and not sys.argv[1].startswith("-") \
    else pathlib.Path(__file__).resolve().parents[1]
BASELINE = pathlib.Path(__file__).resolve().parent / "orphan_page_baseline.json"
HREF = re.compile(r'href="([^"#]+?)"')

#: Below these the graph is not believable and the gate refuses. Measured
#: 2026-09-17: 1893 edges, 250/253 reachable. The broken extractor produced 79.
MIN_EDGES = 500
MIN_REACHABLE_FRACTION = 0.80


def load_pages():
    out = {}
    for p in ROOT.rglob("index.html"):
        if any(part.startswith(".") or part == "node_modules" for part in p.parts):
            continue
        key = str(p.parent.relative_to(ROOT))
        out["" if key == "." else key] = p.read_text(encoding="utf-8", errors="replace")
    return out


def links_of(html, pages):
    """Internal targets, in every shape this site actually writes them."""
    out = set()
    for m in HREF.finditer(html):
        h = m.group(1).split("?")[0]
        h = re.sub(r"^https?://outlier\.host", "", h)   # absolute internal
        if h.startswith("http") or h.startswith("mailto:"):
            continue
        t = re.sub(r"/?index\.html$", "", h.strip("/")).strip("/")
        if t in pages:
            out.add(t)
    return out


def reachable_from_home(pages):
    graph = {k: links_of(v, pages) for k, v in pages.items()}
    edges = sum(len(v) for v in graph.values())
    seen = {"": 0}
    q = deque([""])
    while q:
        cur = q.popleft()
        for nxt in graph.get(cur, ()):
            if nxt not in seen:
                seen[nxt] = seen[cur] + 1
                q.append(nxt)
    return seen, edges, graph


def sitemap_slugs():
    sm = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    out = set()
    for loc in re.findall(r"<loc>([^<]+)</loc>", sm):
        out.add(re.sub(r"^https?://outlier\.host", "", loc.strip()).strip("/"))
    return out


def main():
    if not (ROOT / "sitemap.xml").exists():
        print(f"orphan_page_gate: CANNOT CHECK — no sitemap.xml under {ROOT}.")
        return 1
    pages = load_pages()
    if not pages:
        print(f"orphan_page_gate: CANNOT CHECK — no index.html under {ROOT}.")
        return 1
    seen, edges, graph = reachable_from_home(pages)
    frac = len(seen) / max(len(pages), 1)

    # THE FUNNEL, printed every run — a narrowing rule that excluded everything
    # reads exactly like a clean site.
    print(f"orphan_page_gate: {len(pages)} pages on disk, {edges} internal edges, "
          f"{len(seen)} reachable from the homepage ({frac:.0%})")

    if "" not in pages:
        print("orphan_page_gate: CANNOT CHECK — no homepage index.html found.")
        return 1
    if edges < MIN_EDGES or frac < MIN_REACHABLE_FRACTION:
        print(f"orphan_page_gate: CANNOT CHECK — the link graph is implausible "
              f"({edges} edges, {frac:.0%} reachable; expected >{MIN_EDGES} and "
              f">{MIN_REACHABLE_FRACTION:.0%}). This is what a broken link extractor "
              f"looks like, not what a broken site looks like. Refusing to report "
              f"either a pass or a failure. Fix links_of() first.")
        return 1

    smap = sitemap_slugs()
    orphans = sorted(s for s in smap if s in pages and s not in seen)
    missing_file = sorted(s for s in smap if s not in pages)

    baseline = set()
    if BASELINE.exists():
        baseline = set(json.loads(BASELINE.read_text()))

    new = [o for o in orphans if o not in baseline]
    print(f"orphan_page_gate: {len(smap)} sitemap URLs; {len(orphans)} unreachable "
          f"({len(baseline)} baselined, edit BY REMOVAL ONLY)")
    if missing_file:
        print(f"orphan_page_gate: {len(missing_file)} sitemap URL(s) have no index.html "
              f"(internal_link_gate's territory, reported not enforced): "
              f"{missing_file[:3]}")

    if new:
        print(f"\nFAIL ({len(new)} page(s) in the sitemap with no path from the homepage):")
        for o in new:
            inbound = sum(1 for k, v in graph.items() if k != o and o in v)
            where = "nothing links it" if inbound == 0 else \
                    f"linked only from {inbound} page(s) that are themselves unreachable"
            print(f"  /{o}/ — {where}. We asked Google to index it and gave it no way in.")
        return 1

    print("\nPASS — every sitemap URL is reachable by clicking from the homepage.")
    return 0


def self_check():
    """The gate must fail on its own bug. Two controls."""
    pages = load_pages()
    ok = True

    # 1. A broken extractor must REFUSE, not report a scary number.
    global HREF
    keep = HREF
    HREF = re.compile(r'href="(/[^"#]+?)"')      # the original broken shape
    seen, edges, _ = reachable_from_home(pages)
    frac = len(seen) / len(pages)
    refuses = edges < MIN_EDGES or frac < MIN_REACHABLE_FRACTION
    print(f"  {'ok  ' if refuses else 'FAIL'} a broken extractor ({edges} edges, {frac:.0%} "
          f"reachable) trips CANNOT CHECK instead of reporting")
    ok &= refuses
    HREF = keep

    # 2. With the real extractor the graph must be believable — otherwise every
    #    run of this gate is vacuous and would pass a site full of orphans.
    seen, edges, _ = reachable_from_home(pages)
    frac = len(seen) / len(pages)
    sane = edges >= MIN_EDGES and frac >= MIN_REACHABLE_FRACTION
    print(f"  {'ok  ' if sane else 'FAIL'} the real extractor gives a believable graph "
          f"({edges} edges, {frac:.0%} reachable)")
    ok &= sane
    print("self-check", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(self_check() if "--self-check" in sys.argv else main())
