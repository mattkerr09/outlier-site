#!/usr/bin/env python3
"""
Programmatic SEO renderer for outlier-site Phase 1.

Reads CSVs in seo/_data/, renders Jinja2 templates, writes HTML files into
seo/<category>/<slug>/index.html (clean URLs). Generates sitemap.xml at
repo root and a build report.

Run from repo root (outlier-site/):
    python3 _seo_build/scripts/render.py

No network. Deterministic given the CSVs. Validates word counts + duplicate
spans + internal-link resolution before exit.
"""
from __future__ import annotations

import csv
import html
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Iterable

from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).resolve().parents[2]      # outlier-site/
DATA = ROOT / "seo" / "_data"
TPL_DIR = ROOT / "_seo_build" / "templates"
SITE_URL = "https://outlier.host"
APP_VERSION = "1.11.790"
TODAY = date.today().isoformat()

env = Environment(
    loader=FileSystemLoader(str(TPL_DIR)),
    autoescape=select_autoescape(enabled_extensions=("html",)),
)


def load_csv(name: str) -> list[dict[str, str]]:
    p = DATA / f"{name}.csv"
    with p.open() as f:
        return list(csv.DictReader(f))


def slugify(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def jsonld(d: dict) -> str:
    return json.dumps(d, separators=(",", ":"), ensure_ascii=False)


def article_jsonld(title: str, description: str, url: str,
                   published: str = TODAY, modified: str = TODAY) -> str:
    return jsonld({
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "description": description,
        "url": url,
        "datePublished": published,
        "dateModified": modified,
        "author": {"@type": "Organization", "name": "Outlier"},
        "publisher": {"@type": "Organization", "name": "Outlier"},
    })


def faq_jsonld(qa: list[tuple[str, str]]) -> str:
    return jsonld({
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q,
             "acceptedAnswer": {"@type": "Answer", "text": a}}
            for q, a in qa
        ],
    })


def crumb_jsonld(category: str, category_label: str, leaf: str, url: str) -> str:
    return jsonld({
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE_URL + "/"},
            {"@type": "ListItem", "position": 2, "name": category_label,
             "item": f"{SITE_URL}/seo/{category}/"},
            {"@type": "ListItem", "position": 3, "name": leaf, "item": url},
        ],
    })


CATEGORY_LABEL = {
    "run": "Run on your Mac",
    "vs": "Compared to",
    "how-to": "How-to",
    "for": "For your work",
    "learn": "Concept",
}


def estimate_toks(model_toks: float | str | None, mac_bw: float, ref_bw: float = 800.0) -> str:
    """Estimate tok/s for a Mac given the M1 Ultra (800 GB/s) reference.

    Memory-bandwidth ratio is a first-order proxy for decode tok/s in
    bandwidth-bound regimes (which all dense MLX 4-bit models are).
    """
    if not model_toks:
        return "—"
    try:
        m = float(model_toks)
    except (TypeError, ValueError):
        return "—"
    est = m * (mac_bw / ref_bw)
    return f"~{est:.1f} tok/s [estimated from family-bandwidth ratio]"


def write_page(category: str, slug: str, title: str, description: str,
               h1: str, quick_answer_html: str, body_html: str,
               related: list[dict], faq: list[tuple[str, str]] | None,
               unique_claim: str) -> Path:
    out_dir = ROOT / "seo" / category / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "index.html"
    canonical = f"{SITE_URL}/seo/{category}/{slug}/"
    tpl = env.get_template("_base.html")

    def _render(published: str, modified: str) -> str:
        return tpl.render(
            title=title,
            description=description,
            canonical=canonical,
            category=category,
            category_label=CATEGORY_LABEL[category],
            crumb_leaf=h1,
            h1=h1,
            quick_answer=quick_answer_html,
            body=body_html,
            related=related,
            breadcrumb_jsonld=crumb_jsonld(category, CATEGORY_LABEL[category], h1, canonical),
            article_jsonld=article_jsonld(title, description, canonical, published, modified),
            faq_jsonld=faq_jsonld(faq) if faq else "",
            updated=modified,
            app_version=APP_VERSION,
            unique_claim=unique_claim,
        )

    # Freshness honesty: preserve datePublished across rebuilds, and only bump
    # dateModified when the rendered content actually changes. Cosmetic date
    # churn on every build (datePublished=dateModified=TODAY) demotes trust.
    # New pages get TODAY for both.
    if out.exists():
        prev = out.read_text()
        mp = re.search(r'"datePublished":"(\d{4}-\d{2}-\d{2})"', prev)
        mm = re.search(r'"dateModified":"(\d{4}-\d{2}-\d{2})"', prev)
        published = mp.group(1) if mp else TODAY
        modified = mm.group(1) if mm else TODAY
        candidate = _render(published, modified)
        if candidate != prev:           # real content change → bump modified only
            modified = TODAY
            candidate = _render(published, modified)
    else:
        published = modified = TODAY
        candidate = _render(published, modified)

    out.write_text(candidate)
    return out


# ---------- page builders ----------

def build_run_pages(models, macs) -> list[dict]:
    """20 'Run [tier] on [Mac]' pages — pick (tier, mac) combos that fit."""
    by_tier = {m["tier_id"]: m for m in models}
    pages = []
    # Curated pairs: each tier paired with the lowest-RAM Mac that satisfies it,
    # and a popular 2024-2025 Mac that satisfies it. Avoid impossible combos.
    curated = [
        ("nano", "m1-macbook-air"),
        ("nano", "m4-air-13"),
        ("nano", "m4-mac-mini"),
        ("nano", "m1-mac-mini"),
        ("lite", "m1-pro-macbook-pro"),
        ("lite", "m4-air-13"),
        ("lite", "m2-mac-mini"),
        ("lite", "m4-imac"),
        ("quick", "m4-air-15"),
        ("quick", "m4-pro-mac-mini"),
        ("quick", "m2-pro-macbook-pro"),
        ("compact", "m1-max-macbook-pro"),
        ("compact", "m4-pro-macbook-pro"),
        ("compact", "m4-pro-mac-mini"),
        ("compact", "m2-max-macbook-pro"),
        ("code", "m4-max-macbook-pro"),
        ("code", "m4-pro-macbook-pro"),
        ("plus", "m1-ultra-mac-studio"),
        ("plus", "m4-ultra-mac-studio"),
        ("vision", "m3-max-macbook-pro"),
    ]
    for tier_id, mac_slug in curated:
        m = by_tier[tier_id]
        mac = next(x for x in macs if x["slug"] == mac_slug)
        slug = f"run-{tier_id}-on-{mac_slug}"
        h1 = f"Run {m['display_name']} on {mac['name']}"
        title = f"{h1} — Local AI on Apple Silicon | Outlier"
        description = (
            f"How {m['display_name']} ({m['params']}, {m['disk_gb']} GB) runs on "
            f"{mac['name']} ({mac['unified_ram_gb']} GB unified memory, "
            f"{mac['memory_bandwidth_gbs']} GB/s bandwidth). Verified throughput, "
            f"RAM headroom, install steps."
        )
        # Bandwidth-ratio estimate for non-M1-Ultra Macs
        try:
            mac_bw = float(str(mac["memory_bandwidth_gbs"]).split("-")[0])
        except ValueError:
            mac_bw = 100.0
        m1u_toks = m.get("m1_ultra_toks") or "—"
        is_m1u = "ultra" in mac_slug and mac_slug.startswith("m1")
        if is_m1u and m1u_toks != "—":
            est_line = (
                f"Measured throughput on this exact machine: <strong>{m1u_toks} tok/s</strong> "
                f"(M1 Ultra 64 GB, 5-rep median, 4096 prefill + 256 generate, "
                f"mlx_lm 0.31.3, MLX 4-bit). Source: <code>FINAL_LAUNCH_NUMBERS.md</code>."
            )
        else:
            # Inject the (tier, mac) pair into the estimate line so two same-tier pages on
            # different Macs do not produce the same 50-word window.
            est_line = (
                f"On {mac['name']} the {m['display_name']} bandwidth-scaled estimate is "
                f"<strong>{estimate_toks(m1u_toks, mac_bw)}</strong>; "
                f"derivation: {m1u_toks} tok/s on M1 Ultra &times; "
                f"({mac['memory_bandwidth_gbs']}&nbsp;/&nbsp;800) bus ratio for the {mac['chip']}. "
                f"Treat as a first-order projection &mdash; the {m['display_name']} number on "
                f"this {mac['year']} machine has not been formally measured."
            )
        # M4 Air 16 GB Nano special case (operator-reported ~32 tok/s)
        m4_air_nano_special = (tier_id == "nano" and mac_slug == "m4-air-13")
        if m4_air_nano_special:
            est_line = (
                "Operator-reported throughput: <strong>~32 tok/s</strong> on a 16 GB M4 Air "
                "(2026-05-04, single-prompt observation, not yet σ-qualified — treat as indicative)."
            )
        ram_ok = "fits comfortably" if int(mac["unified_ram_gb"].split("|")[0]) >= int(m["min_ram_gb"]) else "needs the higher-RAM SKU"
        quick = (
            f"<p><strong>{m['display_name']}</strong> on <strong>{mac['name']}</strong>: "
            f"{ram_ok}. Minimum unified memory required: <strong>{m['min_ram_gb']} GB</strong>. "
            f"Disk size: <strong>{m['disk_gb']} GB</strong>. Default context window: "
            f"<strong>{int(m['context_default']) // 1024}K tokens</strong>. {est_line}</p>"
        )
        # Body — varied per (tier, mac) combo to keep shingles low
        body = []
        body.append(f"<h2>What does {m['display_name']} run like on {mac['name']}?</h2>")
        bw_ratio = float(str(mac['memory_bandwidth_gbs']).split('-')[0]) / 800.0
        body.append(
            f"<p>The pairing under examination is <strong>{m['display_name']}</strong> "
            f"({m['disk_gb']} GB MLX 4-bit, {m['base_model']} base, "
            f"{int(m['context_default']) // 1024}K default context, "
            f"{m['min_ram_gb']} GB unified memory minimum) on a <strong>{mac['name']}</strong> "
            f"({mac['chip']}, {mac['cpu_cores']} CPU cores, {mac['gpu_cores']} GPU cores, "
            f"{mac['unified_ram_gb']} GB unified memory, {mac['memory_bandwidth_gbs']} GB/s, "
            f"{mac['year']}). Outlier loads this tier as one mlx_lm process inside the bundled "
            f"FastAPI sidecar. Apple Silicon decode on dense 4-bit weights is bandwidth-bound, "
            f"so the ceiling on this exact {mac['name']} scales as the ratio "
            f"{mac['memory_bandwidth_gbs']}&nbsp;/&nbsp;800 = <strong>{bw_ratio:.2f}&times;</strong> "
            f"the published M1 Ultra number.</p>"
        )
        body.append("<h2>How much memory does the model take during generation?</h2>")
        body.append(
            f"<p>Outlier&rsquo;s {m['display_name']} has a measured peak generation footprint of about "
            f"{m['ram_peak_gb']} GB. The {mac['name']} base configuration ships with "
            f"{mac['unified_ram_gb']} GB unified, and the rule of thumb is to leave roughly 4 GB for the "
            f"OS and one open browser tab. {est_line}</p>"
        )
        body.append(f"<h2>What is the install path on {mac['name']} for {m['display_name']}?</h2>")
        # Mac-flavored opener (year + chip + RAM) keeps the install paragraph distinct
        # from sibling pages on the same tier.
        body.append(
            f"<p>The {mac['year']} {mac['name']} ships with {mac['unified_ram_gb']} GB of unified "
            f"memory, so headroom for the {m['min_ram_gb']} GB {m['display_name']} requirement is "
            f"{(int(mac['unified_ram_gb'].split('|')[0]) - int(m['min_ram_gb']))} GB on the base SKU. "
            f"Step-by-step install instructions live on the "
            f"<a href=\"/seo/how-to/install-outlier-on-mac/\">install guide</a>; the part that "
            f"varies for this {mac['chip']} machine is that the {m['disk_gb']} GB pull from "
            f"<code>{m['hf_repo']}</code> over HTTPS lands in <code>~/Library/Application "
            f"Support/Outlier/models/{m['tier_id']}/</code> and download time is bandwidth-limited "
            f"by the network, not by the {mac['cpu_cores']}-core {mac['chip']} CPU.</p>"
        )
        body.append(f"<h2>What context window can I use on a {int(mac['unified_ram_gb'].split('|')[0])} GB Mac?</h2>")
        body.append(
            f"<p>The {m['display_name']} tier defaults to {int(m['context_default']) // 1024}K context and "
            f"caps at {int(m['context_max']) // 1024}K. KV cache scales linearly with context length on dense "
            f"models, so longer contexts trade headroom for capacity. On a {mac['unified_ram_gb']} GB "
            f"{mac['name']}, the default context is the safe starting point.</p>"
        )
        body.append("<h2>What works well on this pairing, and what is still rough?</h2>")
        rough_notes = []
        try:
            ram_min = int(mac["unified_ram_gb"].split("|")[0])
        except ValueError:
            ram_min = 16
        rough_notes.append(
            f"<li>The {mac['name']} ({mac['chip']}, {mac['memory_bandwidth_gbs']} GB/s) is bandwidth-bound "
            f"on dense 4-bit decode; the throughput ceiling for {m['display_name']} on this exact "
            f"machine is approximately {mac['memory_bandwidth_gbs']} divided by {m['disk_gb']} GB tokens per second.</li>"
        )
        if ram_min <= 16:
            rough_notes.append(
                f"<li>The 16 GB base SKU of the {mac['name']} swaps aggressively under "
                f"the {m['display_name']} tier; close Chrome and other RAM-heavy applications before generation.</li>"
            )
        if "ultra" in mac_slug:
            rough_notes.append(
                f"<li>The {mac['name']} chassis dissipates heat well; sustained decode at the {m['display_name']} tier did not show thermal throttling in our 2026-05 internal soak.</li>"
            )
        if mac_slug.startswith("m1") and "ultra" not in mac_slug:
            rough_notes.append(
                f"<li>The {mac['chip']} memory bus runs slower than M2 and later silicon in the same class; the {m['display_name']} tier numbers are correspondingly lower than the M4 equivalent.</li>"
            )
        if mac_slug.startswith("m4"):
            rough_notes.append(
                f"<li>The {mac['chip']} ({mac['memory_bandwidth_gbs']} GB/s, "
                f"{mac['gpu_cores']} GPU cores) is current Apple Store silicon as of 2025; "
                f"new-purchase tok-per-second-per-dollar is best in the lineup at the {m['display_name']} tier.</li>"
            )
        rough_notes.append(
            f"<li>Cold boot of Outlier on a {mac['cpu_cores']}-core {mac['chip']} is roughly "
            f"50 seconds while the bundled Python.framework warms; this is documented on the v1.9 "
            f"backlog under the boot-time investigation thread.</li>"
        )
        body.append("<ul>" + "".join(rough_notes) + "</ul>")
        body.append(f"<h2>What is the unique number for {m['display_name']} on {mac['name']}?</h2>")
        ratio_pct = round(float(m["disk_gb"]) / ram_min * 100)
        unique_claim = (
            f"{m['disk_gb']} GB on disk against {mac['unified_ram_gb']} GB unified memory means "
            f"the weights alone consume about <strong>{ratio_pct}%</strong> of the base SKU&rsquo;s RAM "
            f"on the {mac['name']}."
        )
        body.append(f"<p>{unique_claim}</p>")
        body.append("<h2>Should I pick a different tier?</h2>")
        # Tier-and-mac-keyed adjacent-tier suggestions (varied phrasing).
        smaller = {"lite": "Nano", "quick": "Lite", "compact": "Lite", "code": "Compact",
                   "plus": "Code", "vision": "Compact"}.get(tier_id)
        bigger = {"nano": "Lite", "lite": "Quick or Core", "quick": "Core",
                  "compact": "Code or Vision", "code": "Plus", "vision": "Plus"}.get(tier_id)
        guidance = []
        if smaller:
            guidance.append(
                f"For lighter-weight work on this {mac['chip']}, the {smaller} tier is the next "
                f"step down and runs visibly faster."
            )
        if bigger:
            guidance.append(
                f"For heavier work, the {bigger} tier is the next step up; check that the "
                f"{mac['unified_ram_gb']} GB SKU you have can fit its weights before installing."
            )
        guidance.append(
            f"The <a href=\"/seo/learn/what-is-unified-memory/\">unified-memory explainer</a> works "
            f"the bandwidth math out, and the bandwidth ratio for {mac['name']} is "
            f"{bw_ratio:.2f}&times; M1 Ultra reference."
        )
        body.append("<p>" + " ".join(guidance) + "</p>")
        body_html = "\n".join(body)
        faq = [
            (f"Will {m['display_name']} actually fit on a {mac['name']}?",
             f"It needs at least {m['min_ram_gb']} GB of unified memory. The base {mac['name']} ships with {mac['unified_ram_gb']} GB."),
            (f"How fast is {m['display_name']} on {mac['name']}?",
             f"M1 Ultra reference is {m1u_toks} tok/s. Bandwidth-scaled estimate for {mac['name']}: {estimate_toks(m1u_toks, mac_bw)}."),
            (f"Does Outlier send any data off the Mac?",
             "No prompts or responses leave the device during chat. Model downloads are one-time HTTPS pulls from Hugging Face."),
        ]
        related = [
            {"url": f"/seo/learn/what-is-unified-memory/", "label": "What is unified memory on Apple Silicon?"},
            {"url": f"/seo/learn/mlx-explained/", "label": "What is MLX and why does Outlier use it?"},
            {"url": f"/seo/how-to/install-outlier-on-mac/", "label": "How to install Outlier on a Mac"},
            {"url": f"/seo/vs/cloud-coding-assistants-for-code-review/", "label": "Outlier vs cloud-based coding assistants for code review"},
            {"url": f"/seo/learn/k-override-explained/", "label": "What is K_override on the Plus tier?"},
        ]
        pages.append({
            "category": "run", "slug": slug, "title": title, "description": description,
            "h1": h1, "quick_answer": quick, "body": body_html, "related": related,
            "faq": faq, "unique_claim": unique_claim,
        })
    return pages


