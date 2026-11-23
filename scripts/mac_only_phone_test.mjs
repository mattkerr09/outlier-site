#!/usr/bin/env node
// Run the shared js/mac-only.js offline against a small DOM with the page shapes the site really has (23 Nov 2026 tally
// of every .dmg link's parents): the home hero's .cta-bar > .cta-row, a p.pbox-btns pricing box, an article's div.cta card
// with Download and Buy inline, a lone a.cta in the page wrapper, a list, and nav/header/footer (skipped).
//
// What it holds (CEO, 23 Nov 2026, under RULES 71, keeping the 21 Nov call):
// - phones/tablets: a full-width OUTLINE button "Email yourself the Mac download link" right under Download and Buy,
//   that always opens an email (its label says email), then the requirement line; Download and Buy are untouched;
// - Windows/ChromeOS/Linux: the one plain line with "Send yourself the Mac link." (share sheet, else email);
// - a Mac: nothing at all.
// CONTROL: MAC_ONLY_JS=<the 21 Nov js/mac-only.js> node scripts/mac_only_phone_test.mjs  -> every non-Mac case FAILs
// (no phone button, and the lone a.cta's note lands after the whole page wrapper).
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { runInNewContext } from 'node:vm';

const source = readFileSync(process.env.MAC_ONLY_JS || new URL('../js/mac-only.js', import.meta.url), 'utf8');
const DMG = 'https://outlier.host/dl/outlier?src=phone-test&to=https://example.test/Outlier-1.11.1020-arm64.dmg';

class Element {
  constructor(tag, attributes = {}) {
    this.tagName = tag.toUpperCase();
    this.attributes = { ...attributes };
    this.children = [];
    this.parentNode = null;
    this.listeners = {};
    const self = this;
    this.classList = {
      contains: name => self.className.split(/\s+/).includes(name),
      add: name => { if (!self.classList.contains(name)) self.className = `${self.className} ${name}`.trim(); }
    };
  }
  get className() { return this.attributes.class || ''; }
  set className(value) { this.attributes.class = value; }
  get textContent() { return this.children.map(child => child.textContent).join(''); }
  set textContent(value) { this.children = [{ textContent: value }]; }
  get nextSibling() {
    const siblings = this.parentNode.children;
    return siblings[siblings.indexOf(this) + 1] || null;
  }
  get nextElementSibling() {
    const siblings = this.parentNode.children;
    return siblings.slice(siblings.indexOf(this) + 1).find(node => node instanceof Element) || null;
  }
  setAttribute(name, value) { this.attributes[name] = value; }
  appendChild(child) { return this.insertBefore(child, null); }
  insertBefore(child, reference) {
    const index = reference === null ? this.children.length : this.children.indexOf(reference);
    assert.ok(index >= 0, 'insertBefore reference must be a child');
    child.parentNode = this;
    this.children.splice(index, 0, child);
    return child;
  }
  matches(selector) {
    if (selector.startsWith('.')) return this.classList.contains(selector.slice(1));
    if (selector === 'a[href$=".dmg"]') return this.tagName === 'A' && (this.attributes.href || '').endsWith('.dmg');
    assert.match(selector, /^[a-z]+$/, `selector the fixture does not model: ${selector}`);
    return this.tagName === selector.toUpperCase();
  }
  closest(selector) {
    const selectors = selector.split(',').map(value => value.trim());
    for (let node = this; node instanceof Element; node = node.parentNode) {
      if (selectors.some(value => node.matches(value))) return node;
    }
    return null;
  }
  querySelectorAll(selector) {
    return this.children.flatMap(child => child instanceof Element
      ? [...(child.matches(selector) ? [child] : []), ...child.querySelectorAll(selector)] : []);
  }
  addEventListener(name, handler, capture = false) { this.listeners[name] = { handler, capture }; }
}

