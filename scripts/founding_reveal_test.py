#!/usr/bin/env python3
"""Run both founding reveals in node with a fake clock, fetch and timers.

    python3 scripts/founding_reveal_test.py        # exit 0 = every case as expected
"""
import ast, html, json, pathlib, re, runpy, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
home = (ROOT / "index.html").read_text(encoding="utf-8")
PBOX = re.compile(r"<script data-pbox-script>(.*?)</script>", re.S)
script = PBOX.search(home).group(1)
card_script = next(s for s in re.findall(r"<script\b[^>]*>(.*?)</script>", home, re.S)
                   if "[data-lifetime-card]" in s)
end = json.loads((ROOT / "data/founding_offer.json").read_text())["ends"]
regular = {}
for key in ("name", "price", "bnpl", "offer", "btn"):
    node = re.search(r"<([a-z]+)\b([^>]*\bdata-lt-" + key + r"\b[^>]*)>(.*?)</\1>", home, re.S)
    regular[key] = (bool(re.search(r"\bhidden\b", node.group(2))) if key == "offer" else
                    node.group(3) if key == "bnpl" else html.unescape(re.sub(r"<[^>]*>", "", node.group(3))))
# 2026-11-11 (CEO): the regular Pro price from December 1 is $29 once.
assert regular["price"] == "$29"

# 2026-11-13, Matthew's order: regeneration and no-JavaScript fallbacks must agree.
generator = runpy.run_path(str(ROOT / "scripts/product_box.py"))
sale_line = "Black Friday sale: $16.99 once, 31% off our November price of $24.50, through December 2. Then $29"
assert generator["launch_line"]() == sale_line
assert generator["founding_next_day"]() == "December 3"
for output in (generator["box"]("sale-test", "answer", "1.11.1006"),
               generator["end_box"]("sale-test", "1.11.1006"),
               generator["STD_PRICE_NEW"], generator["HOME_NEW"]):
    assert sale_line in output
    assert "<span data-pbox-regular>" in output and "$29 once" in output
assert regular["btn"] == "Buy Outlier Lifetime Licence: $29" and regular["offer"]
schema = [json.loads(s) for s in re.findall(r'<script type="application/ld\+json">(.*?)</script>', home, re.S)]
app = next(v for v in schema if v.get("@type") == "SoftwareApplication")
assert len(app["offers"]) == 2
free, paid = app["offers"]
assert free["price"] == "0" and "priceValidUntil" not in free
assert (paid["name"], paid["price"], paid["priceValidUntil"]) == ("Outlier Lifetime Licence", "16.99", "2026-12-02")
tool = (ROOT / "tools/can-my-mac-run-it/index.html").read_text()
tool_app = next(json.loads(s) for s in re.findall(r'<script type="application/ld\+json">(.*?)</script>', tool, re.S)
                if json.loads(s).get("@type") == "WebApplication")
assert tool_app["offers"] == {"@type": "Offer", "price": "0", "priceCurrency": "USD"}
print("ok   sale generators, regular HTML fallbacks and all three JSON-LD Offers")

# 2026-11-13, Matthew's order: the receipt-page fallback records the shown sale price.
thanks = (ROOT / "thank-you.html").read_text()
value_script = re.search(r'var _value = .*?catch \(e2\) \{\}', thanks, re.S).group()
tracking = r"""
const assert = require('assert');
const source = JSON.parse(require('fs').readFileSync(0, 'utf8'));
const now = 1800000000000;
Date.now = () => now;
for (const [raw, expected] of [
  [JSON.stringify({offer:'founding', t:now}), 16.99],
  [JSON.stringify({offer:'regular', t:now}), 29],
  [JSON.stringify({offer:'founding', t:now-86400000}), 29],
  [null, 29], ['broken JSON', 29]
]) {
  global.localStorage = {getItem: () => raw, removeItem: () => {}};
  eval(source);
  assert.equal(_value, expected);
}
"""
tracking_result = subprocess.run(["node", "-e", tracking], input=json.dumps(value_script),
                                 capture_output=True, text=True, timeout=30)
assert tracking_result.returncode == 0, tracking_result.stderr
print("ok   receipt-page sale, regular, expired, missing and broken storage values")

