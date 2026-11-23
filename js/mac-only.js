/* Outlier runs on Apple Silicon Macs only. 73% of outlier.host visitors are not on a Mac (11-04), so a visitor who is
   clearly NOT on a Mac gets a way to reach their Mac under each Download button. Nothing is blocked: the page reads the
   same and the Download and Buy buttons keep their place and their look.
   - Shown only when the browser is clearly not a Mac: iPhone, iPad (iPadOS says "Macintosh" but has touch points),
     Android, Windows, ChromeOS, Linux. Anything unsure shows nothing, so a Mac visitor never reads "not for you".
   - Phones and tablets (CEO, 23 Nov 2026, under RULES 71): a full-width OUTLINE button right under Download and Buy,
     "Email yourself the Mac download link", then the plain requirement line. Not filled, so it never outranks Buy (21 Nov
     call: a key bought on a phone works on the Mac). It opens a new email with the link in it, addressed to nobody, so the
     visitor sends it to themselves: the site sends no mail, hence "yourself", not "me".
   - Windows, ChromeOS and Linux keep the one plain line with an underlined "Send yourself the Mac link." (share sheet,
     else an email to themselves).
   - Plausible: "Download non-Mac" when such a visitor presses a Download button (props: platform, page), and
     "Send Mac Link" (props: from = phone-button | mac-only-note, platform) when they send the link. Neither carries
     anything personal. The phone funnel is read on 7 Dec (SALES-LEARNINGS). */
