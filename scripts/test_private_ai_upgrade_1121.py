#!/usr/bin/env python3
"""Check the private AI server additions and preserve the original article.

Headings and article href counts are literals from the page before this edit.
Download checks use source prefixes so a later release does not break the test.
"""
from collections import Counter
from html import unescape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import parse_qs, urlsplit
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
PAGE = 'best/private-ai-no-cloud/index.html'
ORIGINAL_H2 = [
    'How this page compares them',
    "What 'private AI' really means",
    'The one test that matters',
    'The private options, compared',
    'What to verify yourself',
    'Frequently asked questions',
    'New models worth running',
]
KEPT_HREFS = Counter({
    'https://outlier.host/': 1,
    'https://outlier.host/learn/': 2,
    '/data/local-ai-benchmarks-mac-2026/': 2,
    '/how-to/keep-prompts-private-on-mac/': 1,
    'https://outlier.host/buy/outlier?src=best-private-ai-no-cloud-box-answer': 1,
    'https://github.com/ollama/ollama': 1,
    'https://ollama.com/pricing': 1,
    'https://lmstudio.ai/app-terms': 1,
    'https://lmstudio.ai/pricing': 1,
    'https://github.com/janhq/jan/blob/main/LICENSE': 1,
    'https://github.com/ggml-org/llama.cpp': 1,
    'https://llama.app/': 1,
    'https://huggingface.co/Outlier-Ai': 1,
    'https://outlier.host/buy/outlier?src=best-private-ai-no-cloud-end': 1,
    'https://outlier.host/learn/why-local-ai-keeps-code-private/': 1,
    'https://outlier.host/best/private-ai-no-cloud/': 1,
})
DOWNLOAD_SRC_PREFIXES = [
    'best-private-ai-no-cloud-box-answer',
    'best-private-ai-no-cloud',
]
ORIGINAL_FAQS = [
    'What is the most private AI tool?',
    'Is ChatGPT private?',
    'How do I verify an AI is really private?',
]
NEW_H2 = 'Where a private AI server can run'
NEW_FAQ = "Who can connect to Outlier's local AI server?"
OFFLINE_CHECK = '/learn/check-an-ai-app-is-offline-on-mac/'


def blocks(html, tag):
    return re.findall(rf'<{tag}\b[^>]*>.*?</{tag}>', html, re.S)


def text(html):
    return unescape(re.sub(r'<[^>]+>', '', html)).strip()


