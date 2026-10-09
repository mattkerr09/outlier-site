#!/usr/bin/env python3
"""Gate: the button in the top nav is readable — its text meets WCAG AA against every colour of its background,
at rest, on hover, on focus and when pressed.

Why (2026-10-09): the homepage's nav "Download" button had shipped with grey text (rgb(169,163,192)) on its purple
gradient, 1.3 to 2.1:1, because `.nav-links a{color:…}` outranks `.btn-primary{color:#fff}`. No gate read colours,
and the button is on top of every visit. A cascade bug is invisible to a text check, so this one asks a browser:
each page whose nav carries a styled link is loaded in headless Chrome (offline, from disk), and the computed text
colour is measured against every colour stop of the computed background. States are measured through the real
cascade by rewriting :hover / :focus / :focus-visible / :active to a class the gate adds (same specificity).

usage: nav_cta_contrast_gate.py <site-root>          check every page
       nav_cta_contrast_gate.py --break-test         must FAIL on a page with the old grey-on-purple button
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PSEUDO = re.compile(r":(?:focus-visible|focus-within|hover|focus|active)")
HEADER = re.compile(r"<(header|nav)\b.*?</\1>", re.S | re.I)
STYLED = re.compile(r'class="[^"]*\b(?:btn|cta)\b', re.I)

PROBE = r"""<script>(function(){
function css(rgb){var m=rgb.match(/rgba?\(([^)]+)\)/);if(!m)return null;var p=m[1].split(/[ ,\/]+/).filter(Boolean).map(Number);
 return {r:p[0],g:p[1],b:p[2],a:p.length>3?p[3]:1};}
function stops(s){return (s.backgroundImage.match(/rgba?\([^)]+\)/g)||[]).map(css).concat(
 css(s.backgroundColor)&&css(s.backgroundColor).a>0.5?[css(s.backgroundColor)]:[]);}
function measure(a){var s=getComputedStyle(a);return {color:css(s.color),stops:stops(s),
 size:parseFloat(s.fontSize),weight:parseInt(s.fontWeight,10)};}
var out=[];var hdr=document.querySelector('header')||document.querySelector('nav');
(hdr?[].slice.call(hdr.querySelectorAll('a,button')):[]).forEach(function(a){
 var s=getComputedStyle(a);if(!stops(s).length)return;
 var rest=measure(a);a.classList.add('__state');var on=measure(a);a.classList.remove('__state');
 out.push({text:(a.textContent||'').trim().slice(0,30),rest:rest,state:on});});
var el=document.createElement('script');el.type='application/json';el.id='__gate';el.textContent=JSON.stringify(out);
document.body.appendChild(el);})();</script>"""


def _lin(c: float) -> float:
    c /= 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _lum(c: dict) -> float:
    return 0.2126 * _lin(c["r"]) + 0.7152 * _lin(c["g"]) + 0.0722 * _lin(c["b"])


def contrast(a: dict, b: dict) -> float:
    la, lb = _lum(a), _lum(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def _with_states(html: str) -> str:
    """Every :hover/:focus/:active in the page's CSS becomes .__state, so adding the class shows that state."""
    html = re.sub(r"(<style\b[^>]*>)(.*?)(</style>)", lambda m: m.group(1) + PSEUDO.sub(".__state", m.group(2))
                  + m.group(3), html, flags=re.S | re.I)
    return html.replace("</body>", PROBE + "</body>", 1) if "</body>" in html else html + PROBE


def measure(path: str) -> list:
    with open(path, encoding="utf-8") as f:
        html = f.read()
    with tempfile.TemporaryDirectory() as d:
        page = os.path.join(d, "page.html")
        with open(page, "w", encoding="utf-8") as f:
            f.write(_with_states(html))
        r = subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-first-run", f"--user-data-dir={d}/u",
                            "--window-size=1280,900", "--virtual-time-budget=3000", "--dump-dom",
                            "file://" + page], capture_output=True, text=True, timeout=120)
    m = re.search(r'<script type="application/json" id="__gate">(.*?)</script>', r.stdout, re.S)
    if not m:
        raise RuntimeError(f"{path}: the page never reported (chrome exit {r.returncode})")
    return json.loads(m.group(1))


def failures(path: str) -> list:
    bad = []
    for cta in measure(path):
        for state in ("rest", "state"):
            m = cta[state]
            large = m["size"] >= 24 or (m["size"] >= 18.66 and m["weight"] >= 700)
            need = 3.0 if large else 4.5
            worst = min(contrast(m["color"], s) for s in m["stops"])
            if worst < need:
                c = m["color"]
                bad.append(f'{path}: nav "{cta["text"]}" ({"hover/focus" if state == "state" else "at rest"}) text '
                           f'rgb({c["r"]},{c["g"]},{c["b"]}) is {worst:.2f}:1 on its background (AA needs {need}:1)')
    return bad


def pages(root: str) -> list:
    out = []
    files = subprocess.run(["git", "-C", root, "ls-files", "*.html"], capture_output=True, text=True).stdout.split()
    for rel in files:
        if rel.startswith("_seo_build/"):
            continue
        with open(os.path.join(root, rel), encoding="utf-8", errors="replace") as f:
            head = HEADER.search(f.read())
        if head and STYLED.search(head.group(0)):
            out.append(os.path.join(root, rel))
    return out


BROKEN = """<!doctype html><html><head><style>
.nav-links a{color:#a9a3c0}.nav-links a:hover{color:#f3f1fa}
.btn{display:inline-flex;padding:.5rem 1rem;font-size:15px;font-weight:600}
.btn-primary{background:linear-gradient(180deg,#b371ff 0%,#8b46ec 100%);color:#fff}
</style></head><body><header><nav class="nav-links"><a href="#">Docs</a>
<a class="btn btn-primary btn-sm" href="#">Download</a></nav></header><main>x</main></body></html>"""


def main(argv) -> int:
    if not os.path.exists(CHROME):
        print(f"nav CTA contrast gate: Chrome not found at {CHROME}")
        return 2
    if argv[1:2] == ["--break-test"]:
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "broken.html")
            with open(p, "w") as f:
                f.write(BROKEN)
            bad = failures(p)
        print("\n".join(bad) or "the gate PASSED the old grey-on-purple button — the gate is broken")
        return 0 if bad else 1
    root = argv[1] if len(argv) > 1 else "."
    todo = pages(root)
    if not todo:
        print("nav CTA contrast gate: no page has a styled nav link — the page scan is broken (the homepage has one)")
        return 1
    bad = [b for p in todo for b in failures(p)]
    print("\n".join(bad) if bad else f"nav CTA contrast gate: {len(todo)} page(s) with a nav button, all AA at "
                                     f"rest and on hover/focus")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
