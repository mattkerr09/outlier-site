#!/usr/bin/env python3
"""Check live-app privacy claims offline, including a restored-claim control."""
from html import unescape
from pathlib import Path
import re
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN = [
    r"nothing you type leaves (your|the) (mac|device)(?! unless you use web search or)",
    r"unless you turn on web search(?:,| or) (?:cloud|a cloud)",
    r"by default,? nothing you type leaves",
    r"stays on your mac unless you turn on web search",
    # 1.11.1020 (live 2026-11-22): with Search the web off, Auto never starts Research and choosing Research asks to
    # turn search on. The 1012-era "Auto can pick Research even with web search off" is false now.
    r"auto can pick|auto picks it|pick research in auto mode|choosing research in auto mode|research reads the web even with search off",
]
# These exact sentences describe local AI generally or Nano only, not Pro Auto.
EXEMPTIONS = {
    "learn/is-local-ai-safe/index.html": [
        "Local AI is safe when the app is signed and the weights come from a reputable source — and it's safer for your data than cloud AI, because with local models nothing you type leaves your Mac.",
    ],
    "how-to/run-ai-on-8gb-mac/index.html": [
        "Nothing you type leaves your Mac unless you turn web on.",
    ],
}

EDITED_CLAIMS = {'learn/how-local-ai-gets-smarter/index.html': ['Runs on your Mac; nothing you type leaves it unless you use '
                                                "web search or Pro's Research mode, cloud escalation or a "
                                                'cloud model.'],
 'learn/why-local-ai-is-slow-to-start/index.html': ['Runs on your Mac; nothing you type leaves it unless you '
                                                    "use web search or Pro's Research mode, cloud escalation "
                                                    'or a cloud model.'],
 'index.html': ['Chats stay on your Mac unless you use web search or Research.',
                'Outlier runs the model on your own Mac, so your code and chats stay on it unless you use '
                'web search or Research.',
                "It edits code, runs tests and searches the web through web search or Pro's Research mode.",
                "Nothing you type leaves your Mac unless you use web search or Pro's Research mode, or pick "
                'a cloud model with your own API key',
                'With web search off, Auto never starts Research, and the app goes online on its own only '
                'for things that carry none of your words: model downloads, the update check, the price '
                'shown when you open an upgrade window, and on Pro the license check.',
                "Pro's Research reads the web, and Research runs only with web search on.",
                'Web search, web pages, web-connected tools and external API keys can send requests out; '
                'Research runs only with web search on.'],
 'for/index.html': ['Chats stay on your Mac unless you use web search or Research, and nothing trains on '
                    'them.',
                    'In Chat or Code mode with web search off, confidential or non-public information stays '
                    "on your Mac; Pro's Research reads the web.",
                    'Outlier runs models locally on your Mac; Chat or Code mode with web search off keeps '
                    'your words and files local, and Auto never starts Research with web search off.',
                    'Outlier drafts progress notes and intake summaries on your Mac in Chat or Code mode '
                    'with web search off; Auto never starts Research with web search off.',
                    'Outlier runs the model on your Mac; use Chat or Code mode with web search off for '
                    'patient data (with web search off, Auto never starts Research).',
                    "Outlier runs on your Mac; a client's documents stay there with a local model in Chat or "
                    'Code mode and web search off, and Auto never starts Research with web search off.',
                    'Outlier keeps interview summaries and drafts on your Mac in Chat or Code mode with web '
                    'search off; Auto never starts Research with web search off.',
                    "Keep web search off and pick Chat or Code mode for source material, since Pro's "
                    'Research reads the web.',
                    'Outlier runs on your Mac; Chat or Code mode with web search off keeps that work local '
                    'and nothing trains on it, and Auto never starts Research with web search off.',
                    'Outlier drafts, post-edits and checks terminology on your Mac; use Chat or Code mode '
                    'with web search off to keep source text local (with web search off, Auto never starts '
                    'Research).',
                    'With those free models and web search off, nothing you type or attach leaves the '
                    'device; Free cannot run Research.',
                    'Outlier drafts listing copy, emails and offer summaries on your Mac in Chat or Code '
                    'mode with web search off; Auto never starts Research with web search off.',
                    'Outlier is $39 once per person, and pre-public code and strategy stay on each Mac in '
                    'Chat or Code mode with web search off; Auto never starts Research with web search off.',
                    'Outlier is a $39 licence you pay once per person, good on up to 3 Macs at a time, and '
                    "each person's work stays on their own machine in Chat or Code mode with web search off; "
                    'Auto never starts Research with web search off.',
                    "Outlier's Nano and Lite models are free, Pro is $39 once, and donor and beneficiary "
                    "records stay on the staffer's Mac in Chat or Code mode with web search off; Auto never "
                    'starts Research with web search off.'],
 'for/lawyers/index.html': ['Chats stay on your Mac unless you use web search or Research.',
                            "Local AI helps with the confidentiality duty when you use Outlier's local "
                            'models in Chat or Code mode with web search off; Auto never starts Research '
                            'with web search off.',
                            'Outlier runs language models directly on your Mac; privileged client '
                            'information stays there in Chat or Code mode with web search off, and Auto '
                            'never starts Research with web search off.'],
 'help/index.html': ['When you use local models in Chat or Code mode with web search off, your prompts, chat '
                     'history, memory, personas, projects, uploaded files and model output stay on your Mac; '
                     'Auto never starts Research with web search off.',
                     "Web search sends your search query when you turn search on, and Pro's Research reads "
                     'the web only when search is on: with it off, Auto never starts Research, and choosing '
                     'Research asks you to turn search on.'],
 'how-to/keep-prompts-private-on-mac/index.html': ['Pick Chat mode with web search off; Research uses the '
                                                   'web.',
                                                   'Use an Outlier local model in Chat or Code mode with web '
                                                   'search off; Auto never starts Research with web search '
                                                   'off.',
                                                   'Outlier can run private AI chat on a Mac and keep '
                                                   'prompts, chat history or files local in Chat or Code '
                                                   'mode with a local model and web search off; Auto never '
                                                   'starts Research with web search off.',
                                                   'Keep the composer&rsquo;s web search switch off, use a '
                                                   'local model and pick Chat or Code mode; Auto never '
                                                   'starts Research with web search off.',
                                                   'Send a message to a downloaded local model in Chat or '
                                                   'Code mode with web search off; Auto never starts '
                                                   'Research with web search off.'],
 'best/private-ai-no-cloud/index.html': ['On a Mac, Outlier is that server when you choose a downloaded '
                                         'local model in Chat or Code mode with web search off after setup; '
                                         'Auto never starts Research with web search off.',
                                         'model downloads, the update check, a price check while an upgrade '
                                         'window is open, the Pro licence check, web search when it is on, '
                                         "and Pro's Research, which runs only with web search on."],
 'how-to/use-ai-offline-mac/index.html': ['Then use that model in Chat or Code mode with web search off; '
                                          'Auto never starts Research with web search off.'],
 'learn/ai-chatbots-share-chats-with-trackers/index.html': ['Local mode means using a local model in Chat or '
                                                            'Code mode with web search off; Auto never '
                                                            'starts Research with web search off.',
                                                            'Web search and cloud models send information to '
                                                            'outside services when you turn them on, and '
                                                            "Pro's Research also sends search queries even "
                                                            'with web search off.'],
 'learn/ai-privacy-policies-explained/index.html': ['Local AI like Outlier has far less to disclose, because '
                                                    'inference happens on your device; Chat or Code mode '
                                                    'with web search off keeps your words local, and Auto '
                                                    'never starts Research with web search off.',
                                                    'it covers the site, licensing, web research and your '
                                                    "own API keys, including Pro's Research, which runs only "
                                                    'with web search on.'],
 'learn/check-an-ai-app-is-offline-on-mac/index.html': ['Turn web search off, keep the chat on that local '
                                                        'model and choose Chat or Code mode; Auto never '
                                                        'starts Research with web search off.'],
 'learn/does-chatgpt-use-a-data-center/index.html': ['With local models nothing you type leaves your Mac '
                                                     "unless you use web search or Pro's Research mode, or "
                                                     'pick a cloud model with your own API key, so it works '
                                                     'with the Wi-Fi off, on a plane for example.',
                                                     'Outlier is a Mac app built around this: the model '
                                                     'files sit on your disk and answer locally in Chat or '
                                                     'Code mode with web search off, and Auto never starts '
                                                     'Research with web search off.',
                                                     'Outlier runs the model on your own Mac; your questions '
                                                     'stay there in Chat or Code mode with web search off, '
                                                     'and Auto never starts Research with web search off.'],
 'learn/is-local-ai-safe-from-prompt-injection/index.html': ['For Outlier, use a local model in Chat or Code '
                                                             'mode and turn web tools off when working with '
                                                             'untrusted text; Auto never starts Research '
                                                             'with web search off.'],
 'learn/is-local-ai-safe/index.html': ['You can also check it yourself in Terminal, in Chat or Code mode '
                                       'with web search off (with it off, Auto never starts Research):'],
 'privacy.html': ["Chat and Code with web search off keep your words on your Mac; Pro's Research reads the "
                  'web and Research runs only with web search on.',
                  'Your prompts, chat history, memory, personas, projects, and uploaded files, as long as '
                  'you use Outlier&rsquo;s local models in Chat or Code mode with web search off; Auto never '
                  'starts Research with web search off.',
                  'when you toggle 🌐 search on for a turn, or when Pro uses Research, which needs web search '
                  'on.'],
 'thank-you.html': ["Nothing you type leaves your Mac unless you use web search or Pro's Research mode, or "
                    'pick a cloud model with your own API key.',
                    'Web search and external API keys are off by default, and Research runs only with web '
                    'search on.'],
 'vs/cloud-wrapped-local-ai-assistants/index.html': ['The model runs on your Mac; Chat or Code mode with web '
                                                     'search off keeps your words local, and Auto never '
                                                     'starts Research with web search off.',
                                                     'Nothing you type leaves the device unless you use web '
                                                     "search or Pro's Research mode, cloud escalation or a "
                                                     'tool you connect.',
                                                     'Outlier runs the model on your Mac: Chat or Code mode '
                                                     'with web search off keeps your words local, and Auto '
                                                     'never starts Research with web search off.'],
 'vs/outlier-vs-claude-code/index.html': ["Outlier's pitch is different: it's local, there's no API key, "
                                          "there's no usage cap, and your code stays on your Mac unless you "
                                          "use web search or Pro's Research mode, or pick a cloud model with "
                                          'your own API key.',
                                          'Your code stays on your Mac in Code mode with web search off; '
                                          'Auto never starts Research with web search off, and an agent '
                                          'command you approve can reach the internet.'],
 'vs/outlier-vs-chatgpt/index.html': ['Your chats and files stay on the device in Chat or Code mode with web '
                                      "search off; Pro's Research sends search queries out and runs only "
                                      'with web search on.',
                                      "Outlier's free tiers have no web search and answer from what's in the "
                                      "model's training data; Pro adds web research, which sends search "
                                      'queries out; Research runs only with web search on.'],
 'vs/outlier-vs-microsoft-copilot/index.html': ["A chat can leave through 🌐 search, Pro's Research mode, "
                                                'which runs only with search on, or a cloud model with your '
                                                'own API key; the app also checks for updates and, on Pro, '
                                                'its licence key.',
                                                "Web search, Pro's Research, cloud models, connectors and "
                                                'agent commands you approve can send data out, and Research '
                                                'runs only with web search on.'],
 'vs/outlier-vs-perplexity/index.html': ["Pro's web research sends search queries to web search providers, "
                                         'and Research runs only with web search on.',
                                         'Pick Chat or Code mode with web search off to keep your words on '
                                         "your Mac; Pro's Research reads the web.",
                                         "Outlier's free tier has no web search at all; Outlier Pro adds web "
                                         'research and Deep Research, which runs only with web search on and '
                                         'sends search queries out.',
                                         '<strong>Outlier Pro</strong> ships web research and Deep Research, '
                                         'which sends search queries out and runs only with web search on.'],
 'vs/outlier-vs-poe/index.html': ['Outlier runs models on your own Mac: no account, no caps, works with '
                                  "Wi-Fi off, and your words stay local unless you use web search or Pro's "
                                  'Research mode, or a cloud model with your own API key.',
                                  'What it does have is the whole model running on your machine: no account, '
                                  'no usage cap, and your words stay local unless you use web search or '
                                  "Pro's Research mode, or cloud escalation with your own API key.",
                                  "Web search, Pro's Research and cloud escalation with your own API key can "
                                  'send data out.',
                                  'Pick Chat or Code mode with web search off to keep your words local; Auto '
                                  'never starts Research with web search off.',
                                  "Nothing you type leaves your Mac unless you use web search or Pro's "
                                  'Research mode, or pick a cloud model with your own API key.'],
 'vs/outlier-vs-qwen-chat/index.html': ['Outlier runs <em>published</em> open weights on your own Apple '
                                        "Silicon Mac; web search, Pro's Research mode or a cloud model with "
                                        "your own API key can send your words out: Qwen's for five of its "
                                        "six tiers and Google's Gemma 4 for Quick, no account on the free "
                                        'tiers, no caps, works with Wi-Fi off for all six tiers.'],
 'vs/qwen-vs-llama/index.html': ["That's what I built Outlier for: Apple Silicon only, no account, no usage "
                                 "caps, and your words stay local unless you use web search or Pro's "
                                 'Research mode, or a cloud model with your own API key.'],
 'vs/grammarly-vs-local-ai/index.html': ['Web research is Pro-only, and Research runs only with web search '
                                         'on; the free tiers have no web search at all.']}


