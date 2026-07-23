#!/usr/bin/env python3
"""Measure how much a page reads as machine-written.

Not a classifier — a set of signals that correlate with LLM prose, each one
independently fixable. Run over outlier.host article HTML.

  python3 aitell.py <site_root> [--worst N] [--csv out.csv]
"""
import re, sys, json, pathlib, statistics as st
from collections import Counter

# Phrases that are near-exclusively LLM register.
TELLS = [
 "delve", "realm of", "it's worth noting", "it is worth noting", "in today's",
 "fast-paced", "let's dive", "dive into", "the landscape of", "navigate the complexities",
 "navigating the", "at the end of the day", "in conclusion", "ultimately,",
 "it's important to note", "when it comes to", "a testament to", "plays a crucial role",
 "plays a vital role", "in the world of", "the key takeaway", "rest assured",
 "look no further", "unlock the", "harness the power", "tapestry", "multifaceted",
 "myriad of", "plethora", "robust solution", "seamlessly", "elevate your",
 "game-changer", "paradigm shift", "cutting-edge", "state-of-the-art",
]
# Formulaic constructions
CONSTRUCTIONS = [
 (r"\bisn'?t just\b.{0,40}\bit'?s\b", "isn't-just-X-it's-Y"),
 (r"\bnot only\b.{0,60}\bbut also\b", "not-only-but-also"),
 (r"\bwhether you'?re\b", "whether-you're-opener"),
 (r"\bthat said,", "that-said-pivot"),
 (r"\bhowever,\s", "however-comma"),
 (r"\bmoreover,", "moreover"),
 (r"\bfurthermore,", "furthermore"),
 (r"\badditionally,", "additionally"),
 (r"\bthink of it (?:as|like)\b", "think-of-it-as"),
 (r"\bhere'?s the thing\b", "heres-the-thing"),
 (r"\bthe short answer is\b", "short-answer-is"),
]

def visible_text(html: str) -> str:
    h = re.sub(r"<script.*?</script>", " ", html, flags=re.S | re.I)
    h = re.sub(r"<style.*?</style>", " ", h, flags=re.S | re.I)
    h = re.sub(r"<nav.*?</nav>", " ", h, flags=re.S | re.I)
    h = re.sub(r"<footer.*?</footer>", " ", h, flags=re.S | re.I)
    h = re.sub(r"<[^>]+>", " ", h)
    h = (h.replace("&amp;", "&").replace("&nbsp;", " ").replace("&middot;", "·")
          .replace("&rsquo;", "'").replace("&ldquo;", '"').replace("&rdquo;", '"')
          .replace("&mdash;", "—").replace("&#8212;", "—"))
    return re.sub(r"\s+", " ", h).strip()

def paragraphs(html: str):
    return [visible_text(m) for m in re.findall(r"<p[^>]*>(.*?)</p>", html, flags=re.S | re.I)]

def sentences(text: str):
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", text)
    return [p.strip() for p in parts if len(p.split()) >= 2]

