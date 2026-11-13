#!/usr/bin/env python3
"""The sale price switches off at the moment the offer ends, and nothing may show it after.

WHY. Matthew's 2026-11-13 order sets Outlier to $16.99, the bundle to $34.99, and the deadline in
data/founding_offer.json. Dodo refuses an expired code, so a page that still shows the sale price after
that moment offers a price nobody can get, to exactly the person who was ready to buy. A switch that waits
for someone to remember the date is how that would happen, so the pages carry the date themselves:

  * every page that loads the shared offer bar (founding.js, served by the lead worker) has a dated guard
    right before it. From the end date on, the guard sets window.__kcFounding, the bar's own run-once flag,
    so the bar never mounts;
  * the product boxes' founders-price spans are `hidden` in the HTML and their reveal script shows them
    only before the end date AND while the worker reports seats left;
  * the home page's Lifetime card says $29 in the HTML itself. Its script applies the sale price only
    before the end date and while seats are left, so a visitor without JavaScript, and every crawler that
    reads raw HTML, gets the regular price.

Every date in a page is a literal and every one must equal "ends" in data/founding_offer.json.

WHAT FAILS
  always   a page loads founding.js without the dated guard right before it; a guard, a reveal script or
           the home card's script carries no end date or a different one; founding-price text a visitor
           reads in the raw HTML outside hidden elements and scripts. The paid JSON-LD Offer must carry
           the exact sale price and priceValidUntil. Mounts must name the real November reference.
           A text file (llms.txt) may state the offer only on a line that names the end date.
  over     once the end date has passed, or with --live once the worker reports no seats left: ANY
           founding-offer markup left in a served file, hidden or not (the codes, the offer prices, the
           bar and its guard, the reveal spans, "founders price", "founding seats"). The switch keeps
           visitors safe at the moment itself; this makes the leftovers go. The hourly scheduled run
           checks the date with nobody pushing, so it goes red within the first hour after the offer ends
           if anything is left.

    python3 scripts/founding_offer_gate.py [root] [--live] [--now 2026-11-25T02:00:00Z]
    python3 scripts/founding_offer_gate.py --self-check
"""
from __future__ import annotations

import datetime as dt
import html.parser
import json
import pathlib
import re
import sys
import tempfile
import urllib.request

#: fewer pages than this means the scan broke, not that the site shrank (meta_gate probes an empty tree)
MIN_PAGES = 50
BAR = re.compile(r'<script\b[^>]*\bsrc="https://kerr-lead-agent\.kerrco\.workers\.dev/founding\.js"[^>]*>\s*</script>')
GUARD = re.compile(r'<script data-founding-ends="([^"]*)">(.*?)</script>\s*$', re.S)
PBOX_SCRIPT = re.compile(r"<script data-pbox-script>(.*?)</script>", re.S)
SCRIPT = re.compile(r"<script\b[^>]*>(.*?)</script>", re.S)
DATE_LIT = re.compile(r'Date\.parse\("([^"]+)"\)')
#: code, not pages: the gates and generators name the codes on purpose
SKIP_DIRS = {".git", ".github", "scripts", "node_modules"}
SERVED = {".html", ".htm", ".txt", ".xml", ".json", ".md"}
#: records, not pages: the offer file itself, and Dodo's product record (sync_product_facts.py), whose product name stays
#: "Outlier — Founders Lifetime" until the product is renamed in Dodo (the receipt's name; Matthew's account change)
NOT_PAGES = {"data/founding_offer.json", "data/product-facts.json"}
UA = {"User-Agent": "kerr-ops/1.0 (founding_offer_gate)"}

# 2026-11-13, Matthew's order: the paid November price is the only sale reference.
SALE_END = "2026-12-03T07:59:00Z"
SALE_LINE = "Black Friday sale: $16.99 once, 31% off our November price of $24.50, through December 2. Then $29."
BUNDLE_LINE = "Black Friday sale: $34.99 once, 29% off our November price of $49.50, through December 2. Then $59."
MOUNT = re.compile(r'<div\b[^>]*\bdata-founding(?=[\s>])[^>]*>')


