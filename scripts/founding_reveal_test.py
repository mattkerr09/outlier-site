#!/usr/bin/env python3
"""The founders reveal script, run for real in node against the worker's answers (2026-11-02, CEO: the sale is uncapped and
/founding answers {unlimited: true, left: 1000000, of: null}; the hidden span and the homepage card must still reveal, and
must stay hidden when the worker says sold out or the end date has passed).

    python3 scripts/founding_reveal_test.py        # exit 0 = every case as expected
"""
import json, pathlib, re, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
page = (ROOT / "vs" / "jan-vs-ollama" / "index.html").read_text(encoding="utf-8")
script = re.search(r"<script data-pbox-script>(.*?)</script>", page, re.S).group(1)
CASES = [  # (worker answer, now, should reveal)
    ({"unlimited": True, "left": 1000000, "of": None, "soldOut": False, "endsAt": "2026-12-01T07:59:59Z"}, "2026-11-10T12:00:00Z", True),
    ({"unlimited": True, "of": None, "soldOut": False}, "2026-11-10T12:00:00Z", True),          # no left at all
    ({"left": 3, "of": 25, "soldOut": False}, "2026-11-10T12:00:00Z", True),                     # the old capped shape
    ({"left": 0, "of": 25, "soldOut": False}, "2026-11-10T12:00:00Z", False),
    ({"unlimited": True, "left": 1000000, "soldOut": True}, "2026-11-10T12:00:00Z", False),
    ({"unlimited": True, "left": 1000000, "soldOut": False}, "2026-12-01T08:00:00Z", False),      # after the end
    (None, "2026-11-10T12:00:00Z", False),
]
harness = r"""
const [script, answer, nowIso] = JSON.parse(require('fs').readFileSync(0, 'utf8'));
const spans = [{hidden: true}, {hidden: true}];
global.window = {__kcNow: Date.parse(nowIso)};
global.document = {querySelectorAll: () => spans};
let fetched = false;
global.fetch = () => { fetched = true; return Promise.resolve({json: () => Promise.resolve(answer)}); };
eval(script);
setTimeout(() => process.stdout.write(JSON.stringify({revealed: spans.every(s => s.hidden === false), fetched})), 20);
"""
bad = 0
with tempfile.TemporaryDirectory() as d:
    h = pathlib.Path(d) / "h.js"; h.write_text(harness)
    for answer, now, want in CASES:
        out = subprocess.run(["node", str(h)], input=json.dumps([script, answer, now]), capture_output=True, text=True, timeout=30)
        got = json.loads(out.stdout or "{}").get("revealed")
        ok = got == want
        bad += not ok
        print(("ok  " if ok else "FAIL"), f"answer={answer} now={now} -> revealed={got} (want {want})" + (f" stderr={out.stderr[:200]}" if out.stderr else ""))
print("ALL PASS" if not bad else f"{bad} FAILED")
sys.exit(1 if bad else 0)
