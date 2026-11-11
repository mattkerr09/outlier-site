#!/usr/bin/env node
// Run the shared script offline with just the DOM operations it uses.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { runInNewContext } from 'node:vm';

const source = readFileSync(new URL('../js/mac-only.js', import.meta.url), 'utf8');

class Element {
  constructor(tagName, attributes = {}) {
    this.tagName = tagName;
    this.attributes = { ...attributes };
    this.children = [];
    this.parentNode = null;
    this.listeners = {};
    this.classList = {
      contains: name => this.className.split(/\s+/).includes(name),
      add: name => {
        if (!this.classList.contains(name)) this.className = `${this.className} ${name}`.trim();
      },
      remove: name => {
        this.className = this.className.split(/\s+/).filter(value => value !== name).join(' ');
      }
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
    if (selector === 'a[href$=".dmg"]') {
      return this.tagName === 'a' && (this.attributes.href || '').endsWith('.dmg');
    }
    assert.match(selector, /^[a-z]+$/);
    return this.tagName === selector;
  }
  closest(selector) {
    const selectors = selector.split(',').map(value => value.trim());
    for (let node = this; node; node = node.parentNode) {
      if (selectors.some(value => node.matches(value))) return node;
    }
    return null;
  }
  querySelectorAll(selector) {
    return this.children.flatMap(child => child instanceof Element
      ? [...(child.matches(selector) ? [child] : []), ...child.querySelectorAll(selector)] : []);
  }
  addEventListener(name, handler, capture = false) {
    this.listeners[name] = { handler, capture };
  }
}

function fixture(navigator) {
  const document = new Element('document');
  document.documentElement = document.appendChild(new Element('html'));
  document.head = document.documentElement.appendChild(new Element('head'));
  const body = document.documentElement.appendChild(new Element('body'));
  document.createElement = tag => new Element(tag);
  document.createTextNode = textContent => ({ textContent });
  const links = [];
  function download(parent, classes = 'btn btn-primary btn-sm') {
    const link = parent.appendChild(new Element('a', {
      class: classes,
      href: 'https://outlier.host/dl/outlier?src=phone-test&to=https://example.test/Outlier-arm64.dmg',
      target: '_blank',
      rel: 'noopener noreferrer nofollow'
    }));
    links.push({ link, original: { ...link.attributes } });
    return link;
  }
  const skipped = ['nav', 'header', 'footer'].map(tag => {
    const container = body.appendChild(new Element(tag));
    download(container.appendChild(new Element('div')));
    return container;
  });
  const main = body.appendChild(new Element('main'));
  const boxes = [
    main.appendChild(new Element('div', { class: 'cta-bar' })),
    main.appendChild(new Element('div', { class: 'pbox-btns' })),
    main.appendChild(new Element('p')),
    main.appendChild(new Element('ul')),
    main.appendChild(new Element('ol'))
  ];
  for (const box of boxes) {
    const parent = ['ul', 'ol'].includes(box.tagName) ? box.appendChild(new Element('li')) : box;
    download(parent);
    download(parent, 'btn btn-primary'); // One note per box, but demote both links.
    download(parent, 'text-link btn-primary'); // Do not add button styling to a text link.
    box.appendChild(new Element('a', { class: 'btn btn-primary', href: '/buy/outlier?src=test' }));
  }
  const events = [];
  const window = { plausible: (name, options) => events.push({ name, ...options }) };
  const location = { pathname: '/phone-test/', href: 'https://outlier.host/phone-test/' };
  runInNewContext(source, { document, navigator, window, location });
  return { document, main, boxes, skipped, links, events, window, location };
}

const cases = [
  { name: 'iPhone', phone: true, navigator: {
    userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X)', platform: 'iPhone'
  } },
  { name: 'Android', phone: true, navigator: {
    userAgent: 'Mozilla/5.0 (Linux; Android 15; Pixel 9) AppleWebKit/537.36', platform: 'Linux armv8l'
  } },
  { name: 'Windows', navigator: {
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', platform: 'Win32'
  } },
  { name: 'Mac', mac: true, navigator: {
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)', platform: 'MacIntel'
  } },
  { name: 'iPad', phone: true, navigator: {
    userAgent: 'Mozilla/5.0 (iPad; CPU OS 18_0 like Mac OS X)', platform: 'iPad'
  } },
  { name: 'iPadOS desktop UA', kind: 'iPad', phone: true, navigator: {
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)', platform: 'MacIntel', maxTouchPoints: 5
  } },
  { name: 'Linux', navigator: {
    userAgent: 'Mozilla/5.0 (X11; Linux x86_64)', platform: 'Linux x86_64'
  } },
  { name: 'ChromeOS', navigator: {
    userAgent: 'Mozilla/5.0 (X11; CrOS x86_64 16093.0.0)', platform: 'Linux x86_64'
  } }
];