def served_files(root):
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if rel.parts[0] in ("scripts", ".git") or rel.parts[:2] == ("_seo_build", "out"):
            continue
        if path.is_file() and (path.suffix in (".html", ".md") or rel.as_posix() == "llms.txt"):
            yield path


def forbidden_claims(root):
    failures = []
    for path in served_files(root):
        rel = path.relative_to(root).as_posix()
        source = unescape(path.read_text(encoding="utf-8"))
        for sentence in EXEMPTIONS.get(rel, []):
            source = source.replace(sentence, "")
        # Normalize HTML and whitespace so line breaks cannot hide a claim.
        source = re.sub(r"<[^>]+>", " ", source)
        source = re.sub(r"\s+", " ", source)
        for pattern in FORBIDDEN:
            if re.search(pattern, source, re.I):
                failures.append(f"{rel}: forbidden claim matching {pattern}")
    return failures


def check(root):
    failures = forbidden_claims(root)
    for rel, claims in EDITED_CLAIMS.items():
        source = (root / rel).read_text(encoding="utf-8")
        for claim in claims:
            if claim not in source:
                failures.append(f"{rel}: rewritten claim missing: {claim}")
            elif "Research" not in claim[:200]:
                failures.append(f"{rel}: Research missing within 200 characters of claim")
    return failures


