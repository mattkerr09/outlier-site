#!/usr/bin/env python3
"""Check the GGUF additions and preserve the original article from next."""
from collections import Counter
from html import unescape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
PAGE = 'vs/gguf-vs-ggml/index.html'
TITLE = 'What is GGUF? GGUF vs GGML, and which file to use'
H1 = 'What is GGUF? GGUF vs GGML, and which one to use'
DEFINITION = ('GGUF is the model file format that llama.cpp and the tools built on it load: '
              'one file holds the weights plus the metadata and tokenizer needed to run them.')
REPO = 'https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF'


def blocks(html, tag):
    return re.findall(rf'<{tag}\b[^>]*>.*?</{tag}>', html, re.S)


def text(html):
    return unescape(re.sub(r'<[^>]*>', '', html)).strip()


class Markup(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.meta = {}
        self.hrefs = []
        self.stack = []
        self.wrapped_tables = 0
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'meta':
            self.meta[attrs.get('name', attrs.get('property'))] = attrs.get('content')
        if 'href' in attrs:
            self.hrefs.append(attrs['href'])
        if tag == 'table' and any('table-scroll' in a.get('class', '').split()
                                  for t, a in self.stack if t == 'div'):
            self.wrapped_tables += 1
        if tag not in {'meta', 'link', 'img', 'input', 'br', 'hr'}:
            self.stack.append((tag, attrs))

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break


def check(html, original, sitemap):
    current, old = Markup(html), Markup(original)
    assert text(blocks(html, 'title')[0]) == TITLE
    for key in ('og:title', 'twitter:title'):
        assert current.meta[key] == TITLE and len(current.meta[key]) <= 60, key
    assert len(TITLE) <= 60
    assert text(blocks(html, 'h1')[0]) == H1
    for key in ('description', 'og:description', 'twitter:description'):
        assert current.meta[key].startswith('GGUF is ') and len(current.meta[key]) < 155
    qa = re.search(r'<div class="quick-answer">.*?<p>(.*?)</p>', html, re.S).group(1)
    old_qa = re.search(r'<div class="quick-answer">.*?<p>(.*?)</p>', original, re.S).group(1)
    assert text(qa).startswith(DEFINITION)
    assert qa == DEFINITION + ' ' + old_qa, 'Original GGML sentences changed'
    assert len(text(qa).split()) < 90

    # Check original headings first so the negative control proves preservation.
    old_h2 = Counter(blocks(original, 'h2'))
    assert not old_h2 - Counter(blocks(html, 'h2')), 'Original h2 removed or changed'
    headings = [text(h) for h in blocks(html, 'h2')]
    assert headings.index('What is inside a real GGUF file') == headings.index('How to tell which one you have') + 1
    section = html.split('<h2>What is inside a real GGUF file</h2>', 1)[1].split('<h2>', 1)[0]
    rows = {
        'First four bytes': 'GGUF', 'Version': '3', 'Tensor count': '201',
        'Metadata pairs': '23', 'Architecture': 'llama',
        'Quantization': 'File type 15: Q4_K_M', 'Context length': '2048',
        'Tokenizer stored inside': '32,000 tokens, 61,249 merges, a chat template',
        'Tensor types': '135 Q4_K, 21 Q6_K, 45 F32',
        'Where the header and tensor index end': 'Byte 1,709,436 of 668,788,096, about 1.7 MB',
    }
    actual = [[text(cell) for cell in blocks(row, 'td')] for row in blocks(section, 'tr')]
    for key, value in rows.items():
        assert [key, value] in actual, f'Missing file reading: {key}'
    assert Markup(section).wrapped_tables == 1
    assert '.table-scroll { overflow-x: auto;' in html
    for phrase in ('21 November 2026', 'first 8 MB', 'TinyLlama 1.1B Chat Q4_K_M',
                   'reader written to the GGUF spec', 'tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf'):
        assert phrase in section, phrase
    assert current.hrefs.count(REPO) == 1
    assert f'<a href="{REPO}">' in section
    use = html.split('<h2>Which one to use</h2>', 1)[1]
    assert '224,164 models' in use and 'read 21 November 2026' in use
    assert not Counter(old.hrefs) - Counter(current.hrefs), 'Original href lost'
    assert len(blocks(html, 'p')) >= len(blocks(original, 'p'))
    for tag in ('p', 'tr', 'a'):
        preserved = Counter(blocks(original, tag))
        if tag == 'p':
            preserved[f'<p>{old_qa}</p>'] -= 1
        assert not preserved - Counter(blocks(html, tag)), f'Original {tag} changed'
    for cls in ('receipts', 'cta'):
        block = re.search(rf'<div class="{cls}">.*?</div>', original, re.S).group(0)
        assert block in html, f'Original {cls} changed'
    assert 'Last updated 2026-11-21' in html
    assert 'name="last-modified" content="2026-11-21"' in html
    assert 'data-claims-checked="2026-11-21"' in html
    claim_set = re.search(r'data-claims-set="([^"]+)"', html).group(1)
    assert 'GGUF file read' in claim_set and 'Hugging Face GGUF model count' in claim_set
    articles = [json.loads(re.search(r'>(.*?)</script>', s, re.S).group(1))
                for s in blocks(html, 'script') if 'application/ld+json' in s]
    article = next(a for a in articles if a.get('@type') == 'Article')
    assert article['dateModified'] == '2026-11-21'
    assert article['datePublished'] == '2026-11-02'
    assert article['headline'] == H1
    assert 'FAQPage' not in html
    assert not any(c in html for c in ('\u2013', '\u2014'))
    ns = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
    entries = ET.fromstring(sitemap).findall('s:url', ns)
    match = [e for e in entries if e.find('s:loc', ns).text == 'https://outlier.host/vs/gguf-vs-ggml/']
    assert len(match) == 1 and match[0].find('s:lastmod', ns).text == '2026-11-21'


def main():
    # The page as it was before this upgrade. Pinned (Outlier, 2026-11-21): `git merge-base HEAD next` gave that commit only
    # BEFORE the merge; on next itself it is the new commit, so CI compared the page with itself and failed. CI checks out
    # full history (fetch-depth: 0), so the pinned commit is always there.
    base = '8018760b0'
    original = subprocess.check_output(['git', 'show', f'{base}:{PAGE}'], cwd=ROOT, text=True)
    html = (ROOT / PAGE).read_text()
    sitemap = (ROOT / 'sitemap.xml').read_text()
    check(html, original, sitemap)
    print('PASS: GGUF additions, figures, dates and original content preserved')
    removed = blocks(original, 'h2')[0]
    try:
        check(html.replace(removed, '', 1), original, sitemap)
    except AssertionError as exc:
        assert str(exc) == 'Original h2 removed or changed', exc
        print(f'PASS: negative control rejected a removed original h2: {exc}')
    else:
        raise AssertionError('Negative control passed with an original h2 removed')
    from seo_lint import visible_text
    print(f'Visible words: {len(visible_text(original).split())} before; {len(visible_text(html).split())} after')


if __name__ == '__main__':
    main()
