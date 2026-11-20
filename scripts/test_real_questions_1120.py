#!/usr/bin/env python3
"""Offline checks for three real search questions, including failing controls.

Rival prices are pinned to the supplied 20 November vendor reads. No network,
model, sound, real index or commit is used. Historical page-content tests still
run; their old whole-commit scope assertions do not apply to later work.
"""
from html.parser import HTMLParser
import html
import importlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import unittest
from urllib.parse import urlsplit
from xml.etree import ElementTree

from near_dup_gate import words, shingles
from test_private_ai_pages_1120 import visible

# Retired the 20 November real-search-questions job's old-base scope and byte pins:
# later reviewed sitewide edits make those byte pins wrong.
ROOT = Path(__file__).resolve().parent.parent
LM = 'vs/lm-studio-vs-jan/index.html'
MSTY = 'vs/msty-alternatives/index.html'
CURSOR = 'learn/can-cursor-use-a-local-model-on-a-mac/index.html'
PAGES = (LM, MSTY, CURSOR)
NEW = (LM, MSTY)
QUICK = re.compile(r'<div class="quick-answer"[^>]*>.*?</div>', re.S)
STAMP = 'measured on Outlier 1.11.1012, 17 Nov 2026'
MONEY = re.compile(r'\$\d+(?:\.\d+)?')
# Include the amount AND billing period, rather than permitting a price anywhere.
PRICES = {
    'LM Studio': (('$0.00', '$20.00', '$100.00'), ('Free', 'Bionic+', 'Pro', 'a month')),
    'Msty Studio': (('$0.00', '$149.00', '$349.00'), ('Free', 'a year per user', 'one-time per user')),
    'Ollama': (('$0.00', '$20.00'), ('local use', 'a month')),
    'Cursor': (('$8.00',), ('Plus', 'a month')),
    'Jan': ((), ()), 'AnythingLLM': ((), ()), 'GPT4All': ((), ()),
}
SOURCES = {
    'LM Studio': {'https://lmstudio.ai/', 'https://lmstudio.ai/pricing',
                  'https://lmstudio.ai/app-terms', 'https://lmstudio.ai/download',
                  'https://lmstudio.ai/docs/app/system-requirements',
                  'https://lmstudio.ai/docs/developer/openai-compat'},
    'Jan': {'https://github.com/janhq/jan', 'https://docs.jan.ai/desktop/api-server'},
    'Msty Studio': {'https://msty.ai/products/studio/', 'https://msty.ai/pricing/'},
    'Ollama': {'https://github.com/ollama/ollama', 'https://ollama.com/pricing',
               'https://docs.ollama.com/macos'},
    'AnythingLLM': {'https://anythingllm.com/', 'https://anythingllm.com/download',
                    'https://github.com/Mintplex-Labs/anything-llm'},
    'GPT4All': {'https://github.com/nomic-ai/gpt4all', 'https://www.nomic.ai/gpt4all'},
    'Cursor': {'https://forum.cursor.com/t/156489', 'https://forum.cursor.com/t/177245',
               'https://cursor.com/docs/settings/api-keys', 'https://cursor.com/pricing',
               'https://cursor.com/docs/models-and-pricing'},
}


def shown(raw):
    # Product offer spans are present in source but hidden until the dated reveal.
    raw = re.sub(r'<span\b[^>]*\bhidden[^>]*>.*?</span>', '', raw, flags=re.S)
    return visible(raw).text


class ClaimBlocks(HTMLParser):
    """Read whole dated blocks, including nested links, without a non-greedy div regex."""
    def __init__(self, raw):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.blocks = []
        self.feed(raw)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        for block in self.stack:
            if tag == 'a':
                block['links'].append(a.get('href', ''))
        if tag not in {'meta', 'link', 'img', 'br', 'hr', 'input'}:
            self.stack.append({'tag': tag, 'attrs': a, 'parts': [], 'links': []})

    def handle_data(self, data):
        for block in self.stack:
            block['parts'].append(data)

    def handle_endtag(self, tag):
        if not self.stack or self.stack[-1]['tag'] != tag:
            return
        block = self.stack.pop()
        if 'data-claims-checked' in block['attrs']:
            block['text'] = ' '.join(' '.join(block['parts']).split())
            self.blocks.append(block)


def schemas(raw):
    return [json.loads(s) for s in re.findall(
        r'<script type="application/ld\+json">(.*?)</script>', raw, re.S)]