(function () {
  var ua = navigator.userAgent || '';
  var plat = (navigator.userAgentData && navigator.userAgentData.platform) || navigator.platform || '';
  var touch = (navigator.maxTouchPoints || 0) > 1;
  var kind = /iPhone|iPod/.test(ua) ? 'iPhone'
    : (/iPad/.test(ua) || (/Macintosh/.test(ua) && touch)) ? 'iPad'
    : /Android/.test(ua) ? 'Android'
    : /CrOS/.test(ua) ? 'ChromeOS'
    : /Win/i.test(plat) || /Windows/.test(ua) ? 'Windows'
    : /Linux/i.test(plat) || /Linux|X11/.test(ua) ? 'Linux'
    : null;
  if (!kind) return;                                   // a Mac, or not sure: show nothing
  var phone = kind === 'iPhone' || kind === 'iPad' || kind === 'Android';
  var links = document.querySelectorAll('a[href$=".dmg"]');
  if (!links.length) return;

  var TEXT = 'Outlier for Mac is free to start. Open this on your Mac to download it.';
  var SUBJECT = 'Outlier for Mac: download link';
  function track(name, props) {
    if (window.plausible) { try { window.plausible(name, { props: props }); } catch (e) {} }
  }
  function macUrl() {
    var url = 'https://outlier.host/?utm_source=phone-share&utm_medium=share';
    if (typeof window.kcCarry === 'function') { try { url = window.kcCarry(url); } catch (e) {} }
    return url;
  }
  function mailto(url) {
    location.href = 'mailto:?subject=' + encodeURIComponent(SUBJECT) + '&body=' + encodeURIComponent(TEXT + '\n\n' + url);
  }
  function emailLink() {                               // the phone button says "Email", so it always opens an email
    track('Send Mac Link', { from: 'phone-button', platform: kind });
    mailto(macUrl());
  }
  function sendLink() {
    var url = macUrl();
    track('Send Mac Link', { from: 'mac-only-note', platform: kind });
    if (navigator.share) {
      navigator.share({ title: 'Outlier for Mac', text: TEXT, url: url }).catch(function () {});
    } else {
      mailto(url);
    }
  }

  var css = document.createElement('style');
  css.textContent =
    '.mac-only-note{margin:.6rem 0 0;font-size:.9rem;line-height:1.45;color:var(--text-mid,#5b5b66);}' +
    '.mac-only-note .mac-link-line{font:inherit;color:var(--text,inherit);background:none;border:0;padding:0;' +
    'text-decoration:underline;text-underline-offset:2px;cursor:pointer;}' +
    // The phone button: full width and outlined in the page's own text colour, so it reads as a button on light and dark
    // pages alike; 44 px tall (Apple's minimum tap target). As a flex item (the home hero's .cta-bar) it takes a row.
    // The outline is the text colour at 45% (a full-strength white line out-shouted Buy Pro's faint border at 375 on
    // the dark home, 23 Nov); a browser without color-mix() keeps the full-strength line declared first.
    '.mac-only-phone{flex:1 0 100%;width:100%;margin:.75rem 0 0;}' +
    '.mac-only-phone .mac-link-btn{display:block;width:100%;min-height:44px;margin:0;padding:.65rem 1rem;' +
    'font:inherit;font-size:.95rem;font-weight:600;line-height:1.3;text-align:center;color:var(--text,inherit);' +
    'background:transparent;border:1.5px solid currentColor;border-color:color-mix(in srgb,currentColor 45%,transparent);' +
    'border-radius:10px;cursor:pointer;}' +
    '.mac-only-phone .mac-link-btn:focus-visible{outline:2px solid currentColor;outline-offset:2px;}' +
    '.mac-only-phone .mac-only-req{display:block;margin:.45rem 0 0;font-size:.85rem;}' +
    'html.not-mac .phone-link{display:none !important;}';           // the pages' own phone line: one way, not two
  document.head.appendChild(css);
  document.documentElement.classList.add('not-mac');

  // Where the note goes, so it sits right under Download and Buy (23 Nov; before, it went after the nearest <div>, which
  // for an article's lone a.cta is the whole page wrapper, so the note landed below everything):
  // - the Download link sits in a row of buttons (.cta-row, p.pbox-btns, a list item): after that row (a list: after it);
  // - otherwise (a card like div.cta or div.cta-band, a tier, a page wrapper): inside it, right after the last link that
  //   follows Download with nothing between (Buy), or after Download itself.
  var ROWS = ['.cta-row', '.pbox-btns', 'p', 'li'];
  function anchorOf(a) {
    var p = a.parentNode;
    if (p && p.matches && ROWS.some(function (s) { return p.matches(s); })) return p.matches('li') ? p.parentNode : p;
    var last = a;
    while (last.nextElementSibling && /^a$/i.test(last.nextElementSibling.tagName)) last = last.nextElementSibling;
    return last;
  }

  var done = [];
  Array.prototype.forEach.call(links, function (a) {
    if (a.closest('nav, header, footer')) return;     // a note in the nav or footer would break their layout
    var box = anchorOf(a);
    if (!box || !box.parentNode || done.indexOf(box) !== -1) return;
    done.push(box);
    var note = document.createElement('p');
    note.setAttribute('role', 'note');
    var b = document.createElement('button');
    b.type = 'button';
    if (phone) {
      note.className = 'mac-only-note mac-only-phone';
      b.className = 'mac-link-btn';
      b.setAttribute('data-kc-cta', '');               // the shared "Ask a question" pill steps aside from it
      b.textContent = 'Email yourself the Mac download link';
      b.addEventListener('click', emailLink);
      note.appendChild(b);
      var req = document.createElement('span');
      req.className = 'mac-only-req';
      req.textContent = 'Outlier runs on Apple Silicon Macs (macOS 15+).';
      note.appendChild(req);
    } else {
      note.className = 'mac-only-note';
      note.appendChild(document.createTextNode('Outlier runs on Apple Silicon Macs (macOS 15+). Not at your Mac? '));
      b.className = 'mac-link-line';
      b.textContent = 'Send yourself the Mac link.';
      b.addEventListener('click', sendLink);
      note.appendChild(b);
    }
    box.parentNode.insertBefore(note, box.nextSibling);
  });

  document.addEventListener('click', function (e) {
    var a = e.target && e.target.closest ? e.target.closest('a[href$=".dmg"]') : null;
    if (a) track('Download non-Mac', { platform: kind, page: location.pathname });
  }, true);
})();