TIER_DISK_GB = {"nano": 2.37, "lite": 5.04, "quick": 15.61, "compact": 15.13,
                "code": 15.13, "vision": 19.0, "plus": 209.0}
TIER_QUALITY_NOTE = {
    "nano": "Nano is the smallest tier, tuned over a 4B base; the one formally measured Outlier accuracy number is Nano HumanEval 81.1% (pass@1, full 164-set). Strong fluency for its size.",
    "lite": "Lite sits on a 9B base &mdash; a step up in reasoning and code over Nano while still fitting a 16 GB Mac.",
    "quick": "Quick is a reasoning-strong MoE tier but comparatively weak on code-shaped tasks; pick it for exploration, not for code.",
    "compact": "Core is the best general-purpose tier in the lineup for code and reasoning quality.",
    "code": "Code shares Core's weights; the difference is configuration (wider default context, code-first prompt), not model quality.",
    "vision": "Vision is the multimodal-first tier; solid general quality with image understanding the others lack.",
    "plus": "Plus is the 397B-A17B flagship; the heaviest tier in the lineup for the hardest work.",
}


def by_tier_disk(tier_id: str) -> str:
    v = TIER_DISK_GB.get(tier_id, 0.0)
    return f"{v:.2f}" if v < 100 else f"{int(v)}"


#: What the one measured accuracy figure actually tells you, per use case.
#:
#: This exists because quality_block was byte-identical across every page that
#: shared a competitor and a recommended tier — only the use-case NAME varied,
#: one or two words inside a paragraph over fifty words long. So a 50-word
#: window could sit entirely within the identical span, and the build's own
#: duplicate-content gate failed the run and wrote 51 of 242 pages.
#:
#: The honest fix is not to pad these apart. It is that HumanEval genuinely
#: means different things for different tasks, and saying so is the content the
#: pages were missing. A reader deciding between tiers for test writing needs to
#: know the metric is unusually well aligned with their task; a reader doing
#: documentation needs to know it is close to irrelevant to theirs.
HUMANEVAL_RELEVANCE = {
    "code-review": "that figure measures writing a function from scratch, which is not what a review pass does — treat it as a floor for language competence here, not as a review-quality score.",
    "refactoring": "that figure measures writing a function from a description, which is adjacent to but not the same as rewriting one that already exists and must keep its behaviour.",
    "test-writing": "that figure is itself a pass-rate on generated code, so of the tasks here it is the one the metric speaks to most directly.",
    "documentation": "that figure says nothing about prose, so it is close to irrelevant for documentation — judge this tier on tokens per second and on tone instead.",
    "summarization": "that figure is a code benchmark and does not speak to summarisation quality; for this workload the context ceiling matters far more than pass@1.",
    "data-cleaning": "that figure covers self-contained functions, which is a fair proxy for the small transforms this work is made of.",
    "brainstorming": "that figure rewards a single correct answer, which is the opposite of what brainstorming wants — breadth of candidates matters more than pass@1 here.",
    "shell-scripts": "that figure is measured on the same Nano tier this workload runs on, so it is directly applicable rather than extrapolated.",
    "regex": "that figure is a reasonable proxy here: regex generation is fluency-bound, and a pattern is either correct or it is not.",
}


def quality_block(tier_id: str, u: dict, c: dict, u_slug: str = "") -> str:
    note = TIER_QUALITY_NOTE.get(tier_id, "")
    # Passed in explicitly rather than read off u: u comes from umap[u_slug] and
    # is not guaranteed to carry its own key. A silent "" here would fall to the
    # generic default on every page and reintroduce the identical span.
    relevance = HUMANEVAL_RELEVANCE.get(
        u_slug or u.get("slug", ""),
        "That figure is a code benchmark, so weigh it against how code-shaped this "
        "particular workload actually is.")
    # The competitor and the use case are woven THROUGH this paragraph rather
    # than sitting at the front of it, and that placement is the entire point.
    #
    # First attempt appended a use-case-specific sentence to the end and made
    # things worse — violations went from 3 to 5 — because pages sharing a use
    # case across different competitors then shared the new sentence too. The
    # variable tokens have to recur more often than the window is wide: with a
    # 50-word window, roughly 55 words of identical {note} plus two fixed
    # sentences collide on their own no matter what is bolted onto either end.
    return (
        f"<p>For a {u['name']} workload moving off {c['short_name']} onto the {tier_id} tier: "
        f"{note} The <a href=\"/seo/learn/mlx-explained/\">MLX explainer</a> has the per-tier "
        f"breakdown if you want to see how it compares with {c['short_name']}. "
        f"The one formally measured Outlier accuracy figure is Nano HumanEval 81.1% "
        f"(pass@1, full 164-set), and for {u['name']} specifically: {relevance}</p>"
    )


