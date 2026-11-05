#!/usr/bin/env python3
"""Build /tools/can-my-mac-run-it/ — "Can my Mac run it?", a checker that runs in the browser with no network calls.

Pick a Mac and its memory; it says which Outlier tiers run and how fast. Every figure comes from the site's own data, the
same files and the same rules the /seo/run/ pages use, so the checker and those pages can never disagree:
  - seo/_data/models.csv  (min_ram_gb, disk_gb, m1_ultra_toks = MEASURED on an M1 Ultra, and its source)
  - seo/_data/macs.csv    (each Mac's memory options and memory bandwidth)
  - seo/_data/benchmarks.csv (the one check of the speed projection on another Mac: Nano on a 16 GB M4 Air)
  - seo/_data/app_tiers.json (the order the app shows the tiers in)
  - render.py's WORKING_SET_GB and its fit rule (a tier fits when its weights plus a working set fit in memory; the
    catalog minimum is only the floor the picker lets someone try a tier at; Plus streams its experts from the SSD).
Speed on any Mac but an M1 Ultra is the M1 Ultra measurement scaled by memory bandwidth and is labeled an estimate, with
the arithmetic shown, as on the /seo/run/ pages. The page shell (styles, nav, product box, footer) is copied from
vs/when-ollama-is-enough/ so it looks like the rest of the site.
usage: scripts/build_mac_checker.py <publish date YYYY-MM-DD>
"""
from __future__ import annotations

import csv
import html
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "_seo_build" / "scripts"))
import render  # noqa: E402  — WORKING_SET_GB and the version the site advertises

OUT = ROOT / "tools" / "can-my-mac-run-it" / "index.html"
URL = "https://outlier.host/tools/can-my-mac-run-it/"
SHELL = ROOT / "vs" / "when-ollama-is-enough" / "index.html"


def rows(name):
    with (ROOT / "seo" / "_data" / name).open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def bw_range(s):
    a = [float(x) for x in str(s).split("-")]
    return a[0], a[-1]


def verdict(tier, m, ram):
    """render.py's rule, applied to the memory the visitor picked rather than the base model's."""
    need, disk, ws = int(m["min_ram_gb"]), float(m["disk_gb"]), render.WORKING_SET_GB
    if tier == "plus":
        if ram < need:
            return "no", f"needs at least {need} GB"
        if ram >= 256:
            return "yes", f"its {m['disk_gb']} GB of weights fit fully in memory"
        if ram == need:
            return "tight", (f"runs at its {need} GB minimum by streaming experts from the SSD, with no memory to spare; "
                             f"slow by design")
        return "yes", (f"runs by streaming experts from the SSD (its {m['disk_gb']} GB of weights fit fully in memory only "
                       f"on a 256 GB Mac); slow by design")
    if ram == need and ram >= disk + ws:
        return "tight", f"runs, but {ram} GB is exactly its minimum, so there is no memory to spare"
    if ram >= disk + ws:
        return "yes", "fits comfortably"
    if ram >= need:
        return "partial", (f"loads, but runs fully in memory only from {int(-(-(disk + ws) // 1))} GB; at {ram} GB "
                           f"expect it to swap")
    return "no", f"needs at least {need} GB"