#: 10-21 (CEO): until the product is renamed in Dodo a $249 buyer's receipt still says "Founders Lifetime", so the pricing
#: and thank-you pages say so, inside <span data-receipt-name>. That span may name the receipt's product only while Dodo's
#: record (data/product-facts.json, synced from Dodo) still carries that name; once it is renamed, the note fails.
RECEIPT = re.compile(r"<span data-receipt-name>([^<]*)</span>")


def load(root: pathlib.Path) -> dict:
    d = json.loads((root / "data" / "founding_offer.json").read_text(encoding="utf-8"))
    d["_end"] = dt.datetime.fromisoformat(d["ends"].replace("Z", "+00:00"))
    try:
        d["_receipt"] = json.loads((root / "data" / "product-facts.json").read_text(encoding="utf-8")).get("product_name") or ""
    except (OSError, ValueError):
        d["_receipt"] = ""
    return d


def receipt_notes(rel: str, src: str, offer: dict) -> tuple[str, list[str]]:
    """The page with each receipt-name note that matches Dodo's product name taken out, and a failure for each that
    does not (the receipt no longer says it, or the note names something else)."""
    bad = []

    def keep_or_flag(m):
        name = html.unescape(m.group(1)).strip().strip("“”\"'")
        if name and name in offer["_receipt"]:
            return ""
        bad.append(f"{rel}: a receipt note names {name!r}, but Dodo's product is {offer['_receipt']!r}")
        return m.group(0)
    return RECEIPT.sub(keep_or_flag, src), bad


def price_patterns(offer: dict) -> list[re.Pattern]:
    """What the founding offer looks like in text: the founders price, the codes, the offer's own figures, and the
    founders' product name. 10-21 (CEO): the product is the "Outlier Lifetime Licence"; "Founders Lifetime" only fits
    while the founders price exists, so the page names it only beside that price (the home card's dated script)."""
    pats = [re.compile(r"\bfounders?['’]?\s+prices?\b", re.I), re.compile(r"\bfounding\s+prices?\b", re.I),
            re.compile(r"\bfirst\s+\d+\s+buyers\b", re.I), re.compile(r"\bFounders\s+Lifetime\b", re.I)]
    for o in offer["offers"]:
        pats.append(re.compile(r"\b" + re.escape(o["code"]) + r"\b"))
        pats += [re.compile(re.escape(p) + r"(?![\d])") for p in o.get("prices", [])]
    return pats


def leftover_patterns(offer: dict) -> list[re.Pattern]:
    """Once the offer is over, none of this may be left in a served file, hidden or not."""
    return price_patterns(offer) + [
        re.compile(r"kerr-lead-agent\.kerrco\.workers\.dev/founding"),   # the bar, and the seat reads
        re.compile(r"\bdata-pbox-founding\b"), re.compile(r"\bdata-founding\b"), re.compile(r"data-founding-ends"),
        re.compile(r"\bfounding\s+(?:seats?|offer)\b", re.I),
    ]