for (const test of cases) {
  try {
    const f = fixture({ ...test.navigator });
    const notes = f.document.querySelectorAll('.mac-only-note');
    const css = f.document.head.textContent;
    assert.equal(notes.length, test.mac ? 0 : f.boxes.length, 'one note per Download box');
    for (const container of f.skipped) {
      assert.equal(container.querySelectorAll('.mac-only-note').length, 0, 'skip nav, header and footer');
    }
    for (const box of f.boxes) {
      assert.equal(box.children.at(-1).className, 'btn btn-primary', 'leave Buy links alone');
    }
    if (test.mac) {
      assert.equal(css, '');
      assert.equal(f.document.documentElement.className, '');
      assert.deepEqual(f.document.listeners, {});
    } else {
      assert.ok(f.document.documentElement.classList.contains('not-mac'));
      assert.ok(css.includes('html.not-mac .phone-link{display:none !important;}'));
      for (const [index, note] of notes.entries()) {
        const siblings = f.main.children;
        assert.equal(siblings.indexOf(note), siblings.indexOf(f.boxes[index]) + (test.phone ? -1 : 1),
          test.phone ? 'note must come before the Download box' : 'desktop note stays after the box');
        assert.equal(note.attributes.role, 'note');
        assert.equal(note.children[0].textContent,
          'Outlier runs on Apple Silicon Macs (macOS 15+). ' + (test.phone ? 'On a phone? ' : 'Not at your Mac? '));
        const button = note.querySelectorAll('button')[0];
        assert.equal(button.className, test.phone ? 'btn btn-primary' : '', 'send button classes');
        assert.equal(button.textContent, 'Send yourself the Mac link' + (test.phone ? '' : '.'));
        assert.equal(button.type, 'button');
      }
      if (test.phone) {
        assert.match(css, /@media\s*\(max-width:760px\)\{\.mac-only-note \.btn\{width:100%;\}\}/,
          'send button fills phone widths');
        assert.ok(!css.includes('.mac-only-note button{'), 'plain button reset must not override primary styling');
      } else {
        assert.ok(css.includes('.mac-only-note button{font:inherit;color:var(--text,inherit);background:none;'));
      }
      const button = notes[0].querySelectorAll('button')[0];
      const send = button.listeners.click.handler;
      const text = 'Outlier for Mac is free to start. Open this on your Mac to download it.';
      let shared;
      const navigator = { ...test.navigator, share: data => { shared = data; return Promise.resolve(); } };
      // A fresh run lets each navigator exercise both send paths without network access.
      const shareFixture = fixture(navigator);
      shareFixture.window.kcCarry = url => url + '&carried=1';
      shareFixture.document.querySelectorAll('button')[0].listeners.click.handler();
      assert.equal(JSON.stringify(shared), JSON.stringify({ title: 'Outlier for Mac', text,
        url: 'https://outlier.host/?utm_source=phone-share&utm_medium=share&carried=1' }));
      send();
      assert.equal(f.location.href, 'mailto:?subject=' + encodeURIComponent('Outlier for Mac: download link') +
        '&body=' + encodeURIComponent(text + '\n\nhttps://outlier.host/?utm_source=phone-share&utm_medium=share'));
      const expectedEvent = { name: 'Send Mac Link', props: { from: 'mac-only-note', platform: test.kind || test.name } };
      assert.equal(JSON.stringify(f.events), JSON.stringify([expectedEvent]));
      assert.equal(JSON.stringify(shareFixture.events), JSON.stringify([expectedEvent]));
      assert.equal(f.document.listeners.click.capture, true);
      const link = f.links[3].link;
      f.document.listeners.click.handler({ target: link.appendChild(new Element('svg')) });
      assert.equal(JSON.stringify(f.events[1]), JSON.stringify({ name: 'Download non-Mac',
        props: { platform: test.kind || test.name, page: '/phone-test/' } }));
    }
    for (const { link, original } of f.links) {
      const expected = { ...original };
      if (test.phone && !link.closest('nav, header, footer')) {
        expected.class = original.class.split(' ').filter(value => value !== 'btn-primary').join(' ');
        if (original.class.split(' ').includes('btn')) expected.class += ' btn-ghost';
      }
      // Includes href with src, target, rel and all unrelated classes.
      assert.deepEqual(link.attributes, expected, 'Download link attributes and classes');
    }
    console.log(`PASS ${test.name}`);
  } catch (error) {
    console.error(`FAIL ${test.name}: ${error.message}`);
    process.exitCode = 1;
  }
}