def check_page(raw, rel):
    title = html.unescape(re.search(r'<title>(.*?)</title>', raw).group(1))
    assert len(title) <= 60, 'title too long'
    needed = ('LM Studio', 'Jan') if rel == LM else ('Msty', 'alternatives') if rel == MSTY else ('Cursor', 'local model', 'Not directly')
    assert all(w in title for w in needed), 'title words'
    desc = html.unescape(re.search(r'<meta name="description" content="([^"]*)"', raw).group(1))
    assert len(desc) <= 155, 'description too long'
    matches = list(QUICK.finditer(raw))
    assert len(matches) == 1, 'expected one quick answer'
    quick = matches[0]
    assert raw.index('<h1') < quick.start() < quick.end() < raw.index('<h2'), 'answer must precede the first h2'
    answer = ' '.join(shown(p) for p in re.findall(r'<p>(.*?)</p>', quick.group(), re.S))
    assert 2 <= len(re.split(r'(?<=[.!?])\s+(?=[A-Z])', answer)) <= 4, 'two to four sentences'
    assert '0.69 seconds' in answer and 'official openai Python SDK' in answer, 'missing measured figure'
    assert STAMP in answer, 'missing measurement build/date'
    assert '1.11.1013' not in answer, 'unapproved measurement build'
    assert 'name="last-modified" content="2026-11-20"' in raw, 'meta date'
    assert 'Last updated 20 November 2026' in shown(raw), 'visible date'
    article = next(s for s in schemas(raw) if s.get('@type') == 'Article')
    assert article['dateModified'] == '2026-11-20', 'schema date'
    assert article['author'] == {'@type':'Person', 'name':'Matthew Kerr', 'url':'https://outlier.host/about/'}, 'author'
    blocks = ClaimBlocks(raw).blocks
    assert blocks, 'missing rival blocks'
    for block in blocks:
        assert block['attrs']['data-claims-checked'] == '2026-11-20', 'rival block date'
        assert '20 November 2026' in block['text'], 'rival visible date'
        names = block['attrs']['data-claims-set']
        allowed = {p for name, (prices, _) in PRICES.items() if name in names for p in prices}
        assert set(MONEY.findall(block['text'])) <= allowed, 'rival price differs from supplied facts'
        if block['tag'] in {'section', 'li'}:
            assert names in SOURCES, 'unknown rival block'
            assert SOURCES[names] <= set(block['links']) or names == 'LM Studio' and rel == MSTY, 'missing vendor link'
            prices, terms = PRICES[names]
            if MONEY.search(block['text']):
                assert set(MONEY.findall(block['text'])) == set(prices), 'rival price missing'
                assert all(term in block['text'] for term in terms), 'billing period or plan'
    # Pin price periods in the opening as well as the detailed vendor entries.
    for amount, period in (('$149.00', 'a year per user'), ('$349.00', 'one-time per user'),
                           ('$100.00', 'a month'), ('$8.00', 'a month')):
        for block in blocks:
            if amount in block['text']:
                assert amount + ' ' + period in block['text'], 'rival billing period'
    for block in blocks:
        if '$20.00' in block['text']:
            assert '$20.00 a month' in block['text'] or '$20.00 and $100.00 a month' in block['text'], 'rival billing period'
    assert 'data-claims-checked="2026-11-20"' in quick.group(), 'undated quick answer'
    if rel in NEW:
        expected_sections = 2 if rel == LM else 1
        assert len([b for b in blocks if b['tag'] == 'section']) == expected_sections, 'undated rival section'
        assert len([b for b in blocks if b['tag'] == 'div' and b['attrs'].get('class') == 'faq']) == 1, 'undated FAQ'
        if rel == MSTY:
            assert {b['attrs']['data-claims-set'] for b in blocks if b['tag'] == 'li'} == {
                'LM Studio', 'Jan', 'Ollama', 'AnythingLLM', 'GPT4All'}, 'undated list entry'
    links = set(visible(raw).links)
    required = {'LM Studio', 'Jan'} if rel == LM else set(SOURCES)-{'Cursor'} if rel == MSTY else {'Cursor'}
    for name in required:
        assert any(name in b['attrs']['data-claims-set'] for b in blocks), 'undated rival'
        assert SOURCES[name] <= links if rel != MSTY or name != 'LM Studio' else {
            'https://lmstudio.ai/pricing', 'https://lmstudio.ai/app-terms',
            'https://lmstudio.ai/docs/app/system-requirements'} <= links, 'missing source'
    if rel == CURSOR:
        for phrase in ('localhost cannot reach your Mac', 'public HTTPS tunnel', 'chat models only',
                       "Tab stays on Cursor's models", '$8.00 a month', 'excludes your own API keys'):
            assert phrase in answer, 'missing Cursor limit: '+phrase
    if rel in NEW:
        text = shown(re.search(r'<article>.*?</article>', raw, re.S).group())
        assert len(text.split()) > 600, 'article needs substance'
        assert 'I make Outlier.' in text, 'missing disclosure'
        assert not re.search(r'[\u2013\u2014]|\b\d{4}-\d{2}-\d{2}\b', text), 'visible dash or ISO date'
        assert not re.search(r'\b(?:Codex|gate|job|Article Studio|RULES|chain|bar|C38)\b', text), 'internal words'
        assert not any('kerrandcompanyholdings.com' in urlsplit(u).netloc for u in links), 'other Kerr domain'
        faq = [(shown(q), shown(a)) for q,a in re.findall(
            r'<div class="faq-item"><h3>(.*?)</h3><p>(.*?)</p></div>', raw, re.S)]
        schema = next(s for s in schemas(raw) if s.get('@type') == 'FAQPage')
        assert 3 <= len(faq) <= 5, 'FAQ count'
        assert faq == [(q['name'],q['acceptedAnswer']['text']) for q in schema['mainEntity']], 'FAQ schema mismatch'
        assert len({q.casefold() for q,a in faq}) == len(faq), 'duplicate FAQ'
        if rel == MSTY:
            gpt = next(b for b in blocks if b['attrs']['data-claims-set'] == 'GPT4All' and b['tag'] == 'li')
            assert not re.search(r'\bfree\b', gpt['text'], re.I), 'GPT4All free claim'
            assert 'MIT-licensed on GitHub' in gpt['text'], 'GPT4All licence'
            assert len(re.findall(r'<li(?: data-claims[^>]*)?>\s*<h3>', raw)) == 6, 'six real list entries'
    return title, answer