# Read only the SCRIPT expression, without importing or running the generator.
module = ast.parse((ROOT / "scripts/product_box.py").read_text())
expression = next(n.value for n in module.body if isinstance(n, ast.Assign)
                  and any(isinstance(t, ast.Name) and t.id == "SCRIPT" for t in n.targets))
generated = eval(compile(ast.Expression(expression), "product_box.SCRIPT", "eval"),
                 {"__builtins__": {}, "FOUNDING_ENDS": end})
assert PBOX.search(generated).group(1) == script, "generator reveal differs from the pages"
copies = 0
for path in sorted(ROOT.rglob("*.html")):
    if ".git" in path.parts or path.name in {"privacy.html", "terms.html"}:
        continue
    for copy in PBOX.findall(path.read_text(encoding="utf-8")):
        assert copy == script, f"different reveal in {path.relative_to(ROOT)}"
        copies += 1
print(f"ok   {copies} HTML reveal copies match the generator")

# 2026-11-09 (CEO, launch-price wording): a price left in plain text right before a launch-price span would show next to
# the launch price, the "$49 once · $24.50" comparison the wording change removed. It must sit in <span data-pbox-regular>.
beside, spans_seen = [], 0
for path in sorted(ROOT.rglob("*.html")):
    if ".git" in path.parts:
        continue
    page = path.read_text(encoding="utf-8")
    for m in re.finditer(r"<span data-pbox-founding hidden>", page):
        spans_seen += 1
        before = page[max(0, m.start() - 200):m.start()]
        if re.search(r"\$\d", before[before.rfind(">") + 1:]):
            beside.append(f"{path.relative_to(ROOT)}: {before[-60:]!r}")
assert spans_seen >= 200, f"only {spans_seen} launch-price spans found; the scan is broken"
assert not beside, "a price sits right before a launch-price span outside data-pbox-regular:\n  " + "\n  ".join(beside[:10])
print(f"ok   {spans_seen} launch-price spans, none with a bare price right before it")

# 2026-11-13, Matthew's order: the sale ends on 2 December US Pacific.
assert end == "2026-12-03T07:59:00Z"
ANSWER = {"unlimited": True, "left": 1000000, "of": None, "soldOut": False,
          "endsAt": "2026-12-03T07:59:59Z"}