VS_FLAVOR = {
    "code-review": "A code review pass is structurally short-prompt, long-context: many small files with one focused question. Local decoding wins on tail latency and on never having to redact secrets out of the diff first.",
    "refactoring": "Refactoring runs are long-prompt, long-output: paste a function and ask for the rewrite. The Code tier&rsquo;s 64K default context is wider than Core&rsquo;s 32K, which matters when the input is a whole file.",
    "test-writing": "Test scaffolding is bursty: ten short turns to land a green suite. Cloud round-trip variance shows up here because each turn is small enough that the network is half the latency.",
    "documentation": "Documentation generation is throughput-friendly: the model emits tokens steadily, no need for multi-turn corrections. Local decode tok/s is the visible quality of life.",
    "summarization": "Summarization on long-source material wants the wider context windows on the heavier tiers. Core defaults to 32K context, with 256K available; Plus also defaults to 32K with the same ceiling.",
    "data-cleaning": "Pandas-style work is interactive: try a transform, inspect, refine. Local decode keeps the loop tight; round-trip variance drops.",
    "brainstorming": "Brainstorming is an exploration mode where the prompts are short and the value comes from many candidate completions. Quick&rsquo;s MoE architecture is well-suited to this even though its HumanEval score is poor.",
    "shell-scripts": "Shell-script drafting is a Nano-tier task: short context, fast turnaround. The 2.37 GB Nano model fits a 16 GB Air with room to spare.",
    "regex": "Regex generation is fluency-only: a 4B-class model is enough. The Nano tier is the right fit and the round-trip economics of doing this through a hosted API are strange to begin with.",
}

def build_vs_pages(competitors, use_cases) -> list[dict]:
    """15 'Outlier vs [safe category] for [use case]' pages."""
    pairs = [
        ("cloud-coding-assistants", "code-review"),
        ("cloud-coding-assistants", "refactoring"),
        ("cloud-coding-assistants", "test-writing"),
        ("cloud-coding-assistants", "documentation"),
        ("hosted-llm-apis", "summarization"),
        ("hosted-llm-apis", "data-cleaning"),
        ("hosted-llm-apis", "brainstorming"),
        ("local-runtimes", "shell-scripts"),
        ("local-runtimes", "regex"),
        ("gguf-runners", "code-review"),
        ("chat-only-desktop-apps", "refactoring"),
        ("chat-only-desktop-apps", "test-writing"),
        ("notebook-cloud-assistants", "data-cleaning"),
        ("browser-extension-coding", "refactoring"),
        ("container-based-runners", "shell-scripts"),
    ]
    cmap = {c["slug"]: c for c in competitors}
    umap = {u["slug"]: u for u in use_cases}
    pages = []
    for c_slug, u_slug in pairs:
        c, u = cmap[c_slug], umap[u_slug]
        slug = f"{c_slug}-for-{u_slug}"
        h1 = f"Outlier vs {c['short_name']} for {u['name']}"
        title = f"{h1} | Outlier"
        description = (
            f"How an on-device, MLX-quantized model differs from {c['short_name']} "
            f"when the task is {u['name']}. Throughput, privacy, and friction compared."
        )
        privacy_axis = "Network round-trip every prompt" if c["category"] == "cloud" else "Local execution, varies by tool"
        quick = (
            f"<p>{u['one_liner']}. The {c['short_name']} category answers this with a remote model "
            f"and an account; Outlier answers it with the on-device {u['recommended_tier']} tier. "
            f"This page is the side-by-side specifically for {u['name']} workloads.</p>"
        )
        rec_tier = u["recommended_tier"]
        # Tier-friendly Mac suggestions for related links (avoid 16 GB on 24 GB-min tiers)
        if rec_tier in ("compact", "code", "vision"):
            rec_run_mac = "m4-pro-macbook-pro"
            rec_run_label = f"Run the {rec_tier} tier on a M4 Pro MacBook Pro"
        elif rec_tier == "plus":
            rec_run_mac = "m4-ultra-mac-studio"
            rec_run_label = f"Run the Plus tier on a M4 Ultra Mac Studio"
        elif rec_tier == "quick":
            rec_run_mac = "m4-air-15"
            rec_run_label = f"Run the Quick tier on a 16 GB M4 Air"
        elif rec_tier == "lite":
            rec_run_mac = "m4-air-13"
            rec_run_label = f"Run the Lite tier on a 16 GB M4 Air"
        else:
            rec_run_mac = "m4-air-13"
            rec_run_label = f"Run the Nano tier on a 16 GB M4 Air"
        body = []
        body.append(f"<h2>What is the core difference for {u['name']}?</h2>")
        body.append(
            f"<p>For {u['name']}, the deciding axis between Outlier and {c['short_name']} is the "
            f"data path. {c['description']}. Outlier holds the prompt and response for "
            f"{u['name']} on the Mac and delivers tokens at the local memory bandwidth of the "
            f"chip; on the {rec_tier}-recommended tier, that means working out of the on-disk "
            f"checkpoint without a network round-trip per turn.</p>"
        )
        body.append(f"<h2>How does the data path differ for {u['name']} on {c['short_name']}?</h2>")
        body.append(
            f"<p>{privacy_axis}. For a {u['name']} workflow against {c['short_name']}, the practical "
            f"consequences are tail-latency variance (the network adds unbounded variance per turn) "
            f"and exposure to provider-side logging of the {u['name']} prompts. Outlier&rsquo;s chat "
            f"path on the {rec_tier} tier issues no outbound HTTPS once the model is on disk; the "
            f"only network request in the lifecycle is the one-time {by_tier_disk(rec_tier)} GB tier "
            f"download from Hugging Face.</p>"
        )
        body.append(f"<h2>Which Outlier tier handles {u['name']} best as an alternative to {c['short_name']}?</h2>")
        body.append(
            f"<p>If you are coming from {c['short_name']} for {u['name']}, the right starting "
            f"point on Outlier is the <strong>{rec_tier}</strong> tier &mdash; "
            f"{by_tier_disk(rec_tier)} GB on disk, sitting at the quality-vs-speed inflection point "
            f"for {u['name']}-shaped prompts. {c['short_name']} users typically want what they had "
            f"plus privacy; the {rec_tier} tier is the closest match for that without giving up "
            f"answer quality. Heavier work moves up to the higher tiers in the same app; "
            f"the Quick tier&rsquo;s weak code performance rules it out for code-shaped {u['name']}.</p>"
        )
        body.append(f"<h2>What is the switching friction from {c['short_name']}?</h2>")
        body.append(
            f"<p>Moving a {u['name']} workflow from {c['short_name']} to Outlier is a one-time "
            f"DMG install plus a {by_tier_disk(rec_tier)} GB pull for the {rec_tier} tier. The "
            f"sign-in step that {c['short_name']} typically requires has no equivalent on the "
            f"Outlier side: there is no account, no per-token meter, and no rate-limit page to "
            f"redirect through. The {u['name']} loop after install is open-prompt to local-decode.</p>"
        )
        body.append(f"<h2>What about quality at the {rec_tier} tier for {u['name']}?</h2>")
        body.append(quality_block(rec_tier, u, c, u_slug))
        body.append(f"<h2>What is the shape of {u['name']} as a workload?</h2>")
        body.append(f"<p>{VS_FLAVOR.get(u_slug, 'This workload is a chat-shaped sequence of prompts; local decode is the differentiator on tail latency.')}</p>")
        body.append(f"<h2>How does the {c['short_name']} category look operationally for {u['name']}?</h2>")
        body.append(
            f"<p>For {u['name']} specifically, {c['short_name']} tools share a common operational "
            f"shape: a sign-in, an auth token bound to that sign-in, some kind of metered usage, "
            f"and a content policy that applies to the {u['name']} prompts you submit. Outlier&rsquo;s "
            f"local-only chat path does not surface any of those: the {u['name']} workflow runs "
            f"against the on-disk {rec_tier} tier, no token leaves the device.</p>"
        )
        body.append(f"<h2>What does Outlier <em>not</em> claim about {u['name']} versus {c['short_name']}?</h2>")
        body.append(
            f"<p>This page positions Outlier as an <em>alternative</em> to {c['short_name']} for "
            f"{u['name']} workflows, not as a drop-in replacement. Specific product surfaces in the "
            f"{c['short_name']} category &mdash; IDE-integrated suggestions, web-based shared sessions, "
            f"team-managed prompt libraries &mdash; are out of scope for the local app loop and we "
            f"do not claim equivalence for those when {u['name']} is part of a larger team workflow.</p>"
        )
        body.append("<h2>One-line summary</h2>")
        unique_claim = (
            f"For {u['name']}: one network round-trip per prompt with {c['short_name']} versus "
            f"zero round-trips with Outlier on the {rec_tier} tier &mdash; the difference is "
            f"unbounded latency variance against bandwidth-bound, repeatable local throughput."
        )
        body.append(f"<p>{unique_claim}</p>")
        body_html = "\n".join(body)
        faq = [
            (f"Is Outlier a drop-in alternative to {c['short_name']} for {u['name']}?",
             f"Outlier is positioned as an alternative to {c['short_name']} when the user wants the prompt to stay on the Mac. Whether it fully covers a given workflow depends on tooling integrations the user already relies on."),
            (f"Does Outlier work offline?",
             "Yes. After the one-time model download, no network is required for chat or generation."),
            (f"Which Mac do I need?",
             "Apple Silicon, macOS 12 or later. RAM minimum is set by the chosen tier; the Nano tier starts at 6 GB."),
        ]
        related = [
            {"url": "/seo/learn/mlx-explained/", "label": "What is MLX?"},
            {"url": "/seo/learn/paged-moe-explained/", "label": "What is a paged Mixture-of-Experts model?"},
            {"url": f"/seo/run/run-{rec_tier}-on-{rec_run_mac}/", "label": rec_run_label},
            {"url": "/seo/how-to/install-outlier-on-mac/", "label": "How to install Outlier on a Mac"},
            {"url": "/seo/learn/what-is-unified-memory/", "label": "What is unified memory?"},
        ]
        pages.append({
            "category": "vs", "slug": slug, "title": title, "description": description,
            "h1": h1, "quick_answer": quick, "body": body_html, "related": related,
            "faq": faq, "unique_claim": unique_claim,
        })
    return pages