def main():
    failures = check(ROOT)
    # Exercise the same checker against a real temporary page with old copy.
    with tempfile.TemporaryDirectory(prefix="outlier-web-off-") as temp:
        root = Path(temp)
        page = root / "index.html"
        source = (ROOT / "index.html").read_text(encoding="utf-8")
        current = "Nothing you type leaves your Mac unless you use web search or Pro's Research mode, or pick a cloud model with your own API key"
        old = "Nothing you type leaves your Mac unless you turn web on or switch a chat to a cloud model with your own API key"
        if source.count(current) != 1:
            failures.append("negative control: replacement target missing or ambiguous")
        else:
            page.write_text(source.replace(current, old, 1), encoding="utf-8")
            if not forbidden_claims(root):
                failures.append("negative control: restored old sentence passed")
        # Second control (1020): the old Auto-picks-Research sentence put back must fail too.
        current = "Pro's Research reads the web, and Research runs only with web search on."
        old = "Pro's Research reads the web, and Auto can pick Research even with web search off."
        if source.count(current) != 1:
            failures.append("negative control 2: replacement target missing or ambiguous")
        else:
            page.write_text(source.replace(current, old, 1), encoding="utf-8")
            if not forbidden_claims(root):
                failures.append("negative control 2: restored Auto-picks-Research sentence passed")
    if failures:
        print("\n".join("FAIL: " + failure for failure in failures))
        return 1
    print("PASS: served claims, Research qualifications and both restored-sentence negative controls")
    return 0


if __name__ == "__main__":
    sys.exit(main())
