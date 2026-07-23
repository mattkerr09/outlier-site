#!/usr/bin/env python3
"""Replace identical '<h2>Frequently asked questions</h2>' headings with topic-specific ones.

Conservative by design: a page only gets a rewrite if a clean, grammatical heading can be
produced from its own H1 (or its slug, for for/ and data/). Otherwise it KEEPS the generic
heading — a clean generic beats an awkward specific.
"""
from __future__ import annotations
import re, sys, pathlib

GENERIC = "<h2>Frequently asked questions</h2>"
SKIP = {"vs/outlier-vs-chatgpt/index.html"}   # live template for an in-flight batch

PROFESSION = {
 "accountants": "accountants", "consultants": "consultants", "educators": "teachers",
 "finance": "people in finance", "healthcare": "clinicians", "journalists": "journalists",
 "lawyers": "lawyers", "marketers": "marketers", "nonprofits": "nonprofit teams",
 "real-estate": "real estate agents", "researchers": "researchers", "startups": "founders",
 "students": "students", "teams": "small teams", "therapists": "therapists",
 "translators": "translators", "writers": "writers",
}
DATASET = {
 "can-a-local-27b-model-code-like-claude": "the 27B coding measurements",
 "local-ai-benchmarks-mac-2026": "these Mac benchmarks",
 "mac-ram-to-model-size": "the RAM-to-model-size table",
 "outlier-vs-claude-54-prompt-benchmark": "the 54-prompt benchmark",
 "prefix-cache-latency-benchmarks": "these latency measurements",
 "v11-streaming-engine-benchmarks": "the streaming-engine numbers",
}

# H1 shapes that will NOT nominalise into "Questions about ___"
REJECT_START = re.compile(r"^(can|does|do|is|are|will|should|why|who|when|where|which|has|have)\b", re.I)
FINITE_VERB = re.compile(r"\b(is|are|was|were|has|have|will|keeps|means|gets|goes|costs|uses|runs|makes|comes)\b", re.I)
IMPERATIVE = re.compile(r"^(run|use|install|move|fix|free|stop|cancel|speed|write|review|download|set)\b", re.I)
STRIP_PREFIX = ("how to ", "what is ", "what are ", "the best ", "best ")

def clean_topic(h1: str):
    t = h1.strip()
    if t.endswith("?"):
        t = t[:-1].strip()
    t = re.split(r"\s+[—–]\s+", t)[0].strip()   # em/en-dash subtitle
    t = re.split(r":\s+", t)[0].strip()                    # colon subtitle
    t = re.split(r"(?<=[a-z])\.\s+", t)[0].strip()         # trailing second sentence
    if REJECT_START.match(t):
        return None
    low = t.lower()
    for pre in STRIP_PREFIX:
        if low.startswith(pre):
            t = t[len(pre):].strip()
            break
    if FINITE_VERB.search(t):        # sentence-shaped -> broken fragment
        return None
    if IMPERATIVE.match(t):          # "Questions about run X" reads wrong
        return None
    t = t.strip().rstrip(",.")
    if "?" in t or ", and " in t.lower():   # leftover clause -> awkward heading
        return None
    if re.match(r"^(the|a|an)\b", t, re.I) and len(t.split()) <= 3:
        return None                          # "The math" is not a topic
    if re.search(r"\b(does|do|did)\b", t, re.I):
        return None                          # residual question fragment
    if not (2 <= len(t.split()) <= 8):
        return None
    # Lowercase the first word ONLY when it's a common opener, never a brand/proper noun.
    COMMON = {"how", "private", "local", "running", "using", "offline", "free", "small", "real"}
    first = t.split()[0]
    if first.lower() in COMMON:
        t = first.lower() + t[len(first):]
    return t

def heading_for(path: pathlib.Path, html: str):
    slug, hub = path.parent.name, path.parent.parent.name
    if hub == "for":
        who = PROFESSION.get(slug)
        return f"<h2>What {who} ask most</h2>" if who else None
    if hub == "data":
        ds = DATASET.get(slug)
        return f"<h2>Questions about {ds}</h2>" if ds else None
    m = re.search(r"<h1[^>]*>(.*?)</h1>", html, flags=re.S)
    if not m:
        return None
    topic = clean_topic(re.sub(r"<[^>]+>", "", m.group(1)))
    if not topic:
        return None
    if hub == "how-to":
        return f"<h2>Questions that come up when you {topic[0].lower() + topic[1:]}</h2>" \
               if len(topic.split()) <= 6 else None
    if hub in ("vs", "run", "learn", "best"):
        return f"<h2>Questions about {topic}</h2>"
    return None

def main():
    root = pathlib.Path(sys.argv[1])
    apply = "--apply" in sys.argv
    changed = kept = 0
    counts, samples = {}, []
    for p in sorted(root.rglob("index.html")):
        rel = str(p.relative_to(root))
        if "_seo_build" in rel or rel in SKIP:
            continue
        html = p.read_text(errors="ignore")
        if GENERIC not in html:
            continue
        new = heading_for(p, html)
        if not new:
            kept += 1
            continue
        counts[new] = counts.get(new, 0) + 1
        samples.append((rel, new[4:-5]))
        if apply:
            p.write_text(html.replace(GENERIC, new, 1))
        changed += 1
    for rel, h in samples:
        print(f"  {rel[:54]:54s} -> {h}")
    dupes = {k: v for k, v in counts.items() if v > 1}
    print(f"\n{'APPLIED' if apply else 'DRY RUN'}: {changed} rewritten, {kept} left generic")
    print(f"distinct: {len(counts)} | shared by >1: {len(dupes)}")
    for k, v in sorted(dupes.items(), key=lambda x: -x[1])[:6]:
        print(f"   {v:3d}  {k[4:-5]}")

if __name__ == "__main__":
    main()