CASES = [  # Keep the worker shapes covered as well as the deadline changes.
    ("uncapped", {"answer": ANSWER, "sale": True}),
    ("uncapped without left", {"answer": {"unlimited": True, "of": None}, "sale": True}),
    ("capped with seats", {"answer": {"left": 3, "of": 25}, "sale": True}),
    ("no seats", {"answer": {"left": 0, "of": 25}, "sale": False}),
    ("sold out", {"answer": {**ANSWER, "soldOut": True}, "sale": False}),
    ("empty answer", {"answer": None, "sale": False}),
    ("fetch failure", {"answer": ANSWER, "fail": True, "sale": False}),
    ("loaded at deadline", {"answer": ANSWER, "start": 0, "sale": False}),
    ("loaded after deadline", {"answer": ANSWER, "start": 1, "sale": False}),
    ("fetch answers at deadline", {"answer": ANSWER, "response": 0, "sale": False}),
    ("fetch answers after deadline", {"answer": ANSWER, "response": 1, "sale": False}),
    ("open across deadline", {"answer": ANSWER, "sale": True, "expire": True}),
    ("restore saved DOM values", {"answer": ANSWER, "sale": True, "expire": True, "custom": True}),
    ("timer just under 24 days", {"answer": ANSWER, "sale": True, "start": -24*86400000+1}),
    ("no timer at 24 days", {"answer": ANSWER, "sale": True, "start": -24*86400000}),
    ("no timer above 24 days", {"answer": ANSWER, "sale": True, "start": -25*86400000}),
]
harness = r"""
const assert = require('assert');
const [scripts, original, endIso, kind, useOverride, options] = JSON.parse(require('fs').readFileSync(0, 'utf8'));
const end = Date.parse(endIso), limit = 24*86400000;
let now = end + (options.start ?? -60000), resolveFetch, rejectFetch, clicks, stored;
const initial = {...original};
if (options.custom) Object.assign(initial, {
  name: 'Saved card name', bnpl: '<span>Saved pay-in-4 line</span>', btn: 'Saved button text'
});
const nodes = {
  name: {textContent: initial.name}, price: {textContent: initial.price},
  bnpl: {innerHTML: initial.bnpl}, offer: {hidden: initial.offer}, btn: {textContent: initial.btn}
};
// 2026-11-09: the regular price beside a launch-price span (<span data-pbox-regular>) hides while the launch price shows.
const regular = () => ({hidden: false, hasAttribute: a => a === 'data-pbox-regular'});
const regs = [regular(), regular()];
const spans = [{hidden: true, previousElementSibling: regs[0]}, {hidden: true, previousElementSibling: regs[1]}, {hidden: true}];
const card = {querySelector: s => nodes[s.match(/data-lt-(\w+)/)[1]]};
global.window = useOverride ? {__kcNow: now} : {};
Date.now = () => now;
global.document = {
  querySelector: s => { assert.equal(s, '[data-lifetime-card]'); return card; },
  querySelectorAll: s => { assert.equal(s, '[data-pbox-founding]'); return spans; },
  addEventListener: (event, handler) => { assert.equal(event, 'click'); clicks = handler; }
};
global.localStorage = {setItem: (key, value) => { assert.equal(key, 'outlier_offer'); stored = JSON.parse(value); }};
const timers = [];
global.setTimeout = (fn, delay) => { timers.push({fn, delay, due: now + delay}); };
let fetched = 0;
global.fetch = () => {
  fetched++;
  return new Promise((resolve, reject) => { resolveFetch = resolve; rejectFetch = reject; });
};
function advance(target) {
  now = target;
  if (useOverride) window.__kcNow = now;
  for (const timer of timers) if (!timer.fired && timer.due <= now) {
    timer.fired = true;
    timer.fn();
  }
}
function state() {
  return {name: nodes.name.textContent, price: nodes.price.textContent, bnpl: nodes.bnpl.innerHTML,
          offer: nodes.offer.hidden, btn: nodes.btn.textContent};
}
function check(sale) {
  if (kind === 'pbox') {
    assert.deepStrictEqual(spans.map(s => s.hidden), [!sale, !sale, !sale]);
    assert.deepStrictEqual(regs.map(r => r.hidden), [sale, sale]);
  } else {
    const expected = sale ? {...initial, name: 'Outlier Lifetime Licence', price: '$16.99', bnpl: '',
      offer: false, btn: 'Buy Outlier Lifetime Licence: $16.99'} : initial;
    assert.deepStrictEqual(state(), expected);
    const a = {hasAttribute: () => true};
    clicks({target: {closest: () => a}});
    assert.equal(stored.offer, sale ? 'founding' : 'regular');
  }
}
(async function () {
  eval(scripts[kind]);
  check(false);
  const before = now < end;
  assert.equal(fetched, before ? 1 : 0);
  assert.equal(timers.length, before && end-now < limit ? 1 : 0);
  if (timers.length) assert.equal(timers[0].delay, end-now);
  if (before) {
    if (options.response !== undefined) advance(end + options.response);
    if (options.fail) rejectFetch(new Error('offline'));
    else resolveFetch({json: () => Promise.resolve(options.answer)});
    // Drain the response and JSON promise callbacks without real timers.
    for (let i = 0; i < 8; i++) await Promise.resolve();
  }
  check(options.sale);
  if (options.expire) {
    advance(end - 1);
    check(true);
    advance(end);
    check(false);
    advance(end + 1);
    check(false);
  }
})().catch(e => { console.error(e.stack); process.exitCode = 1; });
"""
bad = 0
with tempfile.TemporaryDirectory() as d:
    h = pathlib.Path(d) / "h.js"
    h.write_text(harness)
    for kind in ("pbox", "card"):
        for use_override in (True, False):
            for name, options in CASES:
                payload = [{"pbox": script, "card": card_script}, regular, end, kind, use_override, options]
                out = subprocess.run(["node", str(h)], input=json.dumps(payload), capture_output=True, text=True, timeout=30)
                ok = out.returncode == 0
                bad += not ok
                print(("ok  " if ok else "FAIL"), kind, "__kcNow" if use_override else "Date.now", name,
                      f"exit={out.returncode}")
                if not ok:
                    print(out.stderr)
print("ALL PASS" if not bad else f"{bad} FAILED")
sys.exit(1 if bad else 0)