function fixture(navigator) {
  const document = new Element('document');
  document.documentElement = document.appendChild(new Element('html'));
  document.head = document.documentElement.appendChild(new Element('head'));
  const body = document.documentElement.appendChild(new Element('body'));
  document.createElement = tag => new Element(tag);
  document.createTextNode = textContent => ({ textContent });
  const links = [];
  const el = (parent, tag, attributes) => parent.appendChild(new Element(tag, attributes));
  const download = (parent, cls = 'btn') => { const a = el(parent, 'a', { class: cls, href: DMG }); links.push(a); return a; };
  const buy = (parent, cls = 'btn') => { const a = el(parent, 'a', { class: cls, href: '/buy/outlier?src=test' }); links.push(a); return a; };
  const space = parent => parent.children.push({ textContent: ' ' });  // the " " between Download and Buy

  const skipped = ['nav', 'header', 'footer'].map(tag => { const c = el(body, tag); download(el(c, 'div')); return c; });
  const wrap = el(body, 'div', { class: 'wrap' });
  // where each note must land: [parent the note goes in, the element it must follow]
  const expect = [];

  const bar = el(wrap, 'div', { class: 'cta-bar' });                        // home hero
  const row = el(bar, 'div', { class: 'cta-row' });
  download(row, 'btn btn-primary'); buy(row, 'btn btn-ghost');
  el(bar, 'p', { class: 'trust' });
  expect.push(['hero row', bar, row]);

  const pbox = el(wrap, 'div', { class: 'pbox' });                          // pricing box (191 pages)
  const btns = el(pbox, 'p', { class: 'pbox-btns' });
  download(btns, 'pbox-dl'); space(btns); buy(btns, 'pbox-buy');
  el(pbox, 'p', { class: 'pbox-req' });
  expect.push(['pricing box', pbox, btns]);

  const card = el(wrap, 'div', { class: 'cta' });                           // article card (166 pages)
  el(card, 'h3'); el(card, 'p');
  download(card); space(card); const cardBuy = buy(card);
  el(card, 'p', { class: 'phone-link' });
  expect.push(['article card', card, cardBuy]);

  const lone = download(wrap, 'cta');                                       // a.cta straight in the wrapper (23 pages)
  el(wrap, 'p', { class: 'phone-link' });
  expect.push(['lone a.cta', wrap, lone]);

  const list = el(wrap, 'ul');                                              // a list item
  download(el(list, 'li'));
  expect.push(['list', wrap, list]);

  const events = [];
  const window = { plausible: (name, options) => events.push({ name, ...options }) };
  const location = { pathname: '/phone-test/', href: 'https://outlier.host/phone-test/' };
  const before = links.map(a => ({ ...a.attributes }));
  runInNewContext(source, { document, navigator, window, location });
  return { document, skipped, expect, links, before, events, window, location };
}

const mailto = url => 'mailto:?subject=' + encodeURIComponent('Outlier for Mac: download link') + '&body=' +
  encodeURIComponent('Outlier for Mac is free to start. Open this on your Mac to download it.\n\n' + url);
const SHARE_URL = 'https://outlier.host/?utm_source=phone-share&utm_medium=share';