def main(date):
    tiers = {r["tier_id"]: r for r in rows("models.csv")}
    order = json.loads((ROOT / "seo" / "_data" / "app_tiers.json").read_text())["tier_display_order"]
    macs = rows("macs.csv")
    bench = rows("benchmarks.csv")
    air_nano = next((float(r["score"]) for r in bench if r["tier_id"] == "nano" and r["bench"].startswith("M4 Air")), None)
    air = next(x for x in macs if x["slug"] == "m4-air-13")
    air_proj = float(tiers["nano"]["m1_ultra_toks"]) * bw_range(air["memory_bandwidth_gbs"])[0] / 800.0

    data = {"tiers": [], "macs": []}
    for t in order:
        m = tiers[t]
        data["tiers"].append({"id": t, "name": m["display_name"], "min": int(m["min_ram_gb"]), "disk": float(m["disk_gb"]),
                              "m1u": float(m["m1_ultra_toks"]), "params": m["params"]})
    for x in macs:
        lo, hi = bw_range(x["memory_bandwidth_gbs"])
        rams = [int(v) for v in str(x["unified_ram_gb"]).split("|") if v.strip().isdigit()]
        per = {}
        for ram in rams:
            per[str(ram)] = {}
            for t in order:
                m = tiers[t]
                v, why = verdict(t, m, ram)
                m1u = float(m["m1_ultra_toks"])
                if x["chip"] == "Apple M1 Ultra":
                    speed = {"kind": "measured", "lo": m1u, "hi": m1u}
                else:
                    speed = {"kind": "estimate", "lo": round(m1u * lo / 800.0, 1), "hi": round(m1u * hi / 800.0, 1)}
                # render.py's one measured exception: Nano on the 16 GB M4 Air (benchmarks.csv, operator-reported)
                if t == "nano" and x["slug"] == "m4-air-13" and air_nano:
                    speed["seen"] = air_nano
                per[str(ram)][t] = {"v": v, "why": why, "speed": speed}
        data["macs"].append({"slug": x["slug"], "name": x["name"], "chip": x["chip"], "bw": x["memory_bandwidth_gbs"],
                             "year": x["year"], "rams": rams, "fit": per})

    # the answer sentence, read from the same verdicts: the smallest memory at which each tier fits (yes or tight)
    first = {}
    for t in order:
        oks = [ram for x in data["macs"] for ram in x["rams"] if x["fit"][str(ram)][t]["v"] in ("yes", "tight")]
        first[t] = min(oks) if oks else None
    nm = {t: tiers[t]["display_name"].replace("Outlier ", "") for t in order}
    by_ram = {}
    for t in order:
        by_ram.setdefault(first[t], []).append(nm[t])
    def _and(xs):
        return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " and " + xs[-1]
    steps = [f"{ram} GB {'runs' if i == 0 else 'adds'} {_and(by_ram[ram])}"
             for i, ram in enumerate(sorted(k for k in by_ram if k))]
    answer = ("Any Apple Silicon Mac (M1 or newer) on macOS 15 runs Outlier, and memory decides which models: "
              + "; ".join(steps) + ". Pick your Mac below to see every model and how fast it writes.")

    shell = SHELL.read_text(encoding="utf-8")
    style = re.search(r"  <style>\n.*?\n  </style>\n", shell, re.S).group(0)
    head_scripts = re.search(r"  <script async src=\"https://plausible\.io/js/[^\n]*\n  <script>window\.plausible[^\n]*\n",
                             shell).group(0)
    snippet = re.search(r"<script src=\"https://kerr-affiliate-hub\.kerrco\.workers\.dev/snippet\.js\" defer></script>\n"
                        r"<style data-pbox-style>.*?</style>\n", shell, re.S).group(0)
    nav = re.search(r"<nav>.*?</nav>\n", shell, re.S).group(0)
    pbox = re.search(r"<div class=\"pbox\" data-pbox=\"answer\">.*?</div>\n", shell, re.S).group(0)
    tail = re.search(r"<footer>.*</html>\n?", shell, re.S).group(0)

    def box(where):
        return pbox.replace('data-pbox="answer"', f'data-pbox="{where}"').replace(
            "src=vs-when-ollama-is-enough-box-answer", f"src=tools-can-my-mac-run-it-box-{where}")

    title = "Can my Mac run local AI? Free checker (2026)"
    desc = ("Pick your Mac and its memory to see which Outlier models run and how fast, from our own measurements. "
            "Runs in your browser; nothing is sent.")
    ld_article = {"@context": "https://schema.org", "@type": "WebApplication", "name": "Can my Mac run it?",
                  "url": URL, "applicationCategory": "UtilitiesApplication", "operatingSystem": "Any (runs in the browser)",
                  "description": desc, "author": {"@type": "Person", "name": "Matt Kerr"},
                  "datePublished": date, "dateModified": date, "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"}}
    ld_crumb = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Outlier", "item": "https://outlier.host/"},
        {"@type": "ListItem", "position": 2, "name": "Run on your Mac", "item": "https://outlier.host/run/"},
        {"@type": "ListItem", "position": 3, "name": "Can my Mac run it?", "item": URL}]}
    m1u_rows = "".join(
        f"<tr><td>{html.escape(tiers[t]['display_name'])}</td><td>{tiers[t]['params']}</td><td>{tiers[t]['min_ram_gb']} GB</td>"
        f"<td>{tiers[t]['disk_gb']} GB</td><td>{tiers[t]['m1_ultra_toks']} tok/s</td></tr>" for t in order)

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" type="image/png" sizes="192x192" href="/icon-192.png">
<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">

  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="msvalidate.01" content="34D102FD9C044A2BDA597B176842725B" />
  <title>{html.escape(title)} | Outlier</title>
  <meta name="description" content="{html.escape(desc)}">
  <meta name="theme-color" content="#07060b">
  <meta name="last-modified" content="{date}">
  <link rel="canonical" href="{URL}">
  <meta property="og:type" content="website">
  <meta property="og:title" content="{html.escape(title)}">
  <meta property="og:description" content="{html.escape(desc)}">
  <meta property="og:url" content="{URL}">
  <meta property="og:site_name" content="Outlier">
  <meta property="og:image" content="https://outlier.host/og-card.png">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta name="twitter:image" content="https://outlier.host/og-card.png">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{html.escape(title)}">
  <meta name="twitter:description" content="{html.escape(desc)}">
{style}
  <style>
    .chk {{ border:1px solid rgba(127,127,127,.35); border-radius:12px; padding:1rem 1.15rem; margin:1.4rem 0; }}
    .chk label {{ display:block; font-size:.9rem; margin:.2rem 0 .3rem; opacity:.85; }}
    .chk select {{ font:inherit; width:100%; max-width:26rem; padding:.45rem .55rem; border-radius:8px; margin-bottom:.8rem;
      background:transparent; color:inherit; border:1px solid rgba(127,127,127,.5); }}
    .chk select option {{ color:#111; }}
    .chk-out {{ width:100%; border-collapse:collapse; margin-top:.4rem; font-size:.95rem; }}
    .chk-out th, .chk-out td {{ text-align:left; padding:.5rem .4rem; border-top:1px solid rgba(127,127,127,.25); vertical-align:top; }}
    .chk-v {{ font-weight:600; white-space:nowrap; }}
    .v-yes {{ color:#34c759; }} .v-tight {{ color:#d0a000; }} .v-partial {{ color:#ff9f0a; }} .v-no {{ opacity:.6; }}
    .chk-note {{ font-size:.85rem; opacity:.8; margin-top:.7rem; }}
    .chk-wrap {{ overflow-x:auto; }}
    table.src {{ width:100%; border-collapse:collapse; font-size:.9rem; }}
    table.src th, table.src td {{ text-align:left; padding:.4rem; border-top:1px solid rgba(127,127,127,.25); }}
  </style>
{head_scripts}  <script type="application/ld+json">
  {json.dumps(ld_article)}
  </script>
  <script type="application/ld+json">
  {json.dumps(ld_crumb)}
  </script>
{snippet}</head>
<body>
{nav}<article>
  <div class="wrap">
    <div class="crumb"><a href="https://outlier.host/">Outlier</a> &nbsp;&rsaquo;&nbsp; <a href="https://outlier.host/run/">Run on your Mac</a></div>
    <h1>Can my Mac run local AI?</h1>
    <div class="byline-row">
      <span class="byline">Matt Kerr &middot; Outlier &middot; published {date}</span>
    </div>

    <p class="lead">{html.escape(answer)}</p>

    <div class="chk" id="checker">
      <label for="chk-mac">Your Mac</label>
      <select id="chk-mac"></select>
      <label for="chk-ram">Its memory (Apple menu &rsaquo; About This Mac shows it)</label>
      <select id="chk-ram"></select>
      <div class="chk-wrap"><table class="chk-out" aria-live="polite">
        <thead><tr><th>Model</th><th>On this Mac</th><th>Speed</th></tr></thead>
        <tbody id="chk-body"><tr><td colspan="3">Pick your Mac above. (This checker needs JavaScript; the table under
        &ldquo;Where the numbers come from&rdquo; has the same figures.)</td></tr></tbody>
      </table></div>
      <p class="chk-note" id="chk-note"></p>
      <p class="chk-note">Mac not listed? Pick one with the same chip and memory. An Intel Mac cannot run Outlier: it needs
      Apple Silicon (M1 or newer) and macOS 15 or later. Nothing you pick here leaves this page.</p>
    </div>

{box("answer")}
    <h2>How to read the answer</h2>
    <p><strong>Fits comfortably</strong> means the model's weights plus a {render.WORKING_SET_GB:g} GB working set fit in
    memory, the same test the app uses when it recommends a model. <strong>No memory to spare</strong> means your memory
    is exactly the model's minimum: it runs, but other apps will push it into swap. <strong>Loads, expect it to swap</strong>
    means the app lets you try it, but it will be slow until you close other apps. Outlier Plus is different: it streams
    its experts from the SSD, so it runs on a 64 GB Mac, slowly, by design.</p>
    <p><strong>Speed</strong> is how many tokens a model writes per second once it starts answering. On an M1 Ultra it is
    our own measurement. On every other Mac it is that measurement scaled by your Mac's memory bandwidth (the M1 Ultra has
    800 GB/s), and it says so. The only time we have checked that projection on another Mac, Nano on a 16 GB M4 Air
    {"wrote about " + format(air_nano, "g") + " tok/s, about " + str(round(air_nano / air_proj)) + "&times; the " + format(air_proj, ".1f") + " tok/s the projection gives" if air_nano else "has not been measured"},
    so read the estimates as conservative.</p>

    <h2>Where the numbers come from</h2>
    <p>Each model's minimum memory, download size and speed on an M1 Ultra (800 GB/s), measured by Outlier:</p>
    <div class="chk-wrap"><table class="src"><thead><tr><th>Model</th><th>Size</th><th>Minimum memory</th><th>Download</th>
    <th>Speed on M1 Ultra</th></tr></thead><tbody>{m1u_rows}</tbody></table></div>
    <p>The memory options and bandwidth of each Mac are Apple's published figures. The same data drives the per-Mac pages
    in <a href="https://outlier.host/run/">Run Outlier on your Mac</a>; for what each amount of memory holds in general, see
    <a href="https://outlier.host/data/mac-ram-to-model-size/">how much RAM a local model needs</a>, and for the step by
    step, <a href="https://outlier.host/seo/how-to/install-outlier-on-mac/">installing Outlier on a Mac</a>.</p>

{box("end")}  </div>
</article>
<script id="chk-data" type="application/json">{json.dumps(data, separators=(",", ":"))}</script>
<script>
(function () {{
  var D = JSON.parse(document.getElementById('chk-data').textContent);
  var mac = document.getElementById('chk-mac'), ram = document.getElementById('chk-ram');
  var body = document.getElementById('chk-body'), note = document.getElementById('chk-note');
  var LABEL = {{ yes: 'Runs', tight: 'Runs, no memory to spare', partial: 'Loads, expect it to swap', no: 'Not on this memory' }};
  D.macs.forEach(function (m, i) {{ var o = document.createElement('option'); o.value = i; o.textContent = m.name + ' (' + m.year + ')'; mac.appendChild(o); }});
  function fillRam() {{
    var m = D.macs[+mac.value]; ram.innerHTML = '';
    m.rams.forEach(function (r) {{ var o = document.createElement('option'); o.value = r; o.textContent = r + ' GB'; ram.appendChild(o); }});
  }}
  function speedText(s) {{
    var v = s.lo === s.hi ? String(s.lo) : s.lo + '–' + s.hi;
    return s.kind === 'measured' ? v + ' tok/s, measured' :
      '~' + v + ' tok/s, estimate' + (s.seen ? ' (one real run on this Mac: about ' + s.seen + ' tok/s)' : '');
  }}
  function show() {{
    var m = D.macs[+mac.value], fit = m.fit[ram.value];
    function el(tag, cls, text) {{ var e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }}
    var VCLS = {{ yes: 'chk-v v-yes', tight: 'chk-v v-tight', partial: 'chk-v v-partial', no: 'chk-v v-no' }};
    body.textContent = '';
    D.tiers.forEach(function (t) {{
      var f = fit[t.id], tr = document.createElement('tr'), a = el('td'), b = el('td'), c = el('td');
      a.appendChild(el('strong', null, t.name)); a.appendChild(el('br')); a.appendChild(el('span', 'chk-note', t.params + ', ' + t.disk + ' GB download'));
      b.appendChild(el('span', VCLS[f.v], LABEL[f.v])); b.appendChild(el('br')); b.appendChild(el('span', 'chk-note', f.why));
      c.textContent = f.v === 'no' ? '—' : speedText(f.speed);
      tr.appendChild(a); tr.appendChild(b); tr.appendChild(c); body.appendChild(tr);
    }});
    note.textContent = m.chip === 'Apple M1 Ultra' ? 'Speeds on this chip are our own measurements.' :
      'Speeds are estimates: the M1 Ultra measurement × (' + m.bw + ' ÷ 800 GB/s) for the ' + m.chip + '.';
  }}
  function track() {{   // only a visitor's own pick is counted, never the page load
    var m = D.macs[+mac.value];
    if (window.plausible) {{ try {{ window.plausible('Mac Checker', {{ props: {{ mac: m.slug, ram: ram.value }} }}); }} catch (e) {{}} }}
  }}
  mac.addEventListener('change', function () {{ fillRam(); show(); track(); }});
  ram.addEventListener('change', function () {{ show(); track(); }});
  var start = D.macs.findIndex(function (m) {{ return m.slug === 'm4-air-13'; }});
  mac.value = start < 0 ? 0 : start; fillRam(); ram.value = D.macs[+mac.value].rams[0];
  show();
}})();
</script>
{tail}"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(page, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} · {len(data['macs'])} Macs · answer: {answer}")


if __name__ == "__main__":
    main(sys.argv[1])
