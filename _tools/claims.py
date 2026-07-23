#!/usr/bin/env python3
"""Extract every checkable factual assertion about a THIRD PARTY from the new /vs/ pages.

The adversarial verifier never ran (session limit), so these competitor claims are unverified.
This produces a review sheet: one line per claim, grouped by page, highest-risk first.

Risk ordering:
  1. Legal / security allegations about a named company   (highest liability)
  2. Direct quotes attributed to someone
  3. Prices and money
  4. Dates and version numbers
  5. Policy claims (training on data, retention, opt-out)
  6. Hard numbers (limits, context windows, sizes)
"""
import re, sys, pathlib, json
from collections import OrderedDict

PRE = {'apple-intelligence-vs-local-ai','best-chatgpt-alternative-mac-offline','cursor-alternatives-local-mac',
 'jan-vs-ollama','local-ai-vs-claude-code','local-ai-vs-cloud-ai','mac-native-ai-comparison','ollama-vs-lm-studio',
 'outlier-core-27b-vs-claude-opus','outlier-vs-chatgpt','outlier-vs-claude-code','outlier-vs-gemini',
 'outlier-vs-jan','outlier-vs-lm-studio','outlier-vs-ollama'}

PATTERNS = [
 ("LEGAL/SECURITY", re.compile(r"\b(lawsuit|sued|suing|copyright suit|settlement|breach|vulnerabilit|exploit|"
                               r"prompt injection|exfiltrat|CVE-\d+|investigation|fined|regulator|FTC|GDPR fine|"
                               r"class action|allegation|accused)\b", re.I)),
 ("QUOTE",          re.compile(r"[\"“][^\"“”]{25,240}[\"”]")),
 ("MONEY",          re.compile(r"(?<![\w])(\$\s?\d[\d,]*(?:\.\d+)?\s?(?:/\s?(?:mo|month|yr|year|seat|user))?"
                               r"|\d+\s?(?:USD|EUR|GBP)|free tier|free plan|no free tier)", re.I)),
 ("DATE/VERSION",   re.compile(r"\b(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+20\d\d"
                               r"|(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+20\d\d"
                               r"|20\d\d-\d\d-\d\d|v?\d+\.\d+(?:\.\d+)?)\b")),
 ("POLICY",         re.compile(r"\b(train(?:s|ed|ing)? on|opt[- ]out|opt[- ]in|retain(?:s|ed|tion)?|delete[sd]? within|"
                               r"human review|data (?:is|are) (?:sent|stored|shared)|privacy polic|terms of service|"
                               r"does not (?:store|train|retain)|zero[- ]retention)\b", re.I)),
 ("NUMBER",         re.compile(r"\b(\d[\d,]*\s?(?:k|K|M|B)?\s?(?:tokens?|context|parameters?|GB|TB|MB|tok/s|"
                               r"requests?|messages?|users?|stars?|hours?|days?|%))\b")),
]

OURS = re.compile(r"\bOutlier\b", re.I)

def visible(html):
    h = re.sub(r"<script.*?</script>", " ", html, flags=re.S|re.I)
    h = re.sub(r"<style.*?</style>", " ", h, flags=re.S|re.I)
    h = re.sub(r"<nav.*?</nav>", " ", h, flags=re.S|re.I)
    h = re.sub(r"<footer.*?</footer>", " ", h, flags=re.S|re.I)
    h = re.sub(r"<[^>]+>", " ", h)
    for a,b in [("&amp;","&"),("&nbsp;"," "),("&mdash;","—"),("&ndash;","–"),("&rsquo;","'"),
                ("&lsquo;","'"),("&ldquo;",'"'),("&rdquo;",'"'),("&middot;","·"),("&rsaquo;","›"),("&hellip;","…")]:
        h = h.replace(a,b)
    return re.sub(r"\s+"," ",h).strip()

def sentences(t):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"“])", t) if len(s.split()) >= 4]

def main():
    root = pathlib.Path(sys.argv[1])
    out = []
    counts = OrderedDict((k,0) for k,_ in PATTERNS)
    pages = 0
    for d in sorted(root.glob("vs/*/")):
        if d.name in PRE or not (d/"index.html").exists():
            continue
        pages += 1
        html = (d/"index.html").read_text(errors="ignore")
        subj = ""
        m = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.S)
        if m: subj = re.sub(r"<[^>]+>","",m.group(1)).strip()
        text = visible(html)
        hits = []
        for s in sentences(text):
            # only claims that are ABOUT a third party — skip pure Outlier self-description
            if OURS.search(s) and len(OURS.findall(s)) >= 2:
                continue
            for label, pat in PATTERNS:
                if pat.search(s):
                    hits.append((label, s))
                    counts[label] += 1
                    break
        if hits:
            order = {k:i for i,(k,_) in enumerate(PATTERNS)}
            hits.sort(key=lambda x: order[x[0]])
            out.append((d.name, subj, hits))

    lines = ["# Unverified competitor claims — /vs/ batch review sheet", ""]
    lines.append("The adversarial verify stage never ran (session limit), so **none of these claims about third")
    lines.append("parties have been independently checked**. Each is quoted verbatim with its page. Scan the")
    lines.append("LEGAL/SECURITY and QUOTE blocks first — those carry the most liability.")
    lines.append("")
    lines.append(f"**{pages} pages · {sum(counts.values())} extracted claims**")
    lines.append("")
    lines.append("| category | count |")
    lines.append("|---|---|")
    for k,v in counts.items():
        lines.append(f"| {k} | {v} |")
    lines.append("")
    # highest-risk first across the whole corpus
    lines.append("---")
    lines.append("## ⚠️ LEGAL / SECURITY allegations (read every one)")
    lines.append("")
    any_legal = False
    for slug, subj, hits in out:
        ls = [s for lbl,s in hits if lbl == "LEGAL/SECURITY"]
        if ls:
            any_legal = True
            lines.append(f"### `/vs/{slug}/` — {subj}")
            for s in ls: lines.append(f"- {s}")
            lines.append("")
    if not any_legal: lines.append("_None found._\n")

    lines.append("---")
    lines.append("## Direct quotes attributed to a third party")
    lines.append("")
    anyq = False
    for slug, subj, hits in out:
        qs = [s for lbl,s in hits if lbl == "QUOTE"]
        if qs:
            anyq = True
            lines.append(f"### `/vs/{slug}/`")
            for s in qs: lines.append(f"- {s}")
            lines.append("")
    if not anyq: lines.append("_None found._\n")

    lines.append("---")
    lines.append("## All remaining claims, by page")
    lines.append("")
    for slug, subj, hits in out:
        rest = [(l,s) for l,s in hits if l not in ("LEGAL/SECURITY","QUOTE")]
        if not rest: continue
        lines.append(f"### `/vs/{slug}/` — {subj}")
        for lbl, s in rest:
            lines.append(f"- **[{lbl}]** {s}")
        lines.append("")

    dest = root/"_tools"/"VS_CLAIMS_REVIEW.md"
    dest.write_text("\n".join(lines))
    print(f"pages scanned : {pages}")
    for k,v in counts.items(): print(f"  {k:16s} {v}")
    print(f"total claims  : {sum(counts.values())}")
    print(f"written       : {dest}")

if __name__ == "__main__":
    main()
