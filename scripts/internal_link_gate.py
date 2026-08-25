#!/usr/bin/env python3
"""Every internal link must resolve to a file that exists.

Added after learn/ai-privacy-policies-explained — a page ABOUT privacy policies —
shipped a footer link to /privacy/, which 404s. The real path is /privacy.html.
Four other pages linked it correctly; this one did not, and nothing noticed.

No existing gate reads links. A dead internal link costs a reader the page they
asked for and costs an ad click the landing it paid for, and it is invisible to
every check that only reads text.

Python 3.9.6 — the site gates run on the system interpreter.
"""
import collections
import pathlib
import re
import sys


def main(root_arg):
    root = pathlib.Path(root_arg).resolve()
    pages = [p for p in root.rglob('*.html')
             if 'node_modules' not in str(p) and '_seo_build' not in str(p)]
    if not pages:
        print("FAIL: no html pages found — the gate would pass vacuously")
        return 1

    have = set()
    for p in pages:
        rel = str(p.relative_to(root))
        have.add('/' + rel)
        if rel.endswith('index.html'):
            have.add('/' + rel[:-len('index.html')])
            have.add('/' + rel[:-len('/index.html')])
    norm = {h.rstrip('/') for h in have}

    broken = collections.defaultdict(list)
    checked = 0
    for p in pages:
        text = p.read_text(errors='ignore')
        for href in re.findall(r'href="([^"#?]+)', text):
            # An absolute link to our own domain is an INTERNAL link wearing a
            # hostname. Skipping everything that starts with http left 3233 of
            # them unchecked — the same class of defect, invisible to the gate
            # that exists to catch it.
            for own in ('https://outlier.host', 'http://outlier.host'):
                if href.startswith(own):
                    href = href[len(own):] or '/'
                    break
            if href.startswith(('http', 'mailto:', 'tel:', 'data:', '//')):
                continue
            checked += 1
            if href.startswith('/'):
                target = href
            else:
                try:
                    target = '/' + str((p.parent / href).resolve().relative_to(root))
                except ValueError:
                    broken[href].append(str(p.relative_to(root)))
                    continue
            if target.rstrip('/') in norm:
                continue
            if (root / target.lstrip('/')).exists():
                continue
            broken[target].append(str(p.relative_to(root)))

    if not broken:
        print("internal links: %d checked across %d pages, all resolve"
              % (checked, len(pages)))
        return 0

    print("FAIL: %d internal link target(s) do not exist" % len(broken))
    for target, sources in sorted(broken.items(), key=lambda kv: -len(kv[1])):
        print("   %s  <- %d page(s)" % (target, len(sources)))
        for src in sources[:3]:
            print("       %s" % src)
    print("")
    print("   A dead internal link costs a reader the page they asked for.")
    print("   Check the real path: /privacy.html and /terms.html are files,")
    print("   not directories — /privacy/ has never resolved.")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "."))