class RealQuestions(unittest.TestCase):
    def test_pages_and_controls(self):
        for rel in PAGES:
            with self.subTest(page=rel):
                self.assertTrue((ROOT / rel).is_file())
                raw = (ROOT / rel).read_text()
                title, answer = check_page(raw, rel)
                quick = QUICK.search(raw).group()
                plants = [
                    (raw.replace('0.69 seconds', '0.68 seconds'), 'measured figure'),
                    (raw.replace('1.11.1012, 17 Nov', '1.11.1013, 17 Nov'), 'measurement build/date'),
                    (raw.replace('data-claims-checked="2026-11-20"', 'data-claims-checked="2026-11-19"'), 'rival block date'),
                    (raw.replace(quick, '', 1).replace('</article>', quick+'</article>', 1), 'precede the first h2'),
                ]
                if rel == CURSOR:
                    plants += [(raw.replace('$8.00', '$9.00'), 'rival price'),
                               (raw.replace('localhost cannot reach your Mac', 'localhost reaches your Mac'), 'Cursor limit')]
                else:
                    plants += [(raw.replace('$20.00', '$21.00'), 'rival price'),
                               (raw.replace('$100.00 a month', '$100.00 a year'), 'rival billing period'),
                               (raw.replace('"acceptedAnswer": {"@type": "Answer", "text": "',
                                            '"acceptedAnswer": {"@type": "Answer", "text": "Wrong. ', 1), 'FAQ schema mismatch')]
                if rel == MSTY:
                    plants += [(raw.replace('MIT-licensed on GitHub', 'free and MIT-licensed on GitHub'), 'GPT4All free'),
                               (raw.replace('$149.00 a year per user', '$149.00 a month per user'), 'rival billing period'),
                               (raw.replace('<li data-claims-checked="2026-11-20" data-claims-set="Jan">', '<li>'), 'undated list entry')]
                for planted, error in plants:
                    self.assertNotEqual(raw, planted, 'control did not land')
                    with self.assertRaisesRegex(AssertionError, error):
                        check_page(planted, rel)
                print(f'{rel}: {title}\nQuick answer: {answer}', flush=True)

    def test_discovery_faq_and_similarity(self):
        ns = {'s':'http://www.sitemaps.org/schemas/sitemap/0.9'}
        sitemap = ElementTree.fromstring((ROOT / 'sitemap.xml').read_text())
        corpus = {}
        all_faqs = {}
        for p in ROOT.rglob('index.html'):
            if any(d in p.parts for d in ('.git', 'node_modules', '_seo_build')):
                continue
            raw = p.read_text()
            w = words(raw)
            if w:
                corpus[p.relative_to(ROOT).as_posix()] = shingles(w)
            for s in schemas(raw):
                if s.get('@type') == 'FAQPage':
                    for q in s.get('mainEntity', []):
                        all_faqs.setdefault(q['name'].strip().casefold(), []).append(p.relative_to(ROOT).as_posix())
        for rel in PAGES:
            path = '/' + rel.removesuffix('index.html')
            entries = [n for n in sitemap.findall('s:url', ns) if n.findtext('s:loc', namespaces=ns) == 'https://outlier.host'+path]
            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0].findtext('s:lastmod', namespaces=ns), '2026-11-20')
            if rel in NEW:
                inbound = ['vs/index.html', 'vs/mac-native-ai-comparison/index.html']
                if rel == LM:
                    inbound.append('vs/jan-vs-ollama/index.html')
                for hub in inbound:
                    self.assertIn(path, {urlsplit(u).path for u in visible((ROOT / hub).read_text()).links}, hub)
                for s in schemas((ROOT / rel).read_text()):
                    if s.get('@type') == 'FAQPage':
                        for q in s['mainEntity']:
                            self.assertEqual(all_faqs[q['name'].casefold()], [rel], 'FAQ unique across site')
            a = corpus[rel]
            pairs = [(len(a & b)/len(a | b), other) for other,b in corpus.items() if other != rel]
            score, other = max(pairs)
            self.assertLess(score, .5, (rel, other))
            print(f'{rel}: {len(words((ROOT / rel).read_text()))} body words; max Jaccard {score:.4f} with {other}', flush=True)
        lm_links = {urlsplit(u).path for u in visible((ROOT / LM).read_text()).links}
        self.assertTrue({'/vs/jan-vs-ollama/', '/vs/ollama-vs-lm-studio/'} <= lm_links)
        self.assertIn('/vs/outlier-vs-msty/', {urlsplit(u).path for u in visible((ROOT / MSTY).read_text()).links})
        # A whole-page copy must be rejected by the same similarity measure.
        self.assertEqual(len(corpus[MSTY] & corpus[MSTY])/len(corpus[MSTY] | corpus[MSTY]), 1)

    def test_cursor_faq_matches_visible_text(self):
        raw = (ROOT / CURSOR).read_text()
        faq = [(shown(q), shown(a)) for q, a in re.findall(
            r'<div class="faq-item">\s*<h3>(.*?)</h3>\s*<p>(.*?)</p>\s*</div>', raw, re.S)]
        schema = next(s for s in schemas(raw) if s.get('@type') == 'FAQPage')
        self.assertTrue(faq)
        self.assertEqual(faq, [(q['name'], q['acceptedAnswer']['text'])
                               for q in schema['mainEntity']])

    def test_earlier_content(self):
        suite = unittest.TestSuite()
        for name in ('test_private_ai_pages_1120', 'test_private_ai_pages_2_1120'):
            suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(importlib.import_module(name)))
        for name in ('test_measured_answers', 'test_measured_answers_2', 'test_measured_answers_3', 'test_measured_answers_3b'):
            module = importlib.import_module(name)
            cls = next(c for n,c in vars(module).items() if n.startswith('MeasuredAnswers') and isinstance(c,type))
            suite.addTest(cls('test_answers_and_controls'))
        result = unittest.TextTestRunner(verbosity=1).run(suite)
        self.assertTrue(result.wasSuccessful(), 'earlier page content failed')

    def test_pre_push_claim_gates_on_working_tree(self):
        # These are the two unchanged commands in scripts/githooks/pre-push.
        hook = (ROOT / 'scripts/githooks/pre-push').read_text()
        for name in ('claim_freshness_gate', 'faq_schema_visible_gate'):
            command = f'python3 scripts/{name}.py .'
            self.assertIn(command, hook)
            result = subprocess.run(command.split(), cwd=ROOT, text=True, capture_output=True,
                                    env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))
            print(result.stdout.splitlines()[-1], flush=True)
            self.assertEqual(result.returncode, 0, result.stdout+result.stderr)


if __name__ == '__main__':
    sys.dont_write_bytecode = True
    unittest.main(verbosity=2)