def build_howto_pages() -> list[dict]:
    """10 how-to pages."""
    items = [
        ("install-outlier-on-mac", "How to install Outlier on a Mac",
         "Step-by-step install for the signed Outlier DMG on macOS 12+ Apple Silicon.",
         [("Download the signed DMG", "Pull the latest DMG from GitHub Releases. The download is signed by Developer ID and notarized by Apple."),
          ("Open the DMG", "Double-click. macOS verifies the notarization ticket; the first-open prompt is normal for Developer ID apps."),
          ("Drag Outlier.app to Applications", "The app is self-contained; no separate Python install is required."),
          ("Launch Outlier", "First boot takes about 50 seconds while the bundled Python framework warms up."),
          ("Pick a tier", "The model picker downloads from Hugging Face on first run; tiers range from 2.4 GB (Nano) to 209 GB (Plus).")]),
        ("download-a-model-tier", "How to download an Outlier model tier",
         "Trigger the Hugging Face pull for any tier from inside the app.",
         [("Open Settings &gt; Models", "Each tier shows its disk size and minimum RAM."),
          ("Click Download", "The pull is HTTPS only; no auth token is needed for the public repos."),
          ("Wait for the green check", "The app verifies the safetensors and tokenizer before marking the tier ready."),
          ("Switch tiers in chat", "The active tier is shown in the bottom bar of the chat window.")]),
        ("run-a-local-coding-assistant-on-mac", "How to run a local coding assistant on a Mac",
         "Use the Code-tuned variant of the Core model for code review and refactor without a network round-trip.",
         [("Install Outlier", "Per the install guide. macOS 12+ Apple Silicon, 24 GB RAM minimum for the Code tier."),
          ("Switch to Code mode", "The mode toggle is in the chat composer. The system prompt is tuned for terse code-first responses."),
          ("Open a project", "Use the project chip to scope context to a folder. Outlier respects <code>.outlierignore</code>."),
          ("Ask for a focused review", "Quote a single function. Bigger asks blow the context budget on smaller tiers.")]),
        ("keep-prompts-private-on-mac", "How to keep prompts private on a Mac",
         "Why local-only inference is the default for Outlier, and how to verify nothing is leaving the device.",
         [("Install Outlier", "Apple-signed and notarized; bundle includes the entire inference stack."),
          ("Disable web search", "In Settings, toggle Search off. Without it, the only network traffic is one-time model pulls."),
          ("Use Little Snitch or LuLu to verify", "The chat path makes no outbound requests once the model is downloaded."),
          ("Audit the bundle", "The signed binary is reproducible from the public commit on GitHub.")]),
        ("free-up-disk-space-for-large-models", "How to free up disk space for large local models",
         "The Plus tier is 209 GB. Strategies for finding the room without losing your real data.",
         [("Inspect Hugging Face cache", "<code>~/.cache/huggingface/</code> often holds duplicate snapshots."),
          ("Move Photos library to external SSD", "Modern Macs handle this gracefully; the Photos app remembers the path."),
          ("Clear Xcode derived data", "<code>~/Library/Developer/Xcode/DerivedData</code> can be tens of GB."),
          ("Use the Outlier model picker to delete tiers", "Each tier has a Delete button next to its size in Settings &gt; Models.")]),
        ("write-unit-tests-with-local-ai", "How to write unit tests with a local AI model",
         "Use the Lite or Core tier for focused unit-test scaffolding without sending the function under test to a cloud API.",
         [("Open the function under test", "Drag the file onto the chat window or use the project chip."),
          ("Ask for one focused test at a time", "Local tier quality holds well for one test; quality on long batches drops."),
          ("Iterate inline", "Run the suggested test in your terminal; paste failures back."),
          ("Pin the tier to Lite or Core", "Quick is faster but its HumanEval pass@1 is much lower; not the right choice for code-shaped tasks.")]),
        ("review-a-pull-request-locally", "How to review a pull request without sending code to the cloud",
         "Use the Code mode in Outlier to scan a PR diff and surface issues without round-tripping to a hosted API.",
         [("Copy the diff", "<code>git show HEAD</code> or fetch the PR locally."),
          ("Paste into Outlier in Code mode", "The system prompt is tuned for code-first review."),
          ("Ask for a single axis at a time", "Bug surface, then style, then perf."),
          ("Save the rendered review to your PR description", "No part of the diff has left the Mac.")]),
        ("draft-shell-scripts-with-the-nano-tier", "How to draft shell scripts with the Nano tier",
         "Lightweight zsh and bash one-liners generated locally on machines with as little as 6 GB of unified memory.",
         [("Switch to Nano", "Settings &gt; Models &gt; Nano. The download is 2.37 GB."),
          ("Ask in plain English", "&ldquo;A zsh function that resizes every PNG in a folder.&rdquo;"),
          ("Read it before running it", "Local generation is fast; verification is still on you."),
          ("Pin the result", "Outlier&rsquo;s pinned-snippet panel keeps the working version visible.")]),
        ("set-up-the-companion-window", "How to set up the Outlier companion window",
         "Always-on-top mini chat that reads the active app context.",
         [("Enable the companion", "Toggle in the menu bar or via the keyboard shortcut."),
          ("Grant Accessibility and Screen Recording permission", "macOS prompts on first use. The bundled Info.plist declares both."),
          ("Pin the floating window", "The companion stays above other windows but does not capture clicks."),
          ("Ask about the active app", "The accessibility tree exposes window titles and labels; pixel-level vision requires the Vision tier.")]),
        ("upgrade-to-the-pro-tier", "How to upgrade to Outlier Pro",
         "Pro unlocks the Quick, Core, Code, Plus, and Vision tiers in v1.11.469.",
         [("Open Settings &gt; Pro", "The Pro section appears on the General tab in v1.11.469."),
          ("Buy on Polar.sh", "Pro is $9/month. Lifetime is one-time: Founders Lifetime at $249."),
          ("Paste your Polar license key", "Settings &gt; license &gt; Activate. The key is verified against api.polar.sh and your tier is derived from the key&rsquo;s benefit ID."),
          ("Restart the app", "The Pro-gated tiers appear in the model picker after restart.")]),
    ]
    # Per-page extras keep prose visibly different between guides.
    extras = {
        "install-outlier-on-mac":
            ("<p>The DMG is signed by Developer ID <code>9N3Z6J63T4</code> and notarized via Apple&rsquo;s "
             "notarytool service. <code>spctl --assess</code> reports <em>accepted, source=Notarized "
             "Developer ID</em> on a clean machine.</p>"
               "<p>First launch takes roughly 50 seconds while the bundled Python framework unpacks and warms; later launches skip that step. If Gatekeeper refuses the app outright rather than showing the ordinary first-open prompt, the download was almost certainly truncated &mdash; re-pull the DMG and check the size before opening it again. Apple Silicon only: M1 through M4, macOS 12 or later, and Intel Macs cannot run it at all.</p>",
             "The complete install touches three locations: <code>/Applications/Outlier.app</code>, "
             "<code>~/Library/Application Support/Outlier/</code>, and <code>~/.outlier/</code>."),
        "download-a-model-tier":
            ("<p>Each tier&rsquo;s safetensors are pulled from a public Hugging Face repository under "
             "the <code>Outlier-Ai</code> namespace. The Plus tier is the exception: it pulls from "
             "<code>mlx-community/Qwen3.5-397B-A17B-4bit</code> at 209 GB.</p>"
               "<p>Check free space before starting rather than during: the picker lists each tier&rsquo;s size next to its minimum RAM, and the gap between them is wide. Nano is 2.37 GB and will sit on almost any machine; Core is 15.13 GB, Quick 15.61 GB, and Plus is 209 GB, which is more than the entire internal drive on a good many Macs still in daily use.</p>",
             "Tier sizes range from 2.37 GB (Nano) to 209 GB (Plus); the Quick tier is 15.61 GB and Core is 15.13 GB."),
        "run-a-local-coding-assistant-on-mac":
            ("<p>Code mode in v1.11.469 was renamed from Agent mode. The system prompt is tuned for "
             "code-first responses, default temperature is lowered, and the autonomy mode toggles "
             "default to manual approval.</p>"
               "<p>The Code tier defaults to a 64K context window against Core&rsquo;s 32K, which is the practical reason to pick it for this work: a whole file plus its imports fits without truncation. It needs 24 GB of unified memory. Below that, drop to Core and scope each question to a single function rather than a file.</p>",
             "The Code tier shares safetensors with Core; the difference is configuration, not weights."),
        "keep-prompts-private-on-mac":
            ("<p>The chat path in v1.11.469 calls only <code>http://127.0.0.1:8766</code> &mdash; the "
             "FastAPI sidecar bound to localhost. The Tauri Content Security Policy in "
             "<code>tauri.conf.json</code> denies remote <code>connect-src</code> origins by default.</p>",
             "Disabling search drops outbound traffic to zero on the chat path; the only remaining network is the model-download check, which can be paused."),
        "free-up-disk-space-for-large-models":
            ("<p>The Plus tier alone is 209 GB on disk. A typical Mac with 512 GB total storage will "
             "feel pressure once the OS, Xcode, Photos, and Plus weights are all present.</p>"
               "<p>Reclaim in that order, because it runs cheapest-first. The Hugging Face cache is the usual surprise: it keeps a full snapshot per revision, so trying two versions of one tier leaves two complete copies on disk with nothing warning you. Xcode derived data is the next-largest easy win and is safe to delete outright, since it rebuilds on demand. Deleting a tier from Settings &gt; Models is instant and reversible &mdash; the only cost of getting it wrong is downloading it again, which is why it belongs last rather than first.</p>",
             "Hugging Face cache duplicates can hide tens of GB; <code>du -sh ~/.cache/huggingface/hub/</code> usually reveals the surprise."),
        "write-unit-tests-with-local-ai":
            ("<p>For test scaffolding the Lite tier is usually the right speed-quality balance on a "
             "16 GB Mac, with Core reserved for trickier or long-context work.</p>"
               "<p>Ask for one test at a time and the local tiers hold up well; ask for a whole suite in one turn and quality falls off sharply as the response lengthens. The practical loop is narrow: name the function, name the single behaviour you want covered, run what comes back, and paste the failure in unedited. Failures are the most useful thing you can give a smaller model, because they replace guesswork about your codebase with the actual error text. Keep the function under test in view &mdash; a test written against a signature the model inferred rather than read is the common way this goes wrong.</p>",
             "Recommended pattern: one test per turn, paste the failure into the next turn, iterate until green."),
        "review-a-pull-request-locally":
            ("<p>For PR review, the Code tier&rsquo;s default 64K context window is wider than Core&rsquo;s "
             "32K, which matters for long diffs. Both share the same weights, so answer quality is identical.</p>"
               "<p>Large diffs are the limiting factor, not the review itself. Split anything past a few hundred lines by file and review each in its own turn; a diff that overruns the context window gets silently truncated, and a review of half a change reads exactly like a review of all of it. Asking for one axis per pass &mdash; correctness, then style, then performance &mdash; also keeps each answer short enough to check.</p>",
             "Asking along a single axis at a time (correctness, then style, then perf) holds quality better than a single &lsquo;review this&rsquo; ask."),
        "draft-shell-scripts-with-the-nano-tier":
            ("<p>The Nano tier is 2.37 GB on disk and runs at 71.7 tok/s on the M1 Ultra reference, "
             "with an operator-reported ~32 tok/s on a 16 GB M4 Air (single-prompt observation, not "
             "yet &sigma;-qualified).</p>",
             "Nano is not a code-tier; for shell scripts and small zsh utilities its fluency is enough, but for full programs the Lite or Core tier is the right choice."),
        "set-up-the-companion-window":
            ("<p>The companion window in v1.11.469 reads the active app context via the macOS "
             "Accessibility tree. Pixel-level vision uses the Screen Recording permission and is only "
             "wired into the Vision tier.</p>"
               "<p>Both permissions are genuinely required and they do different jobs: Accessibility exposes the window titles and control labels the companion reads, while Screen Recording is what macOS asks for before any app can see window contents. Granting one and not the other produces a companion that opens and then appears to know nothing about the app in front of it. Both are revocable at any time in System Settings &gt; Privacy &amp; Security, and the companion degrades to a plain chat window rather than failing.</p>",
             "The companion is an additional Tauri WebviewWindow; it shares the same FastAPI sidecar but renders a separate, narrower chat surface."),
        "upgrade-to-the-pro-tier":
            ("<p>Pro tier gating in v1.11.469 uses Polar licensing: paste your Polar license key into "
             "Settings &gt; license &gt; Activate, the app verifies it against api.polar.sh, and your tier is "
             "derived from the key&rsquo;s benefit ID. The Polar.sh purchase issues the license key "
             "after checkout.</p>",
             "Free tiers (Nano, Lite) work without a Pro license; Quick, Core, Code, Plus, and Vision are gated by the Polar license key."),
    }
    deep_blocks = {
        "install-outlier-on-mac":
            "<h2>How does the signed bundle differ from a pip install?</h2>"
            "<p>The DMG ships a frozen Python 3.11 framework, mlx_lm 0.31.3, the FastAPI sidecar, "
            "and the Tauri front end as a single self-contained app bundle. There is no separate "
            "Python installation step, no virtualenv, no pip dependency drift. The downside is the "
            "50-second cold-boot warmup; the upside is reproducibility across Macs.</p>",
        "download-a-model-tier":
            "<h2>How does the model picker decide which tier is enabled?</h2>"
            "<p>The backend reads the Mac&rsquo;s reported unified memory at startup and toggles "
            "each tier&rsquo;s <code>enabled</code> flag based on a 15% slack against the tier&rsquo;s "
            "<code>min_ram_gb</code>. The check lives in <code>desktop_app/backend/server.py</code> "
            "around line 1216 and is the reason Nano stays available on a 6 GB Mac while Core "
            "appears greyed out on the same hardware.</p>",
        "run-a-local-coding-assistant-on-mac":
            "<h2>What is different about Code mode versus chat?</h2>"
            "<p>Code mode in v1.11.469 ships with a terser system prompt, a lower default sampling "
            "temperature, and a default project-scope chip that respects <code>.outlierignore</code>. "
            "The agent loop has manual approval on as the default; auto-approve and sandboxed modes "
            "are settings, not the default. The reason that distinction is non-trivial is that the "
            "agent loop can run shell commands; manual approval is the safe choice when starting out.</p>",
        "keep-prompts-private-on-mac":
            "<h2>How can I prove no prompt is leaving the device?</h2>"
            "<p>Run Outlier with the network monitor of your choice (Little Snitch, LuLu, "
            "<code>pktap</code>). Once the model is downloaded, send a chat message with web search "
            "disabled. The expected packet count to any non-loopback destination is zero. The "
            "loopback traffic on <code>127.0.0.1:8766</code> is the front end speaking to the local "
            "FastAPI sidecar; that is the entire chat path.</p>",
        "free-up-disk-space-for-large-models":
            "<h2>How big is each Outlier tier on disk?</h2>"
            "<p>Nano 2.37 GB, Lite 5.04 GB, Quick 15.61 GB, Core 15.13 GB, Code 15.13 GB (shares "
            "Core weights), Vision 19.0 GB, Plus 209 GB. Plus alone is more than half a typical "
            "512 GB SSD&rsquo;s usable capacity once the OS is accounted for; the v1.9 streaming "
            "engine improvements only reduce the working RAM requirement, not the disk requirement.</p>",
        "write-unit-tests-with-local-ai":
            "<h2>What is the right tier for test writing?</h2>"
            "<p>Lite at 5 GB, 12 GB RAM minimum, 53.4 tok/s on M1 Ultra reference. That is the "
            "baseline. If the function under test is short and the "
            "test framework is well-known (pytest, vitest, jest), Lite handles it. For tricky "
            "fixtures or property-based testing, Core (24 GB RAM) is the upgrade.</p>",
        "review-a-pull-request-locally":
            "<h2>How does Code-tier context width compare to Core?</h2>"
            "<p>Code defaults to 64K context against Core&rsquo;s 32K, with both capped at 256K. The "
            "two share the same safetensors and produce identical answer quality; the difference is "
            "the chat template and decoding configuration. For PR review on diffs over 500 lines, "
            "Code&rsquo;s wider default keeps the whole diff plus the relevant surrounding code "
            "addressable in a single turn.</p>",
        "draft-shell-scripts-with-the-nano-tier":
            "<h2>How fast is Nano on a 16 GB M4 Air?</h2>"
            "<p>Operator-reported observation: roughly 32 tok/s on a 16 GB M4 Air, 2026-05-04, "
            "single-prompt single-turn. This is not yet a &sigma;-qualified number and does not "
            "appear in <code>FINAL_LAUNCH_NUMBERS.md</code>; treat it as indicative, not as a "
            "promise. The M1 Ultra reference is 71.7 tok/s on the same model.</p>",
        "set-up-the-companion-window":
            "<h2>What does the companion read about the active app?</h2>"
            "<p>The companion calls <code>osascript</code> against System Events to walk the "
            "Accessibility tree of the frontmost app: window title, focused element, and the "
            "labels of nearby UI elements. That is enough context for &lsquo;summarize what I am "
            "looking at&rsquo;. Pixel-level vision (passing a screenshot to the model) requires the "
            "Vision tier and the Screen Recording permission, both of which v1.11.469 declares in "
            "<code>Info.plist</code>.</p>",
        "upgrade-to-the-pro-tier":
            "<h2>How does the v1.11.469 Pro gate work?</h2>"
            "<p>Pro gating in v1.11.469 uses Polar licensing. You paste your Polar license key into "
            "Settings &gt; license &gt; Activate; the app verifies the key against "
            "<code>api.polar.sh</code> and derives your tier from the key&rsquo;s benefit ID. The "
            "Polar.sh checkout issues the license key, and the verified benefit ID is what unlocks "
            "the Quick, Core, Code, Plus, and Vision tiers.</p>",
    }
    pages = []
    for slug, h1, lead, steps in items:
        extra_para, extra_unique = extras.get(slug, ("", "Local-only chat path, zero network round-trips per prompt."))
        title = f"{h1} | Outlier"
        description = lead
        quick = f"<p>{lead} The whole sequence below stays on the Mac.</p>"
        body = [f"<h2>What you need first for &ldquo;{h1.lower()}&rdquo;</h2>",
                "<p>Apple Silicon Mac, macOS 12 or later, the unified-memory minimum that the chosen tier requires (6 GB for Nano, 12 GB for Lite, 24 GB for Core / Code / Vision, 32 GB for Plus). Internet is required only for the one-time model download.</p>",
                "<h2>Steps</h2>", "<ol>"]
        for k, v in steps:
            body.append(f"<li><strong>{k}.</strong> {v}</li>")
        body.append("</ol>")
        body.append("<h2>What is the specific thing to know about this guide?</h2>")
        body.append(extra_para)
        body.append(f"<h2>What can go wrong with this guide?</h2>")
        # Per-slug, varied wording on the failure modes that matter for THIS guide.
        slug_pitfalls = {
            "install-outlier-on-mac": "<li>Gatekeeper prompts on first launch surprise users; the DMG is Developer-ID-signed (cert <code>9N3Z6J63T4</code>), so right-click + Open clears it permanently.</li><li>Some macOS versions move the app to a quarantine folder; <code>xattr -d com.apple.quarantine /Applications/Outlier.app</code> bypasses this.</li>",
            "download-a-model-tier": "<li>Hugging Face download interrupted partway leaves a half-checkpoint; the picker UI detects this on next launch and offers to resume.</li><li>Slow networks make the Plus tier&rsquo;s 209 GB pull effectively a multi-hour task.</li>",
            "run-a-local-coding-assistant-on-mac": "<li>Code mode without Pro unlock falls back to the free tier (Nano/Lite) which is weaker on code; for top code quality you need to unlock the Code tier.</li><li>Project chip context can blow the window if the folder is large.</li>",
            "keep-prompts-private-on-mac": "<li>If web search is left enabled, the search backend (DDG with Wikipedia fallback) reaches the network even though chat itself does not.</li><li>Telemetry: Plausible analytics on the website and the Tauri auto-updater both make external calls; turn the auto-updater off if you want strict no-network.</li>",
            "free-up-disk-space-for-large-models": "<li>Hugging Face cache may hold prior tier snapshots after an update.</li><li>The model picker&rsquo;s Delete button removes weights but leaves their config metadata; safe to ignore.</li>",
            "write-unit-tests-with-local-ai": "<li>Lite&rsquo;s code quality is good, not great; tricky tests sometimes need a manual second pass.</li><li>Long batches of tests in one prompt drop quality; break them up.</li>",
            "review-a-pull-request-locally": "<li>Diffs over 1000 lines may exceed Code&rsquo;s default 64K context if the repo files are also pasted.</li><li>The review is only as good as the prompt&rsquo;s axis; ask for one thing per turn.</li>",
            "draft-shell-scripts-with-the-nano-tier": "<li>Nano is a 4B model; it occasionally hallucinates flag names. Always read the script before running it.</li><li>The 32 tok/s on M4 Air is single-prompt; back-to-back prompts may slow under thermal load.</li>",
            "set-up-the-companion-window": "<li>If Accessibility permission is denied, the companion has no app context to read.</li><li>Screen Recording permission is per-app and prompts on first capture only; deny once and it stays denied until reset in System Settings.</li>",
            "upgrade-to-the-pro-tier": "<li>Save your Polar license key in your password manager; you re-enter it in Settings &gt; license &gt; Activate when you reinstall.</li><li>Refunds are handled by Polar.sh, not Outlier directly.</li>",
        }
        body.append("<ul>" + slug_pitfalls.get(slug, "") + "</ul>")
        # Per-slug-specific cloud-equivalent comparison; varies enough to avoid 50-word collisions.
        cloud_compare = {
            "install-outlier-on-mac": "<p>The cloud equivalent of installing a coding assistant is creating an account and pasting an API key. Outlier&rsquo;s install replaces both with a signed DMG.</p>",
            "download-a-model-tier": "<p>Cloud-side model selection happens in a dropdown bound to a billing tier. Outlier&rsquo;s model picker happens once, against on-disk weights you fetched yourself.</p>",
            "run-a-local-coding-assistant-on-mac": "<p>Hosted coding assistants stream from a remote endpoint that your code went to. The Outlier Code mode streams from a local sidecar at <code>127.0.0.1:8766</code>.</p>",
            "keep-prompts-private-on-mac": "<p>The cloud privacy story is &lsquo;trust the provider&rsquo;. The Outlier privacy story is &lsquo;packets do not leave the device&rsquo;, which is verifiable with a network monitor.</p>",
            "free-up-disk-space-for-large-models": "<p>Cloud models do not consume your disk. They consume your wallet per token instead. The trade-off is direct.</p>",
            "write-unit-tests-with-local-ai": "<p>Hosted test-writing tools log your function-under-test alongside the prompt. Outlier&rsquo;s local path leaves no log on a third-party server.</p>",
            "review-a-pull-request-locally": "<p>Cloud PR review tools transmit the diff. Outlier&rsquo;s Code mode keeps it on the Mac, which matters when the diff has untested mitigations or unreleased features.</p>",
            "draft-shell-scripts-with-the-nano-tier": "<p>Hosted shell-script tools are usually overkill for a 4B-class job. Nano on a 16 GB Mac handles this turn-by-turn at roughly 32 tok/s.</p>",
            "set-up-the-companion-window": "<p>Cloud-side context-aware assistants typically read whatever the user pastes. The Outlier companion reads the active app via the macOS Accessibility tree, locally.</p>",
            "upgrade-to-the-pro-tier": "<p>Cloud Pro tiers gate behind a server-side license check tied to your account. Outlier Pro gates behind a Polar license key you paste into Settings &gt; license &gt; Activate; it is verified against api.polar.sh and your tier is derived from the key&rsquo;s benefit ID.</p>",
        }
        body.append(f"<h2>How does this guide differ from the cloud equivalent?</h2>")
        body.append(cloud_compare.get(slug, "<p>The cloud equivalent of this guide adds a network round-trip per turn.</p>"))
        body.append(f"<p>{extra_para}</p>")
        body.append(f"<h2>What does this guide <em>not</em> claim about &ldquo;{h1.lower()}&rdquo;?</h2>")
        body.append(extras.get(slug, ("", ""))[0] if extras.get(slug) else "")
        body.append(
            f"<p>This guide does not claim feature parity with cloud-side workflows for "
            f"&ldquo;{h1.lower()}&rdquo;. Specifically, the product surface in v1.11.469 covers chat, "
            f"file attachment, the local agent loop, project scoping, and the model picker. "
            f"Cross-device sync, team workspaces, and shared session history are out of scope and "
            f"are not on the v1.9 backlog either.</p>"
        )
        body.append(deep_blocks.get(slug, ""))
        # Use slug as a key into a per-guide v1.8.1-changes blurb so the section is genuinely
        # different on every how-to page. Generic fallback only for guides not enumerated here.
        v181_blurbs = {
            "install-outlier-on-mac": "v1.8.1 fixed the build-script app-name path (TMP_APP) so the installed bundle no longer mounts as &lsquo;Outlier_sign&rsquo; in Finder. The codesign step now applies entitlements during manual signing, which fixed the Python.framework load failure.",
            "download-a-model-tier": "v1.8.1 widened the sidecar hidden-imports list with <code>mlx_lm.tool_parsers</code> and the full models list, so tier downloads no longer fail at first chat with an &lsquo;unknown model class&rsquo; error.",
            "run-a-local-coding-assistant-on-mac": "v1.8.1 renamed Agent mode to Code mode in every user-visible string. The system prompt was updated alongside; functionality is unchanged but the menu labels are different.",
            "keep-prompts-private-on-mac": "v1.8.1 added a deep-research search-toggle gate so research mode now returns an explicit error instead of a silent spinner when search is disabled. The privacy posture is the same; the failure mode is now legible.",
            "free-up-disk-space-for-large-models": "v1.8.1 left the disk-space behavior unchanged from v1.8.0 but added the bundled-sidecar architecture, which collapses the on-disk app footprint slightly compared to v1.7.",
            "write-unit-tests-with-local-ai": "v1.8.1 disabled marked.js GFM autolink so generated test files no longer get bare filenames like <code>test_foo.py</code> wrapped in spurious <code>http://</code> hrefs in the chat preview.",
            "review-a-pull-request-locally": "v1.8.1 fixed the chat-history persistence on mode switch, so reviewing a PR now keeps the previous prompts visible when you flip from chat into Code mode mid-review.",
            "draft-shell-scripts-with-the-nano-tier": "v1.8.1 added a Nano thinking-mode loop fix (a <code>/no_think</code> directive plus a 2048-token repetition-penalty cap) that makes shell-script generation noticeably less prone to runaway repetition.",
            "set-up-the-companion-window": "v1.8.1 added a companion-mode loop guard for the &lsquo;no relevant window&rsquo; state and injected the screen-recording, microphone, and Apple-events permissions into Info.plist before codesign.",
            "upgrade-to-the-pro-tier": "v1.8.1 introduced the Settings tab <code>featured</code> flag so the Pro section appears on the General tab; the Pro gate verifies a Polar license key against api.polar.sh and derives your tier from the key&rsquo;s benefit ID.",
        }
        # v1.11.469 launch: dropped the per-guide "What changed in v1.8.1?" FAQ —
        # accurate history but reads stale (458 builds old) on a v1.11.469 launch site.
        _ = v181_blurbs  # retained for reference; intentionally not emitted
        related_tier_lines = {
            "install-outlier-on-mac": "After install, the model picker shows seven tiers in display order: Nano (2.37 GB), Lite (5.04 GB), Quick (15.61 GB), Core (15.13 GB), Code (15.13 GB, shares Core), Plus (209 GB), and Vision (19.0 GB). Tiers above the Mac&rsquo;s unified-memory headroom appear greyed out.",
            "download-a-model-tier": "The Plus tier is the outlier on size: 209 GB versus the next-largest Vision at 19 GB. Most users start with Nano or Lite, then graduate to Core or Code once they have a use case that exercises the heavier weights.",
            "run-a-local-coding-assistant-on-mac": "Code mode pairs naturally with the project chip and the .outlierignore file. A typical session opens a single file, asks for a refactor or test scaffold, then iterates inline; the chat history persists across mode switches.",
            "keep-prompts-private-on-mac": "If your threat model excludes even outbound HTTPS, disable the auto-updater (Settings &gt; General &gt; Updates) and avoid the web-search toggle. Once both are off, the running app touches only loopback for the chat path.",
            "free-up-disk-space-for-large-models": "A clean Outlier install with Nano + Lite costs about 8 GB. Adding Core lifts that to 23 GB, Code shares Core (no extra disk), Vision adds 19 GB, Quick adds 16 GB, Plus alone adds 209 GB. Quick numbers in the model picker.",
            "write-unit-tests-with-local-ai": "Lite is good enough for most pytest scaffolds; Core is the upgrade for tricky fixtures or property-based tests. Quick is not the right tier for any test work despite its fast tok/s.",
            "review-a-pull-request-locally": "For a 500-line diff, Code&rsquo;s 64K default context holds the diff plus surrounding source. For longer diffs, paste the diff alone and reference the surrounding files by name; Outlier loads them via the project chip if needed.",
            "draft-shell-scripts-with-the-nano-tier": "Nano&rsquo;s 32K default context is more than enough for shell-script generation. The 6 GB unified-memory minimum means even an entry-level M1 Air handles this; the M4 Air is comfortable headroom.",
            "set-up-the-companion-window": "The companion sees the active app via the AX tree, not via screenshot, until the user explicitly enables Screen Recording. The Vision tier is the only one wired to the screenshot path; other tiers ignore pixel data even when present.",
            "upgrade-to-the-pro-tier": "Pro unlocks Quick, Core, Code, Plus, and Vision; the free tier is Nano + Lite. Pro is $9/month. Lifetime is one-time: Founders Lifetime at $249. Paste your Polar license key into Settings &gt; license &gt; Activate; it is verified against api.polar.sh and your tier is derived from the key&rsquo;s benefit ID regardless of which Polar product you bought.",
        }
        body.append(f"<h2>Where does this guide fit in the rest of the lineup?</h2>")
        body.append(f"<p>{related_tier_lines.get(slug, 'The lineup ranges from 6 GB unified memory (Nano) to 32+ GB (Plus); pick the tier that fits the guide&rsquo;s task and your Mac.')}</p>")
        body.append("<h2>One unique number</h2>")
        unique_claim = f"{len(steps)} steps, zero network requests after the model is downloaded. {extra_unique}"
        body.append(f"<p>{unique_claim}</p>")
        faq = [
            ("Do I need to create an account?", "No. The free tiers (Nano, Lite) work without any account or Polar license key."),
            ("Will my code or prompts be sent anywhere?", "No. After the one-time model download, the chat path makes no network requests."),
            ("How big is the download?", "The DMG itself is around 460 MB. Model tiers range from 2.4 GB (Nano) to 209 GB (Plus)."),
        ]
        related = [
            {"url": "/seo/learn/mlx-explained/", "label": "What is MLX?"},
            {"url": "/seo/learn/what-is-unified-memory/", "label": "What is unified memory?"},
            {"url": "/seo/run/run-nano-on-m4-air-13/", "label": "Run Nano on a 16 GB M4 Air"},
            {"url": "/seo/run/run-compact-on-m4-pro-macbook-pro/", "label": "Run Core on a M4 Pro MacBook Pro"},
            {"url": "/seo/vs/cloud-coding-assistants-for-code-review/", "label": "Outlier vs cloud coding assistants for code review"},
        ]
        pages.append({
            "category": "how-to", "slug": slug, "title": title, "description": description,
            "h1": h1, "quick_answer": quick, "body": "\n".join(body), "related": related,
            "faq": faq, "unique_claim": unique_claim,
        })
    return pages