class Markup(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.meta = {}
        self.hrefs = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'meta':
            self.meta[attrs.get('name', attrs.get('property'))] = attrs.get('content')
        if 'href' in attrs:
            self.hrefs.append(attrs['href'])


def check(html, sitemap):
    headings = [text(h) for h in blocks(html, 'h2')]
    assert all(h in headings for h in ORIGINAL_H2), 'Original h2 removed or changed'
    assert [h for h in headings if h in ORIGINAL_H2] == ORIGINAL_H2
    assert headings.index(NEW_H2) < headings.index('The private options, compared')
    assert '\u2013' not in html and '\u2014' not in html, 'En or em dash found'
    assert 'entitlement' not in html.lower()

    current = Markup(html)
    title = text(blocks(html, 'title')[0])
    assert len(title) <= 60 and 'private ai server' in title.lower()
    assert title.endswith(' | Outlier')
    h1 = text(blocks(html, 'h1')[0])
    assert h1 == 'A private AI server on your own Mac, with no cloud'
    for key in ('description', 'og:description', 'twitter:description'):
        assert len(current.meta[key]) < 155
        assert 'private ai server' in current.meta[key].lower()
        assert current.meta[key].startswith('A private AI server runs ')
    for key in ('og:title', 'twitter:title'):
        assert current.meta[key] == title

    article = blocks(html, 'article')[0]
    hrefs = Markup(article).hrefs
    assert not KEPT_HREFS - Counter(hrefs), 'Original article href lost'
    downloads = [urlsplit(h) for h in hrefs if urlsplit(h).path == '/dl/outlier']
    assert len(downloads) == 2
    sources = [parse_qs(h.query).get('src', [''])[0] for h in downloads]
    assert all(src.startswith(prefix) for src, prefix in zip(sources, DOWNLOAD_SRC_PREFIXES))
    assert OFFLINE_CHECK in hrefs and '/learn/is-local-ai-safe/' in hrefs
    qa = re.search(r'<div class="quick-answer">.*?<p>(.*?)</p>', html, re.S).group(1)
    # The quick answer shares one paragraph with the measured-answer sentences (test_measured_answers_2, O8);
    # the direct answer is its first two sentences.
    answer = ' '.join(re.split(r'(?<=[.!?])\s+(?=[A-Z])', text(qa))[:2])
    assert len(answer.split()) <= 60, 'direct answer too long'
    assert text(qa).startswith('A private AI server runs the model on hardware you control')
    assert 'so prompts are not sent to an AI vendor' in text(qa)
    assert 'never reach a vendor' not in html

    section = article.split(f'<h2>{NEW_H2}</h2>', 1)[1].split('<h2>', 1)[0]
    assert '4 November 2026 capture' in text(section), 'dated capture missing from the new section'
    table = blocks(section, 'table')[0]
    assert '<div class="table-scroll">' in section
    assert [text(h) for h in blocks(table, 'th')] == [
        'Where it runs', 'Who holds the hardware', 'Who can connect', 'How you check it',
    ]
    rows = blocks(blocks(table, 'tbody')[0], 'tr')
    assert len(rows) == 4 and all(len(blocks(r, 'td')) == 4 for r in rows)
    for phrase in ('127.0.0.1:8766', 'sampled 22 times', 'Sockets leaving the Mac: 0',
                   'past capture', 'web search off'):
        assert phrase in section

    schemas = [json.loads(re.search(r'>(.*?)</script>', s, re.S).group(1))
               for s in blocks(html, 'script') if 'application/ld+json' in s]
    structured_article = next(s for s in schemas if s.get('@type') == 'Article')
    assert structured_article['headline'] == h1
    assert structured_article['dateModified'] == '2026-11-21'
    assert 'Last updated 2026-11-21' in html
    assert current.meta['last-modified'] == '2026-11-21'
    assert 'claim set above, dated 2026-11-20' in article
    faq = next(s for s in schemas if s.get('@type') == 'FAQPage')['mainEntity']
    assert [q['name'] for q in faq] == ORIGINAL_FAQS + [NEW_FAQ]
    visible = re.search(r'<h3>' + re.escape(NEW_FAQ) + r'</h3>\s*<p>(.*?)</p>', article, re.S)
    assert visible and f'href="{OFFLINE_CHECK}"' in visible[1]
    answer = next(q['acceptedAnswer']['text'] for q in faq if q['name'] == NEW_FAQ)
    assert text(visible[1]) == answer
    for phrase in ('127.0.0.1', "app's local key", '4 November 2026 capture', 'lsof'):
        assert phrase in answer
    for question in ORIGINAL_FAQS:
        assert f'<h3>{question}</h3>' in article

    ns = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
    entries = ET.fromstring(sitemap).findall('s:url', ns)
    match = [e for e in entries if e.find('s:loc', ns).text ==
             'https://outlier.host/best/private-ai-no-cloud/']
    assert len(match) == 1 and match[0].find('s:lastmod', ns).text == '2026-11-21'


def main():
    html = (ROOT / PAGE).read_text()
    sitemap = (ROOT / 'sitemap.xml').read_text()
    check(html, sitemap)
    print('PASS: private AI server additions, links, FAQ and dates')
    for name, mutated, expected in [
        ('removed original h2', html.replace(f'<h2>{ORIGINAL_H2[0]}</h2>', '', 1),
         'Original h2 removed or changed'),
        ('en dash', html.replace('</h1>', '\u2013</h1>', 1), 'En or em dash found'),
    ]:
        try:
            check(mutated, sitemap)
        except AssertionError as exc:
            assert str(exc) == expected, exc
            print(f'PASS: negative control rejected {name}: {exc}')
        else:
            raise AssertionError(f'Negative control passed: {name}')
    for path in ROOT.rglob('index.html'):
        if path == ROOT / PAGE or any(p in path.parts for p in ('.git', 'node_modules')):
            continue
        assert NEW_FAQ not in unescape(path.read_text()), f'FAQ reused in {path}'
    print('PASS: new FAQ is unique on the site')


if __name__ == '__main__':
    main()
