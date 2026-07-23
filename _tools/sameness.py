#!/usr/bin/env python3
"""Corpus-level sameness: individual articles can read human while the SET reads generated.

Checks the things a human editor notices across pages but a per-page metric misses:
  - identical section skeletons (same H2 count, same order of structural blocks)
  - the same opening move on every article
  - the same closing move
  - H2 headings that are templated across pages
  - "quick answer" phrasing that repeats
"""
import re, sys, pathlib, statistics as st
from collections import Counter

HUBS = {"learn", "vs", "for", "best", "how-to", "run", "data", "seo", "developers", "about", ""}

def vis(h):
    h = re.sub(r"<script.*?</script>", " ", h, flags=re.S | re.I)
    h = re.sub(r"<style.*?</style>", " ", h, flags=re.S | re.I)
    h = re.sub(r"<[^>]+>", " ", h)
    return re.sub(r"\s+", " ", h).strip()

def is_article(p, root):
    rel = p.parent.relative_to(root).as_posix()
    return rel not in HUBS and rel != "." and "_seo_build" not in rel

def main():
    root = pathlib.Path(sys.argv[1])
    arts = [p for p in sorted(root.rglob("index.html")) if is_article(p, root)]
    print(f"articles (hubs excluded): {len(arts)}\n")

    skeletons, h2_counts, first_sents, last_sents, h2_all, qa_all = Counter(), [], [], [], Counter(), []
    blocks_seq = Counter()

    for p in arts:
        h = p.read_text(errors="ignore")
        h2s = [vis(x) for x in re.findall(r"<h2[^>]*>(.*?)</h2>", h, flags=re.S | re.I)]
        h2_counts.append(len(h2s))
        for x in h2s: h2_all[x.lower().strip()] += 1

        # structural block order fingerprint
        seq = []
        for cls, tag in [("quick-answer","QA"), ("lead","LEAD"), ("receipts","RCPT"),
                         ("cta","CTA"), ("related","REL"), ("faq","FAQ")]:
            m = re.search(rf'class="[^"]*\b{cls}\b', h)
            if m: seq.append((m.start(), tag))
        if re.search(r"<table", h):
            seq.append((re.search(r"<table", h).start(), "TBL"))
        seq.sort()
        fp = ">".join(t for _, t in seq)
        blocks_seq[fp] += 1
        skeletons[f"{len(h2s)}h2|{fp}"] += 1

        # first / last real sentence of body prose
        ps = [vis(x) for x in re.findall(r"<p[^>]*>(.*?)</p>", h, flags=re.S | re.I)]
        ps = [x for x in ps if len(x.split()) >= 12]
        if ps:
            first_sents.append(re.split(r"(?<=[.!?])\s", ps[0])[0])
            last_sents.append(re.split(r"(?<=[.!?])\s", ps[-1])[0])

        qa = re.search(r'class="quick-answer".*?<p[^>]*>(.*?)</p>', h, flags=re.S | re.I)
        if qa: qa_all.append(vis(qa.group(1)))

    print(f"H2 count      mean {st.mean(h2_counts):.1f}  stdev {st.pstdev(h2_counts):.2f}  "
          f"range {min(h2_counts)}-{max(h2_counts)}")
    print(f"distinct block-order fingerprints: {len(blocks_seq)} across {len(arts)} articles")
    for fp, c in blocks_seq.most_common(6):
        print(f"   {c:4d} ({100*c/len(arts):4.1f}%)  {fp}")

    print(f"\ndistinct full skeletons: {len(skeletons)}")
    for s, c in skeletons.most_common(5):
        print(f"   {c:4d}  {s}")

    print("\nH2 headings reused across 3+ articles:")
    rep = [(t, c) for t, c in h2_all.most_common() if c >= 3]
    for t, c in rep[:20]:
        print(f"   {c:4d}  {t[:78]}")
    if not rep: print("   (none)")

    def opener_stats(sents, label):
        first_words = Counter(" ".join(s.split()[:3]).lower().strip(",.") for s in sents)
        first_word = Counter(s.split()[0].lower().strip(",.") for s in sents if s.split())
        print(f"\n{label}: {len(sents)} sampled")
        print("   most common FIRST WORD:")
        for w, c in first_word.most_common(6):
            print(f"      {c:4d} ({100*c/len(sents):4.1f}%)  {w}")
        print("   most common first 3 words:")
        for w, c in first_words.most_common(5):
            if c >= 2: print(f"      {c:4d}  {w}")

    opener_stats(first_sents, "OPENING sentence of body")
    opener_stats(last_sents, "CLOSING sentence of body")

    if qa_all:
        qw = Counter(" ".join(q.split()[:2]).lower() for q in qa_all)
        print(f"\nQUICK-ANSWER openers ({len(qa_all)} boxes):")
        for w, c in qw.most_common(8):
            print(f"   {c:4d} ({100*c/len(qa_all):4.1f}%)  {w}")

if __name__ == "__main__":
    main()