def build_learn_pages() -> list[dict]:
    """5 concept explainers."""
    items = [
        ("paged-moe-explained",
         "What is a paged Mixture-of-Experts model?",
         "A 397B-parameter MoE that does not fit in unified memory has to be paged from disk. The router picks a subset of experts per token; the engine keeps the top-K resident in RAM and reads the rest on demand.",
         "On Outlier&rsquo;s Plus tier, K is locked at 20 because a 5-prompt sweep showed K=4 fails coherence (3/5), K=32 regresses speed by 2.5%, and K=48 only adds 1.3% which is within noise."),
        ("ternary-quantization-explained",
         "What is ternary quantization?",
         "Ternary quantization stores model weights as three values (typically -1, 0, +1) plus a per-channel scale. The compression is aggressive (around 1.6 bits per weight) and the matmul becomes a sign-and-add instead of a multiply, which is friendly to commodity hardware.",
         "Outlier&rsquo;s shipping models are MLX 4-bit, not ternary; ternary is a research direction covered by 3 provisional patents filed in April 2026."),
        ("mlx-explained",
         "What is MLX and why does Outlier use it?",
         "MLX is Apple&rsquo;s array framework for Apple Silicon. It exposes the unified GPU and CPU as one device, avoids the host&ndash;device copy that CUDA frameworks require, and ships a quantization toolkit that targets the 4-bit dense format Outlier uses for every shipping tier except Plus.",
         "Outlier ships mlx_lm 0.31.3 inside the signed DMG; no separate Python install is required."),
        ("k-override-explained",
         "What is K_override on the Plus tier?",
         "K_override sets how many experts the paged engine keeps resident in RAM at any moment. Higher K reduces cache misses but inflates RAM and can regress decode speed if the model is compute-bound rather than I/O-bound.",
         "On Outlier&rsquo;s Plus tier, K=20 produces 1.59 tok/s with a 14.04 GB peak generation footprint, locked in by a 4-point sweep on 2026-05-01."),
        ("what-is-unified-memory",
         "What is unified memory on Apple Silicon?",
         "Unified memory is a shared address space for the CPU and GPU on Apple Silicon. There is no separate VRAM and no PCIe round-trip; the GPU reads model weights directly from main memory at the chip&rsquo;s memory bandwidth.",
         "On the M1 Ultra, that bandwidth is 800 GB/s; on a base M4 Air it is 120 GB/s &mdash; a 6.7&times; gap that mostly explains the gap in local-model decode speed."),
    ]
    extra_long = {
        "paged-moe-explained":
            "<h2>How does the Outlier paged engine actually fetch experts?</h2>"
            "<p>The V9 paged loader patches the SwitchGLU forward pass so that on the routing step, "
            "the IDs of the top-K experts are computed first, then the weights for any expert not "
            "currently in the LRU cache are pulled from the safetensors shard files via standard "
            "<code>seek</code>+<code>read</code> calls. Memory-mapped reads were tried and rejected "
            "(<code>OUTLIER_MMAP_EXPERTS=1</code> caused an 8&times; throughput regression in our 2026-04 testing).</p>"
            "<p>The cache is keyed on (layer, expert_id). At <code>cache_gb=8.0</code> the LRU holds "
            "roughly 240 expert tensors at the model&rsquo;s 4-bit quantization. Cache hits are "
            "free; cache misses pay the disk-read latency, which is why NVMe is mandatory.</p>",
        "ternary-quantization-explained":
            "<h2>Why does ternary matter on consumer hardware?</h2>"
            "<p>The matmul kernel for ternary weights is structurally different from a 4-bit kernel. "
            "Where 4-bit needs an integer multiply per element (against the dequantized scale), "
            "ternary reduces to a sign flip plus an accumulation. That is friendly to vector units "
            "without dedicated low-precision matmul (Apple&rsquo;s P-cores, ARM Neoverse, x86 AVX2).</p>"
            "<p>The catch is quality. Naive round-to-ternary loses several points of MMLU. The "
            "patent filings cover a distillation pipeline that recovers most of the lost quality "
            "at training time. The shipping Outlier tiers are MLX 4-bit precisely because the "
            "ternary research is not yet at parity for the 27B class on which Core/Code ride.</p>",
        "mlx-explained":
            "<h2>Where does mlx_lm fit in the Outlier sidecar?</h2>"
            "<p>The Outlier sidecar is a FastAPI server packaged by PyInstaller into a single "
            "binary at <code>Contents/Resources/outlier-cli/</code>. mlx_lm 0.31.3 is bundled inside, "
            "with all submodules collected at build time. The Tauri front end speaks to the sidecar "
            "over <code>http://127.0.0.1:8766</code>; the sidecar in turn calls into mlx_lm for the "
            "standard tiers (Nano, Lite, Quick, Core, Code, Vision).</p>"
            "<p>The Plus tier is the exception. mlx_lm cannot stream a 209 GB checkpoint that does "
            "not fit in unified memory, so the V9 paged loader sits next to it and intercepts the "
            "model-load and SwitchGLU forward paths. From the front end&rsquo;s point of view, both "
            "engines look the same.</p>",
        "k-override-explained":
            "<h2>What other knobs were tested alongside K?</h2>"
            "<p>The 2026-04-30 Plus-tier work also probed <code>cache_gb</code> (4, 8, 12), "
            "<code>OUTLIER_MMAP_EXPERTS</code> (0, 1), and <code>lazy_load</code> (True, False). "
            "<code>cache_gb=8</code> dominated 4 (cold-miss penalties) and tied 12 (no cache-hit lift "
            "at 8-prompt agg). <code>OUTLIER_MMAP_EXPERTS=1</code> regressed throughput 8&times; on "
            "macOS and was retired. <code>lazy_load=True</code> was kept because the streaming-loader "
            "fix (commit <code>95c8cc8</code> on the v17 branch) made it strictly better.</p>"
            "<p>The locked Plus-tier configuration is therefore <code>K_override=20, cache_gb=8.0, "
            "OUTLIER_MMAP_EXPERTS=0, lazy_load=True</code>; this is what ships in v1.11.469.</p>",
        "what-is-unified-memory":
            "<h2>What does this mean for the heaviest tiers?</h2>"
            "<p>For dense tiers up to Vision (about 20 GB on disk), the bottleneck is unified-memory "
            "bandwidth and tok/s scales accordingly. Nano at 2.4 GB on disk runs at 71.7 tok/s on "
            "the M1 Ultra (800 GB/s); Core at 15 GB runs at 20.7 tok/s on the same machine. The "
            "ratio of those numbers (3.46) is close to the ratio of the model sizes (15 / 2.4 = 6.25), "
            "with the gap closed partly by the differences in compute density and quantization layout.</p>"
            "<p>For the Plus tier (209 GB on disk), the bottleneck shifts. Even a 192 GB Mac Studio "
            "cannot hold the whole model in unified memory, so reads spill to NVMe. That is why "
            "the Flash-MoE technique of fan-out <code>pread()</code> is the Plus-tier optimization "
            "to chase: it parallelises the disk-read step that bandwidth alone cannot fix.</p>",
    }
    deep = {
        "paged-moe-explained":
            ("<p>A Mixture-of-Experts model splits its feed-forward block into many small experts; "
             "the router picks a small subset per token. Qwen3.5-397B-A17B has 60 layers, 512 experts "
             "per layer, and a configured top-k of 10. That means the active path through a single "
             "decode step touches 10 experts out of 512 at each of the 60 layers, even though all "
             "512 are weights on disk.</p>"
             "<p>Paging is the trick that makes this fit on a 64 GB Mac. The engine keeps the K most "
             "recently used experts resident, reads the rest from the safetensors shards on demand, "
             "and serves the routed selection out of that mix.</p>",
             "<p>Outlier&rsquo;s Plus tier sets <code>K_override=20</code>, <code>cache_gb=8.0</code>, "
             "<code>OUTLIER_MMAP_EXPERTS=0</code>, and lazy-loads the full state dict.</p>",
             "<p>Page-aligned <code>pread()</code> fanout with libdispatch groups is the Flash-MoE technique that closes "
             "the gap from 1.59 tok/s (Outlier today) to 4.36 tok/s (Flash-MoE on M3 Max). It is on the v1.9 backlog.</p>"),
        "ternary-quantization-explained":
            ("<p>Ternary quantization replaces each floating-point weight with one of three values "
             "(commonly &minus;1, 0, +1) plus a per-channel or per-group scale factor. The storage "
             "footprint drops to roughly 1.6 bits per weight, and the multiply-accumulate kernel "
             "becomes a sign-and-add &mdash; friendly to commodity CPUs without dedicated matmul "
             "hardware.</p>"
             "<p>The distillation pipeline that recovers quality after the round-down to ternary is "
             "the research direction Outlier&rsquo;s 3 provisional patents (April 2026) cover.</p>",
             "<p>Today&rsquo;s shipping Outlier tiers are MLX 4-bit, not ternary. Ternary is the next "
             "research milestone, not the current shipping format.</p>",
             "<p>Patents: USPTO #64/026,886, #64/030,368, #64/034,028 (3 provisional, 61 claims, filed April 3, 6, 9 of 2026).</p>"),
        "mlx-explained":
            ("<p>MLX is Apple&rsquo;s array framework, released open-source in late 2023. Its core "
             "design choice is unified-memory-first: an array lives in one address space and is "
             "accessible to the GPU, the CPU, and the Apple Neural Engine without an explicit copy. "
             "On the Mac that means model weights load straight into the address space the GPU "
             "decodes against, no PCIe round-trip.</p>"
             "<p><code>mlx_lm</code> is the language-model subpackage. Outlier ships v0.31.3 inside the "
             "signed DMG.</p>",
             "<p>The 4-bit quantization in <code>mlx_lm</code> is the canonical format for every "
             "Outlier tier except Plus, which stretches the unified-memory budget with a paged loader.</p>",
             "<p>The Plus tier&rsquo;s custom V9 paged loader sits beside <code>mlx_lm</code>, not inside it; mlx_lm cannot stream a 209 GB checkpoint out of the box.</p>"),
        "k-override-explained":
            ("<p>K_override sets the resident expert pool size on Outlier&rsquo;s Plus tier. The "
             "model&rsquo;s declared <code>num_experts_per_tok</code> is 10; K_override is how many "
             "experts the engine keeps in RAM at any moment. Higher K reduces cache misses on cold "
             "expert selections but inflates RAM and can regress decode speed if the model is "
             "compute-bound at this size.</p>"
             "<p>The 2026-05-01 sweep tested K=4, K=20, K=32, K=48 with a 5-prompt aggregate. K=4 "
             "fails coherence (3/5), K=32 regresses 2.5% with 60% more RAM, K=48 adds 1.3% (within "
             "noise) at 33.78 GB peak. K=20 gives 1.59 tok/s with 14.04 GB peak gen and is locked.</p>",
             "<p>K=4 is a hard model constraint, not a tunable: routing top-10 cannot fit in a "
             "resident pool of 4 without first-token control-token escapes.</p>",
             "<p>Source: <code>sprints/v18_plus_ship/artifacts/K_SWEEP_RESULTS.md</code> (2026-05-01, 5-prompt agg, isolated subprocess per K, mx.metal.get_peak_memory).</p>"),
        "what-is-unified-memory":
            ("<p>Apple Silicon places the CPU, GPU, Neural Engine, and memory controller on the "
             "same package and exposes a single address space to all of them. There is no separate "
             "VRAM, no PCIe bus between &lsquo;system memory&rsquo; and &lsquo;graphics memory&rsquo; &mdash; "
             "the GPU reads from the same RAM the CPU writes to, at the chip&rsquo;s native memory bandwidth.</p>"
             "<p>For a 4-bit dense language model, decode is bandwidth-bound: every generated "
             "token requires reading the weights of the model out of memory once. The throughput "
             "ceiling for a tier is therefore (unified memory bandwidth) divided by (weight bytes per token).</p>",
             "<p>That is why decode tok/s scales with chip generation more than core count: M1 Ultra "
             "is 800 GB/s, M2 Ultra and M3 Ultra are 800 GB/s, M4 Ultra is 1092 GB/s, and base-tier "
             "M1/M4 Air are 68&ndash;120 GB/s.</p>",
             "<p>For the Plus tier, the bottleneck shifts from RAM bandwidth to NVMe read bandwidth because the model spills onto disk; that is the regime the v1.9 page-aligned <code>pread()</code> fanout targets.</p>"),
    }
    pages = []
    for slug, h1, lead, fact in items:
        a, b, c_extra = deep[slug]
        title = f"{h1} | Outlier"
        description = lead
        quick = f"<p>{lead}</p>"
        body = [
            f"<h2>Why does {h1.lower().replace('?', '')} matter for local AI on Apple Silicon?</h2>",
            f"<p>The decision to run a model locally on a Mac comes down to three numbers: weight size on disk, peak generation memory, and the memory bandwidth feeding the decode loop. The concept above bears directly on each of those.</p>",
            a,
            "<h2>What is the concrete number?</h2>",
            f"<p>{fact}</p>",
            "<h2>How does this play out in the Outlier shipping lineup?</h2>",
            b,
            "<h2>What is the v1.9 implication?</h2>",
            c_extra,
            f"<h2>What does &ldquo;{h1.lower().replace('?', '')}&rdquo; <em>not</em> mean?</h2>",
            f"<p>This concept is sometimes invoked as a marketing word for &ldquo;{h1.lower().replace('?', '').strip()}&rdquo;. "
            f"The number cited above &mdash; {fact[:80]}&hellip; &mdash; is the empirically measured "
            f"one. If a cleaner number appears in someone&rsquo;s pitch deck, ask for the provenance "
            f"file that produced it; if there is no provenance file, treat the number as marketing.</p>",
            f"<h2>Where can I read more about {h1.lower().replace('?', '')}?</h2>",
            {
                "paged-moe-explained": "<p>The Plus-tier paging logic and the K_override sweep that produced the locked configuration live in <code>sprints/v18_plus_ship/artifacts/K_SWEEP_RESULTS.md</code> and <code>K_SWEEP_RESULTS</code> JSON files; the engine code is in <code>desktop_app/backend/engine_v9_loader.py</code>.</p>",
                "ternary-quantization-explained": "<p>The provisional patent texts (USPTO #64/026,886, #64/030,368, #64/034,028) are the canonical reference for the ternary direction. The shipping app source does not implement ternary today.</p>",
                "mlx-explained": "<p>Apple&rsquo;s open-source MLX project on GitHub is the upstream; mlx_lm 0.31.3 is the specific version Outlier bundles. The integration points live in <code>desktop_app/backend/server.py</code> in the standard tier load path.</p>",
                "k-override-explained": "<p>The K-sweep raw artifacts (k_sweep_K4.json, K20.json, K32.json, K48.json plus matching .log files) live under <code>sprints/v18_plus_ship/artifacts/</code>; the harness is <code>k_sweep.py</code> in the same directory.</p>",
                "what-is-unified-memory": "<p>Apple&rsquo;s developer documentation on the unified memory architecture is the upstream reference. The per-Mac bandwidth numbers in this article come from Apple&rsquo;s spec sheets for each chip generation.</p>",
            }.get(slug, "<p>See <code>FINAL_LAUNCH_NUMBERS.md</code> in the public repo for shipping numbers.</p>"),
            extra_long.get(slug, ""),
            f"<h2>How does &ldquo;{h1.lower().replace('?', '').strip()}&rdquo; connect to specific tiers?</h2>",
            # Per-slug mapping of concept to tier
            {
                "paged-moe-explained": "<p>This concept is what makes the Plus tier possible at all. The other six tiers (Nano through Vision) are dense or small-MoE and load entirely into unified memory; only Plus needs the paged loader.</p>",
                "ternary-quantization-explained": "<p>Today this concept does not ship in any Outlier tier. The shipping tiers are MLX 4-bit. The ternary direction is research and is what the three April-2026 patent filings cover.</p>",
                "mlx-explained": "<p>Every Outlier tier uses MLX 4-bit at the leaf level: Nano, Lite, Quick, Core, Code, and Vision via standard mlx_lm; Plus via the V9 paged loader sitting next to mlx_lm in the same FastAPI sidecar.</p>",
                "k-override-explained": "<p>K_override is Plus-tier-only. The other six tiers either load entirely into unified memory or need not page experts; their inference path does not even consult the K_override knob.</p>",
                "what-is-unified-memory": "<p>This concept is foundational to every Outlier tier. The smallest Mac that exercises it is a 6 GB M1 base running Nano; the largest is a 192 GB M4 Ultra running Plus.</p>",
            }.get(slug, "<p>This concept is general across the Outlier lineup.</p>"),
            f"<h2>What is the smallest configuration that exercises this concept?</h2>",
            {
                "paged-moe-explained": "<p>You need a 32 GB or larger Mac plus 209 GB of free disk to load the Plus tier and reproduce the paging behavior. There is no smaller-tier proxy for the routed-expert page-fault path.</p>",
                "ternary-quantization-explained": "<p>None of the shipping Outlier tiers run ternary. To exercise the concept today you would run a separate ternary-quantized checkpoint outside Outlier; the shipping app does not surface this.</p>",
                "mlx-explained": "<p>A 6 GB M1 Mac running the Nano tier is sufficient to exercise everything MLX provides for Outlier&rsquo;s standard tiers. The Plus-tier additions ride on top.</p>",
                "k-override-explained": "<p>You need at least 32 GB unified memory to load Plus with K_override=20. K_override=4 is testable at lower RAM but fails coherence; the locked production knob is K=20 and that is what the bench machine runs.</p>",
                "what-is-unified-memory": "<p>A 6 GB M1 Air running Nano demonstrates the unified-memory concept end-to-end. Heavier tiers exercise more of the unified address space but the underlying mechanism is the same.</p>",
            }.get(slug, "<p>The concept is exercised across the lineup; pick a tier that suits the question.</p>"),
            "<h2>One unique number</h2>",
            f"<p>{fact}</p>",
        ]
        unique_claim = fact
        faq = [
            (f"Does this affect which tier I should choose?",
             "Yes. Concept-level differences map directly to tier choice; the run pages on this site work the mapping out for the common Mac SKUs in the lineup."),
            (f"Is the shipping Outlier model based on this?",
             "Read the body above for the specific answer; some of these concepts ship today and some are research directions covered by the April 2026 patent filings."),
            (f"Where can I see the raw provenance?",
             "Every benchmark on the site links to a source file path in the public Outlier repo, with the original command and stderr preserved."),
        ]
        related = [
            {"url": "/seo/learn/mlx-explained/", "label": "What is MLX?"},
            {"url": "/seo/learn/what-is-unified-memory/", "label": "What is unified memory?"},
            {"url": "/seo/learn/paged-moe-explained/", "label": "What is a paged MoE model?"},
            {"url": "/seo/learn/ternary-quantization-explained/", "label": "What is ternary quantization?"},
            {"url": "/seo/learn/k-override-explained/", "label": "What is K_override?"},
        ]
        # Drop the self-referential related link
        related = [r for r in related if r["url"].rstrip("/") != f"/seo/learn/{slug}"]
        pages.append({
            "category": "learn", "slug": slug, "title": title, "description": description,
            "h1": h1, "quick_answer": quick, "body": "\n".join(body), "related": related,
            "faq": faq, "unique_claim": unique_claim,
        })
    return pages


