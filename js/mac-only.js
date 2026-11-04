/* Outlier runs on Apple Silicon Macs only. 73% of outlier.host visitors are not on a Mac (11-04), so a visitor who is
   clearly NOT on a Mac sees one plain line under each Download button, with a button that sends the Mac link to
   themselves (share sheet, or an email to themselves). Nothing is blocked: the page reads the same and the Download
   button still works.
   - Shown only when the browser is clearly not a Mac: iPhone, iPad (iPadOS says "Macintosh" but has touch points),
     Android, Windows, ChromeOS, Linux. Anything unsure shows nothing, so a Mac visitor never reads "not for you".
   - Plausible: "Download non-Mac" when such a visitor presses a Download button (props: platform, page), and
     "Send Mac Link" (props: from, platform) when they send the link. Neither carries anything personal. */
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

  function track(name, props) {
    if (window.plausible) { try { window.plausible(name, { props: props }); } catch (e) {} }
  }
  function sendLink() {
    var url = 'https://outlier.host/?utm_source=phone-share&utm_medium=share';
    if (typeof window.kcCarry === 'function') { try { url = window.kcCarry(url); } catch (e) {} }
    var text = 'Outlier for Mac is free to start. Open this on your Mac to download it.';
    track('Send Mac Link', { from: 'mac-only-note', platform: kind });
    if (navigator.share) {
      navigator.share({ title: 'Outlier for Mac', text: text, url: url }).catch(function () {});
    } else {
      location.href = 'mailto:?subject=' + encodeURIComponent('Outlier for Mac: download link') +
        '&body=' + encodeURIComponent(text + '\n\n' + url);
    }
  }

  var css = document.createElement('style');
  css.textContent =
    '.mac-only-note{margin:.6rem 0 0;font-size:.9rem;line-height:1.45;color:var(--text-mid,#5b5b66);}' +
    '.mac-only-note button{font:inherit;color:var(--text,inherit);background:none;border:0;padding:0;' +
    'text-decoration:underline;text-underline-offset:2px;cursor:pointer;}' +
    'html.not-mac .phone-link{display:none !important;}';           // the home page's own phone line: one line, not two
  document.head.appendChild(css);
  document.documentElement.classList.add('not-mac');

  var done = [];
  Array.prototype.forEach.call(links, function (a) {
    if (a.closest('nav, header, footer')) return;     // a paragraph in the nav or footer would break their layout
    var box = a.closest('.cta-bar, .pbox-btns, p, ul, ol, div') || a.parentNode;   // a list item's note goes after its list
    if (!box || done.indexOf(box) !== -1) return;
    done.push(box);
    var note = document.createElement('p');
    note.className = 'mac-only-note';
    note.setAttribute('role', 'note');
    note.appendChild(document.createTextNode('Outlier runs on Apple Silicon Macs (macOS 15+). ' +
      (phone ? 'On a phone? ' : 'Not at your Mac? ')));
    var b = document.createElement('button');
    b.type = 'button';
    b.textContent = 'Send yourself the Mac link.';
    b.addEventListener('click', sendLink);
    note.appendChild(b);
    box.parentNode.insertBefore(note, box.nextSibling);
  });

  document.addEventListener('click', function (e) {
    var a = e.target && e.target.closest ? e.target.closest('a[href$=".dmg"]') : null;
    if (a) track('Download non-Mac', { platform: kind, page: location.pathname });
  }, true);
})();