class Visible(html.parser.HTMLParser):
    """The text a visitor reads in the raw HTML: not inside a script/style/template/noscript, not inside an element
    carrying the hidden attribute. JSON-LD is kept: search engines and answer engines read it as the page's claims."""
    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
    SKIP = {"script", "style", "template", "noscript"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack: list[tuple[str, bool]] = []
        self.out: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in self.VOID:
            return
        a = dict(attrs)
        ld = tag == "script" and (a.get("type") or "").lower() == "application/ld+json"
        self.stack.append((tag, "hidden" in a or (tag in self.SKIP and not ld)))

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                return

    def handle_data(self, data):
        if not any(off for _, off in self.stack):
            self.out.append(data)


def visible_text(src: str) -> str:
    p = Visible()
    p.feed(src)
    p.close()
    return " ".join(p.out)


def sale_visible_text(rel: str, src: str) -> str:
    """Otter's own monthly price shares the sale figure; keep its named exemption narrow."""
    if rel == "vs/otter-ai-alternative-local/index.html":
        src = src.replace("Pro $16.99/user/month billed monthly", "Otter Pro monthly price")
    return visible_text(src)


def buyer_copy(rel: str, src: str, over: bool = False) -> list[str]:
    """Matthew's 2026-11-13 order also covers hidden sale copy and accessibility text."""
    if rel == "terms.html":
        note = ('<p class="updated">Changed 2026-11-04: "lifetime" means the same for every Outlier lifetime licence, '
                'the current $49 licence and the earlier Founding 200 and Founders 500 tiers: the lifetime of the '
                'Outlier product, with 90 days\' notice and a final binary release if it is ever sunset.</p>')
        src = src.replace(note, '')
    # 2026-11-13 (Claude review): terms.html's legal text naming the earlier licence tiers keeps the old names on
    # purpose: legal wording is Matthew's call (his to-do item 186), never a sale edit. Taken out here BY EXACT TEXT, so
    # any other mention still fails. (The thank-you receipt note that was also exempt here is gone: the CEO renamed the
    # Dodo product to "Outlier — Lifetime Licence" on 13 Nov, so receipts no longer say Founders.)
    if rel == "terms.html":
        for legal in ('and the earlier Founding 200 and Founders 500 tiers alike, lifetime means',
                      'Your tier (Founding 200, Founders 500, Pro) is derived from'):
            src = src.replace(legal, "")
    if rel == "vs/unified-memory-vs-vram/index.html":
        src = src.replace("DGX Spark's Founders Edition", "DGX Spark's NVIDIA edition")
    class Buyer(Visible):
        def handle_starttag(self, tag, attrs):
            super().handle_starttag(tag, attrs)
            for key, value in attrs:
                if key in {"alt", "title", "aria-label", "aria-description", "content"}:
                    self.out.append(value or "")

        def handle_data(self, data):
            # Hidden spans will be shown by the reveal; inspect them too.
            if not any(tag in self.SKIP and tag != "noscript" and off for tag, off in self.stack):
                if any(tag == "script" for tag, _ in self.stack):
                    def strings(v):
                        if isinstance(v, str):
                            self.out.append(v)
                        elif isinstance(v, dict):
                            for child in v.values():
                                strings(child)
                        elif isinstance(v, list):
                            for child in v:
                                strings(child)
                    try:
                        strings(json.loads(data))
                    except ValueError:
                        self.out.append(data)
                else:
                    self.out.append(data)
    p = Buyer()
    p.feed(src)
    p.close()
    bad = []
    if re.search(r"founding|founders", " ".join(p.out), re.I):
        bad.append(f"{rel}: buyer copy still names the old offer")
    allowed = {SALE_LINE.rstrip('.'), BUNDLE_LINE.rstrip('.'),
               "$16.99 once in the Black Friday sale",
               "$16.99 once in the Black Friday sale, $29 from December 3",
               "in the Black Friday sale"}
    for span in re.findall(r'<span data-pbox-founding hidden>(.*?)</span>', src, re.S):
        text = html.unescape(span).strip().lstrip('·. ').rstrip('. ')
        other_app = rel == "thank-you.html" and text in {
            "Launch price: $14.50 once, through November 30. From December 1: $29",
            "Launch price: $29.50 once, through November 30. From December 1: $59"}
        if text not in allowed and not other_app:
            bad.append(f"{rel}: sale span differs from Matthew's exact sale wording")
    # A December price is never a former price. Keep these bans even during a real sale.
    for text in re.findall(r'<(?:span|div)[^>]*(?:data-pbox-founding|data-lt-offer)[^>]*>(.*?)</(?:span|div)>', src, re.S):
        if re.search(r"half price|50% off|save\s+\$|\bwas\s+\$|countdown", text, re.I):
            bad.append(f"{rel}: prohibited discount claim in offer copy")
    for text in re.findall(r'<div[^>]*data-lt-offer[^>]*>(.*?)</div>', src, re.S):
        if html.unescape(re.sub(r'<[^>]+>', '', text)).strip() != SALE_LINE + " The Buy button applies the discount for you at checkout.":
            bad.append(f"{rel}: card offer differs from Matthew's exact sale wording")
    for raw in re.findall(r'<script type="application/ld\+json">(.*?)</script>', src, re.S):
        try:
            value = json.loads(raw)
        except ValueError:
            if rel == "_seo_build/templates/_base.html" and raw in {"{{ breadcrumb_jsonld | safe }}", "{{ article_jsonld | safe }}"}:
                continue
            bad.append(f"{rel}: unreadable JSON-LD")
            continue
        def walk(v):
            if isinstance(v, dict):
                if v.get("@type") == "Offer" and v.get("name") == "Outlier Lifetime Licence":
                    expected = ("29", None, "USD") if over else ("16.99", "2026-12-02", "USD")
                    if (v.get("price"), v.get("priceValidUntil"), v.get("priceCurrency")) != expected:
                        bad.append(f"{rel}: paid Offer price, validity and currency must be {expected}")
                for child in v.values():
                    walk(child)
            elif isinstance(v, list):
                for child in v:
                    walk(child)
        walk(value)
    return bad


def served_files(root: pathlib.Path):
    for p in sorted(root.rglob("*")):
        rel = p.relative_to(root)
        if p.is_file() and p.suffix.lower() in SERVED and not (set(rel.parts) & SKIP_DIRS) \
                and rel.as_posix() not in NOT_PAGES:
            yield rel, p.read_text(encoding="utf-8", errors="ignore")


def wiring(rel: str, src: str, ends: str) -> list[str]:
    bad = []
    mounts = MOUNT.findall(src)
    if len(mounts) != len(BAR.findall(src)):
        bad.append(f"{rel}: each shared offer script needs one sale mount")
    for mount in mounts:
        parser = html.parser.HTMLParser()
        attrs = {}
        parser.handle_starttag = lambda tag, pairs: attrs.update(pairs)
        parser.feed(mount)
        if any(attrs.get(k) != v for k, v in
               {"data-ref": "$24.50", "data-now": "$16.99", "data-was": "$29"}.items()):
            bad.append(f"{rel}: sale mount must name data-ref=$24.50, data-now=$16.99, data-was=$29")
    for m in BAR.finditer(src):
        g = GUARD.search(src[:m.start()])
        if not g:
            bad.append(f"{rel}: loads founding.js with no dated guard right before it")
        elif g.group(1) != ends or DATE_LIT.findall(g.group(2)) != [ends] or "window.__kcFounding=1" not in g.group(2):
            bad.append(f"{rel}: the bar's guard ends {g.group(1)!r} / {DATE_LIT.findall(g.group(2))}, not {ends!r}")
    if "data-pbox-founding" in src:
        blocks = PBOX_SCRIPT.findall(src)
        if not blocks:
            bad.append(f"{rel}: founders-price spans with no reveal script")
        for b in blocks:
            if DATE_LIT.findall(b) != [ends] or "if(!(now<end))return;" not in b or b.find("now<end") > b.find("fetch("):
                bad.append(f"{rel}: the founders-price reveal is not dated {ends} before it asks the worker")
    for b in SCRIPT.findall(src):
        if "[data-lifetime-card]" in b and DATE_LIT.findall(b) != [ends]:
            bad.append(f"{rel}: the Lifetime card's script is not dated {ends}")
    return bad


def seats_left(offer: dict) -> bool:
    req = urllib.request.Request(offer["worker"], headers=UA)
    with urllib.request.urlopen(req, timeout=20) as r:
        d = json.loads(r.read().decode())
    if not isinstance(d.get("left"), int):
        raise ValueError(f"the worker's answer has no seat count: {d}")
    print(f"worker: {d.get('code')} left={d['left']} of={d.get('of')} soldOut={d.get('soldOut')}")
    return d["left"] > 0 and not d.get("soldOut")


def check(root: pathlib.Path, now: dt.datetime, live: bool) -> int:
    files = list(served_files(root))
    pages = [f for f in files if f[0].suffix.lower() in (".html", ".htm")]
    print(f"founding_offer_gate: examined {len(pages)} page(s), {len(files)} served file(s)")
    if len(pages) < MIN_PAGES or not (root / "index.html").is_file():
        print(f"FAIL: {len(pages)} page(s) is fewer than {MIN_PAGES}, or there is no index.html. The scan is "
              f"likelier broken than the site. Not reporting clean.")
        return 1
    try:
        offer = load(root)
    except (OSError, ValueError, KeyError) as e:
        print(f"FAIL: data/founding_offer.json is missing or unreadable ({e}). It is the one source for the end date.")
        return 1
    ends = offer["ends"]
    if (ends != SALE_END or [(o.get("what"), o.get("prices")) for o in offer["offers"]]
            != [(SALE_LINE, ["$16.99"]), (BUNDLE_LINE, ["$34.99"])]):
        print("FAIL: offer data differs from Matthew's 2026-11-13 sale order")
        return 1
    over, why = now >= offer["_end"], f"the end date {ends} has passed"
    if live and not over:
        try:
            if not seats_left(offer):
                over, why = True, "the worker reports no founding seats left"
        except Exception as e:   # noqa: BLE001 — any failure to read is a failure to know
            print(f"FAIL: could not read the founding worker ({e}). Whether seats are left is unknown, not 'yes'.")
            return 1
    bad: list[str] = []
    for rel, src in files:
        if rel.suffix.lower() in (".html", ".htm"):
            bad += buyer_copy(rel.as_posix(), src, over=over)
        elif rel.as_posix() in {"llms.txt", "llms-full.txt"} and re.search(r"founding|founders", src, re.I):
            bad.append(f"{rel}: buyer text still names the old offer")
    if over:
        print(f"the founding offer is OVER: {why}")
        for rel, src in files:
            src, flagged = receipt_notes(rel.as_posix(), src, offer)
            bad += flagged
            hits = sorted({m.group(0) for p in leftover_patterns(offer) for m in p.finditer(src)})
            if hits:
                bad.append(f"{rel}: still carries {', '.join(hits[:6])}")
    else:
        print(f"the founding offer is on until {ends}; checking the switch is wired and nothing static shows the price")
        pats, day = price_patterns(offer), ends[:10]
        for rel, src in files:
            src, flagged = receipt_notes(rel.as_posix(), src, offer)
            bad += flagged
            if rel.suffix.lower() in (".html", ".htm"):
                bad += wiring(rel.as_posix(), src, ends)
                hits = sorted({m.group(0) for p in pats for m in p.finditer(sale_visible_text(rel.as_posix(), src))})
                if hits:
                    bad.append(f"{rel}: shows {', '.join(hits)} in the HTML itself; reveal it from a dated script instead")
            else:
                for n, line in enumerate(src.split("\n"), 1):
                    hits = sorted({m.group(0) for p in pats for m in p.finditer(line)})
                    if hits and day not in line:
                        bad.append(f"{rel}:{n}: states {', '.join(hits)} on a line that does not name the end date {day}")
    if bad:
        print(f"\nFAIL ({len(bad)}):")
        for b in bad[:60]:
            print(f"  {b}")
        if len(bad) > 60:
            print(f"  … and {len(bad) - 60} more")
        if over:
            print("\nTake the founding offer off: the bar and its guard, the reveal spans and script, the card's founders "
                  "branch, and the llms.txt line; then any prose that still promises founding seats.")
        return 1
    print("PASS: " + ("nothing founding is left" if over else f"the switch is wired to {ends} and nothing static shows the price"))
    return 0


def self_check() -> int:
    """The gate must fail on each way the switch can be missing, and pass on a wired page and a clean one."""
    ends = SALE_END
    guard = (f'<script data-founding-ends="{ends}">(function(){{var end=Date.parse("{ends}"),now=Date.now();'
             f'if(!(now<end))window.__kcFounding=1;}})();</script>\n')
    mount = '<div data-founding data-ref="$24.50" data-now="$16.99" data-was="$29" hidden></div>\n'
    bar = '<script src="https://kerr-lead-agent.kerrco.workers.dev/founding.js" defer></script>\n'
    reveal = ('<script data-pbox-script>(function(){var m=1;var end=Date.parse("%s"),now=Date.now();'
              'if(!(now<end))return;fetch("x")})();</script>\n')
    span = '<p>$29<span data-pbox-founding hidden>' + SALE_LINE + '</span></p>\n'
    card = ('<div data-lifetime-card>$249</div><script>var c=document.querySelector("[data-lifetime-card]");'
            'var end=Date.parse("%s");</script>\n')
    offer = json.dumps({"ends": ends, "worker": "http://127.0.0.1:9/", "offers": [
        {"code": "FOUNDINGOUTLIER", "what": SALE_LINE, "prices": ["$16.99"]},
        {"code": "FOUNDINGBUNDLE", "what": BUNDLE_LINE, "prices": ["$34.99"]}]})
    before, after = dt.datetime(2026, 11, 1, tzinfo=dt.timezone.utc), dt.datetime(2026, 12, 3, 8, tzinfo=dt.timezone.utc)
    wired = mount + guard + bar + span + reveal % ends
    clean = "<p>Pro Lifetime: $249 once.</p>\n"
    cases = [  # (name, home page, other page, llms line, when, expected exit)
        ("wired, before the end", wired + card % ends, wired, f"{SALE_LINE} until {ends[:10]}", before, 0),
        ("bar with no guard", bar + card % ends, wired, "", before, 1),
        ("guard with another date", mount + guard.replace(ends, "2026-12-01T00:00:00Z") + bar + card % ends, wired, "", before, 1),
        ("reveal with no date", wired + card % ends, mount + guard + bar + span + reveal.replace('if(!(now<end))return;', '') % ends, "", before, 1),
        ("card script not dated", wired + card % "2027-01-01T00:00:00Z", wired, "", before, 1),
        ("visible founders price", wired + card % ends + "<p>Buy for $16.99</p>", wired, "", before, 1),
        ("visible code in JSON-LD", wired + card % ends + '<script type="application/ld+json">{"d":"FOUNDINGOUTLIER"}</script>', wired, "", before, 1),
        ("undated llms line", wired + card % ends, wired, "the first 25 buyers pay $16.99", before, 1),
        ("bundle price shown", wired + card % ends + "<p>All three for $34.99</p>", wired, "", before, 1),
        ("founders' product name in prose", wired + card % ends, wired + "<p>Pro is a one-time Founders Lifetime at $249.</p>", "", before, 1),
        ("leftovers after the end", wired + card % ends, wired, f"{SALE_LINE} until {ends[:10]}", after, 1),
        ("hidden span left after the end", clean, clean + span, "", after, 1),
        ("clean after the end", clean, clean, "Pro Lifetime: $249 once.", after, 0),
    ]
    cases += [
        ("missing data-ref", wired.replace(' data-ref="$24.50"', '') + card % ends, wired, "", before, 1),
        ("wrong reference", wired.replace('data-ref="$24.50"', 'data-ref="$29"') + card % ends, wired, "", before, 1),
        ("old launch price", wired.replace('data-now="$16.99"', 'data-now="$24.50"') + card % ends, wired, "", before, 1),
        ("missing mount", wired.replace(mount, '') + card % ends, wired, "", before, 1),
        ("dated paid schema", wired + card % ends + '<script type="application/ld+json">{"@type":"Offer","name":"Outlier Lifetime Licence","price":"16.99","priceCurrency":"USD","priceValidUntil":"2026-12-02"}</script>', wired, "", before, 0),
        ("undated paid schema", wired + card % ends + '<script type="application/ld+json">{"@type":"Offer","name":"Outlier Lifetime Licence","price":"16.99","priceCurrency":"USD"}</script>', wired, "", before, 1),
    ]
    cases += [  # 2026-11-13, Matthew's order: buyer fields and false discounts stay guarded.
        ("hidden old tier", wired + '<span hidden>Founders Lifetime</span>', wired, "", before, 1),
        ("old tier in alt", wired + '<img alt="FOUNDING sale">', wired, "", before, 1),
        ("old tier in meta", wired + '<meta name="description" content="Founders offer">', wired, "", before, 1),
        ("old tier in aria", wired + '<button aria-label="Founding sale">Buy</button>', wired, "", before, 1),
        ("old launch wording", wired.replace(SALE_LINE, 'Launch price: $24.50 once, through November 30. From December 1: $29.'), wired, "", before, 1),
        ("wrong discount", wired.replace('31% off', '50% off'), wired, "", before, 1),
        ("wrong former price", wired.replace('price of $24.50', 'price of $29'), wired, "", before, 1),
        ("false savings", wired.replace(SALE_LINE, 'Save $12 against December prices'), wired, "", before, 1),
        ("half price", wired.replace(SALE_LINE, 'Half price'), wired, "", before, 1),
        ("countdown", wired.replace(SALE_LINE, 'Sale countdown'), wired, "", before, 1),
        ("wrong paid schema", wired + '<script type="application/ld+json">{"@type":"Offer","name":"Outlier Lifetime Licence","price":"24.50","priceCurrency":"USD","priceValidUntil":"2026-12-02"}</script>', wired, "", before, 1),
        ("regular paid schema after end", clean + '<script type="application/ld+json">{"@type":"Offer","name":"Outlier Lifetime Licence","price":"29","priceCurrency":"USD"}</script>', clean, "", after, 0),
        ("sale paid schema after end", clean + '<script type="application/ld+json">{"@type":"Offer","name":"Outlier Lifetime Licence","price":"16.99","priceCurrency":"USD","priceValidUntil":"2026-12-02"}</script>', clean, "", after, 1),
    ]
    wrong = []
    note = '<p>Your receipt may say <span data-receipt-name>&ldquo;Founders Lifetime&rdquo;</span>: the same licence.</p>'
    cases += [  # 2026-11-13, Matthew's order: old receipt wording fails even before Dodo renames it
        # 2026-11-13: Dodo renamed the product and Matthew's order bans the old tier in buyer copy, so a "Founders" receipt
        # note now fails even where a stale fact file still carries the old name.
        ("receipt note, Dodo still says it", wired + card % ends + note, wired, "", before, 1),
        ("receipt note after the end, Dodo still says it", clean + note, clean, "", after, 1),
        ("receipt note after Dodo renamed it", clean + note, clean, "", after, 1, "Outlier — Lifetime Licence"),
    ]
    for name, home, other, llms, when, want, *rn in cases:
        receipt_name = rn[0] if rn else "Outlier — Founders Lifetime"
        with tempfile.TemporaryDirectory() as t:
            r = pathlib.Path(t)
            (r / "data").mkdir()
            (r / "data" / "founding_offer.json").write_text(offer)
            (r / "data" / "product-facts.json").write_text(json.dumps({"product_name": receipt_name}))
            (r / "index.html").write_text(home)
            (r / "llms.txt").write_text(llms + "\n")
            for i in range(MIN_PAGES):
                (r / f"p{i}.html").write_text(other)
            import contextlib, io
            with contextlib.redirect_stdout(io.StringIO()):
                got = check(r, when, live=False)
        print(f"  {'ok ' if got == want else 'BAD'} {name}: exit {got} (want {want})")
        if got != want:
            wrong.append(name)
    if wrong:
        print(f"SELF-CHECK FAILED: {wrong}")
        return 1
    print(f"self-check: {len(cases)} cases, the gate fails on every missing switch and passes the wired and clean trees")
    return 0


def main(argv: list[str]) -> int:
    if "--self-check" in argv:
        return self_check()
    now = dt.datetime.now(dt.timezone.utc)
    if "--now" in argv:
        now = dt.datetime.fromisoformat(argv[argv.index("--now") + 1].replace("Z", "+00:00"))
    args = [a for i, a in enumerate(argv) if not a.startswith("--") and (i == 0 or argv[i - 1] != "--now")]
    return check(pathlib.Path(args[0] if args else "."), now, live="--live" in argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