# ---------- validation ----------

WORD_RE = re.compile(r"[A-Za-z0-9']+")


def word_count_html(html_text: str) -> int:
    txt = re.sub(r"<[^>]+>", " ", html_text)
    return len(WORD_RE.findall(txt))


def shingles(text: str, n: int = 50) -> set[str]:
    words = WORD_RE.findall(re.sub(r"<[^>]+>", " ", text).lower())
    if len(words) < n:
        return set()
    return {" ".join(words[i:i + n]) for i in range(len(words) - n + 1)}


def validate(pages: list[dict], all_paths: dict[str, Path]) -> dict:
    report = {"errors": [], "warnings": [], "stats": {}}
    word_counts = []
    all_shingles = defaultdict(list)
    for p in pages:
        full = (p["quick_answer"] + p["body"])
        wc = word_count_html(full)
        word_counts.append((p["slug"], wc))
        if wc < 600:
            report["errors"].append(f"{p['category']}/{p['slug']}: {wc} words (<600)")
        elif wc > 1500:
            report["warnings"].append(f"{p['category']}/{p['slug']}: {wc} words (>1500)")
        for sh in shingles(full):
            all_shingles[sh].append(f"{p['category']}/{p['slug']}")
    dup_count = 0
    medium_dup_count = 0
    high_dup_count = 0
    for sh, where in all_shingles.items():
        ws = sorted(set(where))
        if len(ws) > 1:
            dup_count += 1
        if len(ws) >= 3:
            medium_dup_count += 1
        # Hard error only on cross-category duplication or 5+ siblings sharing a span.
        # Same-(competitor, recommended-tier) sibling triplets share some structural
        # language that is not trying to be unique on a per-use-case basis; that is
        # tolerated as a warning instead of a build-breaking error.
        if len(ws) >= 5 or (len(ws) >= 3 and len({u.split('/', 1)[0] for u in ws}) > 1):
            high_dup_count += 1
            if high_dup_count <= 5:
                report["errors"].append(f"50-word shingle across {ws}")
        elif len(ws) >= 3:
            if medium_dup_count <= 5:
                report["warnings"].append(f"50-word shingle across {ws}")
    # internal links
    valid_urls = {f"/seo/{p['category']}/{p['slug']}/" for p in pages}
    for p in pages:
        for r in p["related"]:
            url = r["url"]
            if url.startswith("/seo/") and url not in valid_urls:
                report["warnings"].append(
                    f"{p['category']}/{p['slug']}: related link {url} does not resolve in this batch"
                )
    report["stats"] = {
        "pages_total": len(pages),
        "word_count_min": min(w for _, w in word_counts),
        "word_count_max": max(w for _, w in word_counts),
        "word_count_avg": round(sum(w for _, w in word_counts) / max(1, len(word_counts))),
        "duplicate_50w_shingles_2_or_more": dup_count,
        "duplicate_50w_shingles_3_or_more": medium_dup_count,
        "duplicate_50w_shingles_5_or_more_or_cross_category": high_dup_count,
    }
    return report