def analyse(path: pathlib.Path):
    html = path.read_text(errors="ignore")
    text = visible_text(html)
    words = text.split()
    n = len(words)
    if n < 250:
        return None
    low = text.lower()
    sents = sentences(text)
    slens = [len(s.split()) for s in sents] or [0]
    paras = [p for p in paragraphs(html) if len(p.split()) >= 15]
    plens = [len(p.split()) for p in paras] or [0]

    mean_s = st.mean(slens)
    cv_s = (st.pstdev(slens) / mean_s) if mean_s else 0          # burstiness; low = robotic
    short_pct = 100 * sum(1 for L in slens if L <= 8) / len(slens)
    long_pct = 100 * sum(1 for L in slens if L >= 35) / len(slens)
    cv_p = (st.pstdev(plens) / st.mean(plens)) if plens and st.mean(plens) else 0

    emdash = 1000 * text.count("—") / n
    contractions = 1000 * len(re.findall(r"\b\w+'(?:s|t|re|ve|ll|d|m)\b", low)) / n
    tricolon = 1000 * len(re.findall(r"\b\w+, \w+,? and \w+", low)) / n

    tell_hits = Counter()
    for t in TELLS:
        c = low.count(t)
        if c: tell_hits[t] = c
    con_hits = Counter()
    for pat, name in CONSTRUCTIONS:
        c = len(re.findall(pat, low))
        if c: con_hits[name] = c

    openers = Counter(p.split()[0].lower().strip(",.") for p in paras if p.split())
    top_open, top_open_n = (openers.most_common(1)[0] if openers else ("", 0))
    opener_conc = 100 * top_open_n / len(paras) if paras else 0

    # score: higher = reads more machine-written
    score = 0.0
    if cv_s < 0.50: score += (0.50 - cv_s) * 60          # uniform rhythm
    if short_pct < 12: score += (12 - short_pct) * 1.1   # no punchy short sentences
    if contractions < 6: score += (6 - contractions) * 1.6
    score += min(emdash, 12) * 1.2                       # em-dash overuse
    score += sum(tell_hits.values()) * 5.0
    score += sum(con_hits.values()) * 1.8
    score += max(0, tricolon - 4) * 1.5
    if opener_conc > 25: score += (opener_conc - 25) * 0.5
    if cv_p < 0.35: score += (0.35 - cv_p) * 30

    return dict(
        path=str(path), words=n, sent_cv=round(cv_s, 3), short_pct=round(short_pct, 1),
        long_pct=round(long_pct, 1), para_cv=round(cv_p, 3), emdash_k=round(emdash, 2),
        contractions_k=round(contractions, 2), tricolon_k=round(tricolon, 2),
        opener_conc=round(opener_conc, 1), top_opener=top_open,
        tells=dict(tell_hits), constructions=dict(con_hits),
        score=round(score, 1),
    )

def main():
    root = pathlib.Path(sys.argv[1])
    worst = 20
    if "--worst" in sys.argv: worst = int(sys.argv[sys.argv.index("--worst") + 1])
    rows = []
    for p in sorted(root.rglob("index.html")):
        if "_seo_build" in str(p) or "node_modules" in str(p): continue
        r = analyse(p)
        if r: rows.append(r)
    rows.sort(key=lambda r: -r["score"])

    print(f"analysed {len(rows)} pages\n")
    ss = [r["score"] for r in rows]
    print(f"score      median {st.median(ss):.1f}   p90 {sorted(ss)[int(.9*len(ss))]:.1f}   max {max(ss):.1f}")
    for k, label in [("sent_cv","sentence-length CV (want >0.55)"),
                     ("short_pct","% sentences <=8 words (want >12)"),
                     ("contractions_k","contractions /1k (want >6)"),
                     ("emdash_k","em-dashes /1k (want <6)"),
                     ("tricolon_k","tricolons /1k (want <5)")]:
        v = [r[k] for r in rows]
        print(f"{label:38s} median {st.median(v):.2f}")

    all_tells = Counter()
    for r in rows:
        all_tells.update(r["tells"]); all_tells.update(r["constructions"])
    print("\ntop tells across corpus:")
    for t, c in all_tells.most_common(18):
        print(f"   {c:4d}  {t}")

    print(f"\nworst {worst} pages:")
    print(f"{'score':>6} {'cv':>5} {'shrt':>5} {'contr':>6} {'dash':>5}  page")
    for r in rows[:worst]:
        rel = r["path"].replace(str(root), "").lstrip("/").replace("/index.html", "")
        print(f"{r['score']:6.1f} {r['sent_cv']:5.2f} {r['short_pct']:5.1f} "
              f"{r['contractions_k']:6.2f} {r['emdash_k']:5.2f}  {rel}")

    out = pathlib.Path(__file__).parent / "aitell_report.json"
    out.write_text(json.dumps(rows, indent=1))
    print(f"\nfull report -> {out}")

if __name__ == "__main__":
    main()
