#!/usr/bin/env python3
"""The offline proof is the only evidence on this site. Guard it.

outlier.host's entire pitch is that nothing leaves your Mac. Everything else on
the page ASSERTS that; one block DEMONSTRATES it — a real `lsof` capture taken
while a model was mid-answer, showing only 127.0.0.1 sockets:

    $ lsof -a -p $(pgrep -x outlier-cli) -i -n -P
    outlier-c 62303 22u IPv4 TCP 127.0.0.1:8766->127.0.0.1:56293 (ESTABLISHED)
    outlier-c 62303 25u IPv4 TCP 127.0.0.1:8766 (LISTEN)
    # sampled 17× across a real 27s answer — sockets leaving this Mac: 0

WHY A GATE AND NOT A NOTE. Keeping this block and its control is a SETTLED
decision, and settled decisions are exactly what gets quietly undone by a later
edit that is trying to shorten the page. A prose note in a handoff file does not
survive that; a red gate does.

THE CONTROL IS THE LOAD-BEARING PART, and it is what most "proof" screenshots on
competitor sites lack. The page says it in full:

    "The -a is load-bearing: without it lsof ORs its filters and returns 357
     sockets belonging to every other process — which is how a check like this
     can quietly prove nothing."

A capture without that sentence is a picture of a terminal. With it, the reader
knows the exact way the check could have been faked and can see it was not. If
someone trims the paragraph for length, the evidence silently degrades into
decoration while still looking like evidence. That is the failure this catches.

WHAT IT CHECKS
  1. the capture is present and the command still carries `-a`
  2. every socket shown is loopback — no external address crept into the sample
  3. the control sentence survives, including the 357 figure
  4. the sample count in the caption and in the prose agree (17 / seventeen);
     they are written twice in two formats and would drift independently

WHAT IT CANNOT DO. It cannot re-run lsof, and it cannot tell you the capture is
recent. It checks that the evidence is still evidence.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

PAGE = "index.html"

CMD = re.compile(r"lsof\s+-a\s+-p\s+\$\(pgrep\s+-x\s+outlier-cli\)\s+-i\s+-n\s+-P")
#: The addresses are wrapped in <span class="p-lo"> so they can be coloured, so
#: `TCP\s+<ip>` never matches the raw HTML — my first version reported "no TCP
#: lines found" against a capture that plainly has two. Tags are stripped from
#: the <pre> block before matching, which is also what a reader sees.
SOCKET = re.compile(r"TCP\s+([0-9]{1,3}(?:\.[0-9]{1,3}){3})")
PRE = re.compile(r"(?is)<pre[^>]*>(.*?)</pre>")
TAG = re.compile(r"<[^>]+>")
CONTROL = re.compile(r"-a</code>\s*is load-bearing|<code>-a</code> is load-bearing|"
                     r"-a\s+is load-bearing")
SEVEN_NUM = re.compile(r"sampled\s+17\s*(?:&times;|×)")
SEVEN_WORD = re.compile(r"sampled it seventeen times", re.I)
THREE57 = re.compile(r"\b357\b")


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    page = root / PAGE
    if not page.exists():
        print(f"FAIL: {page} does not exist — nothing checked, which is not a pass")
        return 1
    text = page.read_text(encoding="utf-8", errors="replace")

    failures: list[str] = []

    # 1. the capture, with -a intact
    if CMD.search(text):
        print("  capture      present, command carries -a")
    else:
        print("  capture      MISSING or the command changed")
        failures.append(
            "    the lsof capture is gone or its command no longer matches. Without `-a`, "
            "lsof ORs its filters and the output proves nothing — the page says so itself.")

    # 2. loopback only
    pre_text = " ".join(TAG.sub(" ", b) for b in PRE.findall(text))
    addrs = sorted(set(SOCKET.findall(pre_text)))
    external = [a for a in addrs if not a.startswith("127.")]
    if addrs and not external:
        print(f"  sockets      {len(addrs)} address(es) shown, all loopback: {', '.join(addrs)}")
    elif external:
        print(f"  sockets      EXTERNAL ADDRESS IN THE CAPTURE: {', '.join(external)}")
        failures.append(
            f"    the capture now shows a non-loopback address ({', '.join(external)}). Either "
            f"the sample is wrong or the claim is — both are worse than showing nothing.")
    else:
        print("  sockets      no TCP lines found in the capture")
        failures.append("    the capture shows no sockets at all — it has been emptied or reformatted")

    # 3. the control
    if CONTROL.search(text) and THREE57.search(text):
        print("  control      present, 357-socket explanation intact")
    else:
        print("  control      MISSING")
        failures.append(
            "    the control sentence is gone. It is the part that makes this evidence rather "
            "than a screenshot: it names how the check could have been faked (lsof without -a "
            "returning 357 unrelated sockets) and shows it was not. Trimming it for length "
            "leaves something that still LOOKS like proof.")

    # 4. the two spellings of the sample count agree
    num, word = bool(SEVEN_NUM.search(text)), bool(SEVEN_WORD.search(text))
    if num and word:
        print("  sample count 17 in the caption and 'seventeen' in the prose — agree")
    else:
        print(f"  sample count caption={'17' if num else 'MISSING'}  prose={'seventeen' if word else 'MISSING'}")
        failures.append(
            "    the sample count is written twice, as a numeral in the caption and a word in "
            "the prose, and they no longer agree. Two copies of one number drift; if the "
            "capture was re-taken, both have to move.")

    print()
    if failures:
        print(f"FAIL: {len(failures)} problem(s) with the offline proof.")
        for f in failures:
            print(f)
        print("\n  Keeping this block AND its control is a settled decision. If the capture was")
        print("  legitimately re-taken, update this gate in the same commit — do not delete it.")
        return 1

    print("OK: the offline proof is intact — loopback-only capture, `-a` present, control")
    print("sentence and its 357 figure surviving, and both spellings of the sample count agreeing.")
    print("This does not re-run lsof and cannot tell you the capture is recent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