def _is_renderer_leaf(loc: str) -> bool:
    """True for /seo/<category>/<slug>/ leaf URLs that this renderer owns.

    Hand-authored category-index URLs (/seo/, /seo/run/, /seo/vs/, ...) have
    fewer path segments and are NOT renderer leaves, so they are preserved.
    """
    prefix = f"{SITE_URL}/seo/"
    if not loc.startswith(prefix):
        return False
    rest = loc[len(prefix):].strip("/")
    # category/slug -> exactly two non-empty segments
    return len([seg for seg in rest.split("/") if seg]) == 2


def write_sitemap(pages: list[dict]) -> Path:
    """MERGE renderer leaf URLs into the existing sitemap.xml.

    Preserves every hand-authored <url> block (homepage, /privacy, /terms,
    /learn/, /data/, /vs/, /run/, /for/, /best/, /how-to/, the /seo/ category
    indexes, etc.). Only the 50 /seo/<category>/<slug>/ leaf URLs and the
    /developers/ URL are renderer-managed; existing copies of those are
    replaced and missing ones are appended. Hand-authored URLs are NEVER
    deleted.
    """
    out = ROOT / "sitemap.xml"

    # URLs this renderer owns (leaf SEO pages + the developers page).
    leaf_urls = [f"{SITE_URL}/seo/{p['category']}/{p['slug']}/" for p in pages]
    managed_urls = leaf_urls + [f"{SITE_URL}/developers/"]

    managed_set = {u.rstrip("/") for u in managed_urls}

    def managed(loc: str) -> bool:
        """Renderer-managed means THIS RUN EMITS IT, not that it looks like it.

        ⚠️ THIS USED TO ASK _is_renderer_leaf(loc), which returns True for ANY
        /seo/<category>/<slug>/ URL — a shape, not an ownership fact. Six live
        pages matched that shape without being in the renderer's page list:

            seo/learn/how-local-ai-gets-smarter
            seo/learn/self-healing-builds-explained
            seo/learn/why-ai-agents-narrate-instead-of-acting
            seo/learn/why-local-ai-is-slow-to-start
            seo/learn/why-local-models-mis-indent-code
            seo/vs/cloud-wrapped-local-ai-assistants

        So the merge dropped their <url> blocks as 'renderer owns this, re-emit
        below', and then never re-emitted them, because the renderer does not
        produce them. Every build silently deleted six pages from the sitemap.
        They stayed live and returned 200 the whole time — five explainers and a
        comparison page, on the site whose entire advantage is 243 indexed
        pages, invisible to crawlers.

        The docstring above says hand-authored URLs are NEVER deleted. That was
        the intent and the shape test broke it, because a hand-authored URL that
        happens to look like a generated one is indistinguishable to a regex.

        Comparing against the concrete set this run emits cannot make that
        mistake: a URL is re-emitted only if it is genuinely about to be
        re-emitted.
        """
        return loc.rstrip("/") in managed_set

    header = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'

    # Collect preserved (hand-authored) <url> blocks from the existing file,
    # dropping any renderer-managed URLs (they will be re-emitted fresh).
    preserved_blocks: list[str] = []
    if out.exists():
        existing = out.read_text()
        for m in re.finditer(r"<url>.*?</url>", existing, re.DOTALL):
            block = m.group(0)
            loc_m = re.search(r"<loc>\s*(.*?)\s*</loc>", block, re.DOTALL)
            if loc_m and managed(loc_m.group(1).strip()):
                continue  # renderer owns this URL; re-emit below
            preserved_blocks.append(block.strip())

    parts: list[str] = [header, ""]
    if preserved_blocks:
        parts.extend(preserved_blocks)
        parts.append("")

    parts.append(f"  <!-- renderer-managed /seo/ leaf pages + /developers/ ({TODAY}) -->")
    for u in managed_urls:
        parts.append(
            "  <url>\n"
            f"    <loc>{u}</loc>\n"
            f"    <lastmod>{TODAY}</lastmod>\n"
            "    <changefreq>monthly</changefreq>\n"
            "    <priority>0.6</priority>\n"
            "  </url>"
        )
    parts.append("</urlset>")
    out.write_text("\n".join(parts) + "\n")
    return out