const cases = [
  { name: 'iPhone', phone: true, navigator: { userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X)', platform: 'iPhone' } },
  { name: 'Android', phone: true, navigator: { userAgent: 'Mozilla/5.0 (Linux; Android 15; Pixel 9) AppleWebKit/537.36', platform: 'Linux armv8l' } },
  { name: 'iPad', phone: true, navigator: { userAgent: 'Mozilla/5.0 (iPad; CPU OS 18_0 like Mac OS X)', platform: 'iPad' } },
  { name: 'iPadOS desktop UA', kind: 'iPad', phone: true, navigator: { userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)', platform: 'MacIntel', maxTouchPoints: 5 } },
  { name: 'Windows', navigator: { userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', platform: 'Win32' } },
  { name: 'Linux', navigator: { userAgent: 'Mozilla/5.0 (X11; Linux x86_64)', platform: 'Linux x86_64' } },
  { name: 'ChromeOS', navigator: { userAgent: 'Mozilla/5.0 (X11; CrOS x86_64 16093.0.0)', platform: 'Linux x86_64' } },
  { name: 'Mac', mac: true, navigator: { userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)', platform: 'MacIntel' } }
];

for (const test of cases) {
  try {
    const kind = test.kind || test.name;
    const f = fixture({ ...test.navigator });
    const notes = f.document.querySelectorAll('.mac-only-note');
    const css = f.document.head.textContent;
    f.links.forEach((a, i) => assert.deepEqual(a.attributes, f.before[i], 'Download and Buy links are never changed'));
    for (const c of f.skipped) assert.equal(c.querySelectorAll('.mac-only-note').length, 0, 'skip nav, header and footer');
    if (test.mac) {
      assert.equal(notes.length, 0);
      assert.equal(css, '');
      assert.equal(f.document.documentElement.className, '');
      assert.deepEqual(f.document.listeners, {});
      console.log(`PASS ${test.name}`);
      continue;
    }
    assert.equal(notes.length, f.expect.length, 'one note per Download group');
    assert.ok(f.document.documentElement.classList.contains('not-mac'));
    assert.ok(css.includes('html.not-mac .phone-link{display:none !important;}'), 'the pages\' own phone line hides');
    for (const [where, parent, follows] of f.expect) {
      const note = parent.children[parent.children.indexOf(follows) + 1];
      assert.ok(note && notes.includes(note), `${where}: the note sits right after Download/Buy`);
      assert.equal(note.attributes.role, 'note');
      const button = note.querySelectorAll('button')[0];
      assert.equal(button.type, 'button');
      if (test.phone) {
        assert.equal(note.className, 'mac-only-note mac-only-phone', `${where}: phone note`);
        assert.equal(button.className, 'mac-link-btn');
        assert.equal(button.attributes['data-kc-cta'], '', 'the shared pill steps aside from it');
        assert.equal(button.textContent, 'Email yourself the Mac download link');
        assert.equal(note.children[1].textContent, 'Outlier runs on Apple Silicon Macs (macOS 15+).');
      } else {
        assert.equal(note.className, 'mac-only-note', `${where}: desktop note`);
        assert.equal(note.textContent, 'Outlier runs on Apple Silicon Macs (macOS 15+). Not at your Mac? Send yourself the Mac link.');
      }
    }
    if (test.phone) {
      // full width, outlined (not filled), 44 px tall
      assert.match(css, /\.mac-only-phone \.mac-link-btn\{display:block;width:100%;min-height:44px;/);
      assert.match(css, /\.mac-link-btn\{[^}]*background:transparent;border:1\.5px solid currentColor;/);
      assert.match(css, /\.mac-link-btn\{[^}]*border-color:color-mix\(in srgb,currentColor 45%,transparent\);/,
        'a softer outline than Buy Pro');
      assert.match(css, /\.mac-only-phone\{flex:1 0 100%;width:100%;/, 'takes its own row in the hero flex bar');
    }

    // Sending: a phone always opens an email, even where a share sheet exists; a desktop shares, else emails.
    let shared = null;
    const s = fixture({ ...test.navigator, share: data => { shared = data; return Promise.resolve(); } });
    s.window.kcCarry = url => url + '&carried=1';
    s.document.querySelectorAll('.mac-only-note')[0].querySelectorAll('button')[0].listeners.click.handler();
    const from = test.phone ? 'phone-button' : 'mac-only-note';
    if (test.phone) {
      assert.equal(shared, null, 'the "Email" button never opens the share sheet');
      assert.equal(s.location.href, mailto(SHARE_URL + '&carried=1'));
    } else {
      assert.equal(JSON.stringify(shared), JSON.stringify({ title: 'Outlier for Mac',
        text: 'Outlier for Mac is free to start. Open this on your Mac to download it.', url: SHARE_URL + '&carried=1' }));
      notes[0].querySelectorAll('button')[0].listeners.click.handler();     // no share sheet: an email
      assert.equal(f.location.href, mailto(SHARE_URL));
    }
    assert.equal(JSON.stringify(s.events), JSON.stringify([{ name: 'Send Mac Link', props: { from, platform: kind } }]));

    assert.equal(f.document.listeners.click.capture, true);
    const hero = f.links[0];
    f.document.listeners.click.handler({ target: hero.appendChild(new Element('svg')) });
    assert.equal(JSON.stringify(f.events.at(-1)), JSON.stringify({ name: 'Download non-Mac', props: { platform: kind, page: '/phone-test/' } }));
    console.log(`PASS ${test.name}`);
  } catch (error) {
    console.error(`FAIL ${test.name}: ${error.message}`);
    process.exitCode = 1;
  }
}
