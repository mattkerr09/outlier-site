#!/usr/bin/env python3
"""Every article page offers phone visitors "Send the Mac link to yourself" next to its download.

Why: a phone visitor on /how-to/run-qwen-locally-mac/ got a Download button for a Mac app they can't use there (CEO
quality check, 2026-10-06). The homepage and /learn/does-chatgpt-use-a-data-center/ already had the line. This adds the
same markup, styling and script to every /how-to/, /learn/, /vs/, /run/, /seo/ and /data/ page, and to the /seo/ template so a
re-render keeps it. kcCarry (copied byte for byte from the page that has it) carries the visitor's source and any
affiliate id into the shared link; utm_campaign is the page's own tag (the src= of its download link), so the shares
from each page can be counted.

Idempotent: a page that already has the line is left alone. Datelines are not touched (adding the phone line is
chrome, not content).
  python3 scripts/add_phone_link.py [--check]
"""
import glob
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DONE = ROOT / "learn/does-chatgpt-use-a-data-center/index.html"
LINE = ('<p class="phone-link">On your phone? <button type="button" data-send-mac-link>'
        'Send the Mac link to yourself</button></p>')
CSS = (".phone-link{margin:.9rem 0 0;font-size:.9rem;color:var(--text-mid);}\n"
       ".phone-link button{font:inherit;color:var(--text);background:none;border:0;padding:0;text-decoration:underline;"
       "text-underline-offset:3px;cursor:pointer;}\n")


def _kccarry() -> str:
    m = re.search(r"^function kcCarry\(url\)\{.*\}$", DONE.read_text(encoding="utf-8"), re.M)
    if not m:
        sys.exit(f"kcCarry not found in {DONE}")
    return m.group(0)


def script(campaign: str) -> str:
    return ("<script>\n/* Send the Mac link to yourself: the link carries the visitor's source and any affiliate id (kcCarry). */\n"
            + _kccarry() + "\n"
            "document.querySelectorAll('[data-send-mac-link]').forEach(function (b) {\n"
            "  b.addEventListener('click', function () {\n"
            f"    var url = kcCarry('https://outlier.host/?utm_source=phone-share&utm_medium=share&utm_campaign={campaign}');\n"
            "    var text = 'Outlier for Mac is free to start. Open this on your Mac to download it.';\n"
            "    if (window.plausible) { try { window.plausible('Send Mac Link'); } catch (e) {} }\n"
            "    if (navigator.share) { navigator.share({ title: 'Outlier for Mac', text: text, url: url }).catch(function () {}); }\n"
            "    else { location.href = 'mailto:?subject=' + encodeURIComponent('Outlier for Mac: download link') + '&body=' + "
            "encodeURIComponent(text + '\\n\\n' + url); }\n"
            "  });\n"
            "});\n"
            "</script>\n")


def add(s: str):
    """The page with the line, its styling and its script, or None when it has no download block to put it under.
    The campaign is the src= of THAT block's download link (on /seo/ pages the template's {{ page_tag }})."""
    if "data-send-mac-link" in s:
        return None
    m = re.search(r'(<div class="cta">.*?)(\n?[ \t]*</div>)', s, re.S)
    if m:
        tag = re.search(r"/dl/outlier\?src=([a-z0-9-]+)", m.group(1))
        s = s[:m.end(1)] + "\n      " + LINE + s[m.end(1):]
    else:
        m = re.search(r'<a class="cta"[^>]*>.*?</a>', s, re.S)
        if not m:
            return None
        tag = re.search(r"/dl/outlier\?src=([a-z0-9-]+)", m.group(0))
        s = s[:m.end()] + "\n" + LINE + s[m.end():]
    if not tag:
        return None
    campaign = tag.group(1)
    if ".phone-link{" not in s:
        i = s.find("</style>")
        if i == -1:
            return None
        s = s[:i] + CSS + s[i:]
    i = s.rfind("</body>")
    if i == -1:
        return None
    return s[:i] + script(campaign) + s[i:]


def main() -> int:
    check = "--check" in sys.argv
    pages = sorted({p for d in ("how-to", "learn", "vs", "run", "seo", "data")
                    for p in glob.glob(str(ROOT / d / "**" / "index.html"), recursive=True)})
    changed = skipped = 0
    for p in pages:
        s = Path(p).read_text(encoding="utf-8")
        new = add(s)
        if new is None:
            skipped += 1
            continue
        changed += 1
        if not check:
            Path(p).write_text(new, encoding="utf-8")
    tpl = ROOT / "_seo_build/templates/_base.html"
    t = tpl.read_text(encoding="utf-8")
    if "data-send-mac-link" not in t:
        t2 = re.sub(r'(<a class="cta"[^>]*>.*?</a>)', lambda m: m.group(1) + "\n" + LINE, t, count=1, flags=re.S)
        t2 = t2.replace("</style>", CSS + "</style>", 1)
        t2 = t2.replace("{{ pbox_script | safe }}</body>", script("{{ page_tag }}") + "{{ pbox_script | safe }}</body>", 1)
        if t2.count(LINE) != 1 or ".phone-link{" not in t2 or "utm_campaign={{ page_tag }}" not in t2:
            sys.exit("the /seo/ template did not take all three pieces")
        if not check:
            tpl.write_text(t2, encoding="utf-8")
        print("template: updated" if not check else "template: would update")
    print(f"pages: {changed} {'would get' if check else 'got'} the phone line; {skipped} left alone "
          "(already have it, or no download block)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