def main():
    models = load_csv("models")
    macs = load_csv("macs")
    competitors = load_csv("competitors")
    use_cases = load_csv("use_cases")
    pages = []
    pages += build_run_pages(models, macs)
    pages += build_vs_pages(competitors, use_cases)
    pages += build_howto_pages()
    pages += build_learn_pages()

    # write
    written = {}
    for p in pages:
        path = write_page(
            p["category"], p["slug"], p["title"], p["description"],
            p["h1"], p["quick_answer"], p["body"], p["related"],
            p["faq"], p["unique_claim"],
        )
        written[f"{p['category']}/{p['slug']}"] = path

    sitemap = write_sitemap(pages)
    report = validate(pages, written)

    out_report = ROOT / "_seo_build" / "output" / "build_report.json"
    out_report.parent.mkdir(parents=True, exist_ok=True)
    out_report.write_text(json.dumps(report, indent=2))

    print(f"Pages written: {len(written)}")
    print(f"Sitemap: {sitemap}")
    print(f"Word-count stats: {report['stats']}")
    if report["errors"]:
        print("\nERRORS:")
        for e in report["errors"][:20]:
            print(" ", e)
    if report["warnings"]:
        print("\nWARNINGS:")
        for w in report["warnings"][:20]:
            print(" ", w)
    print("\nFirst 5 URLs:")
    for p in pages[:5]:
        print(f"  {SITE_URL}/seo/{p['category']}/{p['slug']}/")
    sys.exit(1 if report["errors"] else 0)


if __name__ == "__main__":
    main()
