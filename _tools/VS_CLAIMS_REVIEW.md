# Unverified competitor claims — /vs/ batch review sheet

The adversarial verify stage never ran (session limit), so **none of these claims about third
parties have been independently checked**. Each is quoted verbatim with its page. Scan the
LEGAL/SECURITY and QUOTE blocks first — those carry the most liability.

**43 pages · 891 extracted claims**

| category | count |
|---|---|
| LEGAL/SECURITY | 6 |
| QUOTE | 119 |
| MONEY | 218 |
| DATE/VERSION | 375 |
| POLICY | 43 |
| NUMBER | 130 |

---
## ⚠️ LEGAL / SECURITY allegations (read every one)

### `/vs/otter-ai-alternative-local/` — Otter.ai alternative: doing meeting notes locally on a Mac
- Consent risk sits with whoever deployed the recorder: third-party reporting describes a consolidated federal class action in California alleging wiretap and CIPA violations for recording without all-party consent, unresolved as of mid-2026.

### `/vs/outlier-vs-deepseek-app/` — Outlier vs the DeepSeek app: local Mac AI vs a free cloud chat service
- Pick Outlier if the content of your prompts is the problem: client files, patient notes, unreleased source, anything under NDA or anything a regulator won't let cross a border.

### `/vs/outlier-vs-microsoft-copilot/` — Outlier vs Microsoft Copilot: local Mac AI vs Microsoft's cloud
- The Copilot Copyright Commitment means Microsoft defends a commercial customer sued over Copilot output and pays resulting judgments, provided the guardrails were used.

### `/vs/outlier-vs-perplexity/` — Outlier vs Perplexity: local Mac AI vs a cloud answer engine
- Against that, Brave's security team documented indirect prompt injection in Comet: page content reached the model without separating user instructions from untrusted webpage text, letting hidden instructions exfiltrate data from logged-in sessions.
- Sources and receipts: Perplexity pricing from its own Max and enterprise announcements plus the App Store listing ; API rates from docs.perplexity.ai ; data handling from the privacy policy , terms of service and privacy snapshot ; citation accuracy from the Tow Center study ; Comet prompt injection from Brave .

### `/vs/outlier-vs-zed-ai/` — Outlier vs Zed AI: on-device Mac models vs a cloud-first code editor
- Worth checking — after the March 2, 2026 terms overhaul, the AI service requires users to be 18 or older, with binding arbitration and a class action waiver (30-day opt-out) under Delaware law.

---
## ✅ MANUALLY VERIFIED (2026-07-23) — highest-liability claims checked against primary sources

The adversarial verify agents never ran, so these four were checked by hand. **All four hold up.**

| Claim | Page | Verdict | Source checked |
|---|---|---|---|
| Brave documented indirect prompt injection in Perplexity's Comet; reported 25 Jul 2025, disclosed 20 Aug 2025; Perplexity "still hasn't fully mitigated the kind of attack described here" | `/vs/outlier-vs-perplexity/` | **VERIFIED — quote is verbatim, both dates exact** | brave.com/blog/comet-prompt-injection/ |
| Consolidated federal class action in California alleging wiretap + CIPA violations, unresolved mid-2026 | `/vs/otter-ai-alternative-local/` | **VERIFIED** — *In re Otter.AI Privacy Litigation*, No. 5:25-cv-06911 (N.D. Cal.), consolidated 22 Oct 2025; ECPA + CIPA; MTD argued 20 May 2026, ruling pending | NPR, Nat'l Law Review, court docket reporting |
| Zed's 2 Mar 2026 terms: 18+, binding arbitration, class-action waiver, 30-day opt-out, Delaware law | `/vs/outlier-vs-zed-ai/` | **VERIFIED — all five elements exact, effective date exact** | zed.dev/terms-of-service (primary) |
| Copilot Copyright Commitment: Microsoft defends commercial customers sued over Copilot output and pays adverse judgments, if guardrails were used | `/vs/outlier-vs-microsoft-copilot/` | **VERIFIED** — matches Microsoft's stated commitment incl. the guardrails condition | Microsoft CCC announcement + secondary legal coverage |

The two remaining LEGAL/SECURITY regex hits are **false positives** of the extractor, not claims about third parties:
- `/vs/outlier-vs-deepseek-app/` — "anything a regulator won't let cross a border" is our own framing.
- `/vs/outlier-vs-perplexity/` — the "Sources and receipts" line is a citation list, not an allegation.

**Still unverified:** the 119 direct quotes, 218 money claims, 375 dates/versions, 43 policy claims and
130 numbers below. Prices and policies change fastest — treat anything dated as needing a re-check
before it is cited elsewhere.

---
## Direct quotes attributed to a third party

### `/vs/4-bit-vs-8-bit-quantization/`
- "Half a byte per parameter" understates the real footprint by roughly 20%, so size a model against your RAM using the published file size, not arithmetic.
- "Scaling Laws for Precision" (Kumar et al., 2024, fit on 465+ pretraining runs) finds post-training quantization degradation rises with training data, to the point where extra pretraining turns actively harmful for the quantized model.
- The honest answer is often "4-bit, with 6-bit in three places." Sources and receipts: Bits per weight, sizes and throughput: llama.cpp quantize README .

### `/vs/deepseek-vs-qwen/`
- Qwen is equally blunt: "All our open-weight models are licensed under Apache 2.0." Both are OSI-approved, and neither imposes a use policy or an approval form.
- Its model card bills it as "Flagship-Level Coding in a 27B Dense Model," and 27B dense quantizes onto a 32 GB Mac.
- That last tier cuts against my own argument, so I'll say it plainly: expert streaming does let a 397B MoE run on a 64 GB desktop, so "too big for consumer hardware" isn't absolute.
- Its terms document an in-product "Improve the model for everyone" toggle plus an email opt-out, and explicitly assign output rights: "We assign any rights, title, and interests&#8212;if any&#8212;in the Outputs of the Services to you." Qwen documents no equivalent toggle; its policy lists training on de-identified User Content and Feedback under a legitimate-interests basis, offering only generic rights to object or withdraw consent through a DPO email.

### `/vs/gemma-vs-llama/`
- The Community License, effective 5 April 2025, requires a separate license from Meta above 700 million monthly active users, requires you to prominently display "Built with Llama," and requires any derived model's name to begin with "Llama." The sharpest condition is territorial.
- Both disclaim warranties entirely; the Gemma terms provide the model "AS IS" and "WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND." What runs on a Mac, at what RAM The arithmetic is simple: 4-bit weights are half a byte per parameter, so a 12B model's weights land near 6 GB before context and overhead, and a 31B near 15–16 GB.
- On Google's Gemini API, Gemma 4 is free-tier-only with the paid tier marked "Not available," and the free tier marked "Used to improve our products: Yes." Google's terms say human reviewers may read and annotate API input and output, and warn against submitting sensitive or personal information.

### `/vs/grammarly-vs-local-ai/`
- Grammarly's own documentation is blunt — "your computer must be connected to the internet" — and there's no offline mode.

### `/vs/local-ai-vs-api-for-developers/`
- Data path, retention and licensing "Cloud means they train on your prompts" is false at the paid tiers.
- Runtimes are clean — llama.cpp, Ollama and MLX are MIT, vLLM Apache-2.0 — but weights are messier. gpt-oss and Qwen3-32B are Apache-2.0; Meta's Llama 4 Community License isn't, requiring a separate license request if your products exceeded 700 million monthly active users on the release date, a "Built with Llama" notice, and derivative names beginning with "Llama".
- Air-gapped or regulated work: "the process never sees a network" beats any retention policy.

### `/vs/m1-vs-m4-for-local-ai/`
- Apple silicon shares one pool between CPU and GPU, which is why MLX, Apple's MIT-licensed array framework, is built on the line "Arrays in MLX live in shared memory." No copy across a PCIe bus, no VRAM cliff.
- Apple never published a bandwidth figure for the base M1, but called M1 Max's 400GB/s "nearly 6x that of M1," and later said M5's 153GB/s is "more than 2x over M1" — both imply about 68GB/s.
- 16GB is the M1 maximum — Apple's spec sheet for the M1 MacBook Air reads "8GB unified memory, Configurable to 16GB," and plenty shipped with 8GB.
- LM Studio still tells 8GB owners to "stick to smaller models and modest context sizes." Chip ceilings aren't machine ceilings either: Apple's spec page tops the M4 Mac mini at 24GB, not 32GB.
- Metal exposes a "recommended max working set size" for exactly this; I couldn't retrieve Apple's documented fraction, so I won't quote one.
- MLX lead maintainer Awni Hannun wrote in the project's repo that "at the moment we don't have plans to support ANE in MLX given it is a closed source API," reconfirmed it in 2025, and the request is closed as wontfix. llama.cpp runs on Metal, and Ollama's blog says its Apple silicon build now sits on MLX.
- M5 shipped in October 2025 with a Neural Accelerator in every GPU core and 153GB/s bandwidth, and Apple claims "over 4x the peak GPU compute performance for AI compared to M4." M5 Pro and M5 Max followed in March 2026.
- A discrete card makes you shrink the model to fit; unified memory lets you scale the model to the machine — Apple markets the M4 Max's 128GB as enough to "easily interact with large language models that have nearly 200 billion parameters," and the M3 Ultra Mac Studio configures to 512GB.
- Apple's Foundation Models framework — a ~3B on-device model, offline, with "AI inference that is free of cost" — runs on any Apple Intelligence-capable Mac.

### `/vs/mac-vs-nvidia-gpu-local-ai/`
- Apple describes the M3 Ultra's pool as "the most high-bandwidth, low-latency memory ever available in a personal computer." A Mac Studio starts at 36GB with M4 Max and goes to 128GB; M3 Ultra starts at 96GB.
- Capacity versus bandwidth Inference has two phases with different bottlenecks, and conflating them is where hardware advice goes wrong. llama.cpp's benchmark thread puts it plainly: prompt processing at large batch size "is compute bound... speed depends on how many FLOPS you can utilize," while generating one token at a time is bandwidth-bound.
- In May 2026 NVIDIA announced RTX Spark — Grace CPU plus Blackwell RTX GPU over NVLink-C2C, "up to 128GB of unified memory," 1 petaflop of AI performance, and a claim of 120B-parameter models at 1M tokens of context — shipping this fall.

### `/vs/macbook-air-vs-pro-local-ai/`
- Three numbers, and only three The software isn't the variable. macOS, Metal, and MLX — Apple's MIT-licensed array framework, built so "arrays live in shared memory" and operations run on CPU or GPU without transferring data — are identical on both, and one binary covers a 16GB fanless Air and a 128GB M5 Max.
- MacBook Air (M5) MacBook Pro (M5 Pro) MacBook Pro (M5 Max) Memory: standard / max 16GB / 32GB 24GB / 64GB 36GB / 128GB (128GB needs the 40-core GPU) Memory bandwidth 153GB/s 307GB/s 460GB/s (32-core) or 614GB/s (40-core) Cooling Fanless, silent Active (fans) Active (fans) High Power Mode No Yes Yes Starting price $1,099 (13") / $1,299 (15") $2,199 (14") / $2,699 (16") $3,599 (14") / $3,899 (16") Price per GB, as shipped ~$69/GB (13") ~$92/GB (14") ~$100/GB (14") Memory upgrade later None — soldered None — soldered None — soldered Battery (Apple video test) Up to 18 hr Up to 22 hr (14") / 24 hr (16") Up to 20 hr (14") One wrinkle the table flattens: there's also a base-M5 14-inch MacBook Pro from $1,599, and High Power Mode is supported only on M5 Pro and Max.
- The number on the box isn't your working budget, either. macOS takes a slice, Metal publishes recommendedMaxWorkingSetSize — "an approximation of how much memory... this GPU device can allocate without affecting its runtime performance" — which sits below total RAM, and the KV cache grows with the conversation.
- LM Studio agrees — 16GB recommended, 8GB Macs held to "smaller models and modest context sizes." 24GB or 32GB Air: adds Core and Code 27B (15.13 GB, 24GB minimum) and Vision 35B-a3b (19.0 GB).
- Pro at 128GB: headroom for long context, and what Apple means by "Run LLMs with hundreds of billions of parameters entirely on device." Note the cliff: M5 Pro stops at 64GB and 128GB needs the 40-core M5 Max, so reaching the very large models is a $3,599-and-up jump, not simply "buy a Pro." Bandwidth decides how fast it comes out 153GB/s on any Air against up to 614GB/s on the top Pro is roughly a 4x spread.
- Apple's claims fit that split without producing an absolute number: the M5 Air is "up to 4x faster performance for AI tasks" than the M4 Air, and the M5 Pro/Max delivers "up to 4x faster LLM prompt processing than M4 Pro and M4 Max." Relative multipliers against unstated workloads, both.
- Fanless vs actively cooled: what silence costs Apple describes the Air plainly: "Both models feature a thin, light, and completely silent fanless design." The Pro has fans plus High Power Mode, which "allows the fans to run at higher speeds" so the machine "may... deliver higher performance in very intensive workloads." The Air has no equivalent control.
- "After 30 minutes, its performance of 776 points was only 11% lower," with package power peaking at 20.5 watts and settling near 9 after twenty.
- The Pro's design is the mirror image — Apple's own phrase is a system moving "50 percent more air than the previous generation." My read, having shipped an app people run for hours: at chat length cooling barely matters, because you finish before the machine warms up.

### `/vs/mistral-vs-qwen/`
- Side by side Mistral Qwen Open sizes 3B, 8B, 14B; 119B-A6.5B; 675B-A41B 0.8B, 2B, 4B, 9B, 27B, 35B-A3B, 122B-A10B, 397B-A17B License Apache 2.0 on the cards checked Apache 2.0 — "all our open-weight models" Flagship open?

### `/vs/notion-ai-vs-local-ai/`
- That page pairs $10 for Plus and $20 for Business with a "Save up to 20% with yearly" note and doesn't separate the monthly figures, so check at checkout before you budget.

### `/vs/otter-ai-alternative-local/`
- The privacy policy, effective 16 June 2026, says Otter trains "our proprietary AI technology on de-identified audio recordings and on transcriptions," and that data labeling providers receive shared data to build training sets.

### `/vs/outlier-vs-aider/`
- Ollama defaults to a 2k context window, which the docs call "very small for working with aider," and silently discards anything beyond it — the docs themselves call that especially dangerous, since users don't realize most of their data is being thrown away.
- Aider's edit formats also want a capable model; the docs warn it "may not work well with less capable models." The cheapest, most private path is the most fragile one.
- On "fix this failing test across four files," Aider does the work and Outlier watches.

### `/vs/outlier-vs-anythingllm/`
- One honest note on local speed for either tool: AnythingLLM's docs recommend 16 GB of RAM and an 8-core CPU, concede that "the LLM is often the bottleneck to a decent experience," and note Apple M-series chips are considerably faster than Intel.

### `/vs/outlier-vs-cline/`
- What Cline is — and what it isn't Cline calls itself "an AI coding agent that lives in your editor and your terminal." It's Apache 2.0, with roughly 65,000 GitHub stars and about 4.74 million VS Code Marketplace installs.
- Cline's enterprise docs say "Your code never leaves your environment" and "Repositories are never indexed or cached." That's true about Cline's servers.
- The privacy notice draws the line: with your own API key, on prompts and outputs, "we do not collect it." With Cline-provided keys it does collect them "in order to facilitate your requests to third-party AI model providers on your behalf." And Cline can't offer a training opt-out because it doesn't hold the model — the ToS and privacy notice both defer to providers, who "may use User Content for training unless you have explicitly opted out where such an option is offered by that AI model provider." The local path is real — Ollama and LM Studio are documented providers — with documented friction: enable "Use Compact Prompt," watch for Ollama's default context silently truncating the system prompt, budget 32-64GB of RAM.
- What it costs The software is free for individual developers; the pricing page says "You only pay for AI inference credits when you use AI models." Bring your own key, buy Cline credits and pick from "100+ models supported by Cline," or take ClinePass — $4.99 the first month, then $9.99/month promotionally, plus possible processing fees.
- Issue #7558 on Cline's repo, "Something very wrong with token usage and cost control," reports two prompts and three responses costing $6.80 after context reached roughly 441k tokens — a user report, not a vendor admission, and closed, but similar threads recur.

### `/vs/outlier-vs-continue-dev/`
- What Continue is, and what happened to it Continue spent three years as the answer to "I want a coding assistant that doesn't lock me to one model vendor." It's a client, not a model: a VS Code extension, a JetBrains plugin, and a CLI on npm as @continuedev/cli .
- The homepage now reads "Continue has joined Cursor," and the README calls the repository "no longer actively maintained" and "read-only for all users" after a final 2.0.0 that removed anonymous telemetry, pulled out authentication and fixed bugs.

### `/vs/outlier-vs-deepseek-app/`
- Outputs are assigned to you, and the Open Platform Terms explicitly permit applying inputs and outputs to "derivative product development, training other models (such as model distillation)." Most vendors forbid precisely that.
- Its privacy policy, updated February 10, 2026, says the company "directly collect[s], process[es] and store[s] your Personal Data in People's Republic of China." What leaves your machine: text and voice input, prompts, uploaded files, photos, feedback and chat history, plus IP address, device identifiers, cookies, OS and approximate location.
- Inputs are used for training by default — the stated purpose includes training and improving DeepSeek's machine learning models, and the policy discloses sharing with corporate-group entities for "foundation model training and optimization." The only opt-out mechanism described is emailing privacy@deepseek.com; no in-app toggle is documented, and the sole in-product control is copying or deleting chat history.

### `/vs/outlier-vs-enchanted/`
- Which is better depends entirely on whether "install and manage Ollama" reads to you as a five-minute chore or a wall.
- The App Store listing was renamed "Enchanted Developers Only" in version 1.9.0, with the entire release note reading "App name changed to reflect that it's for developers only." It sits in the Developer Tools category and its description talks about LLM researchers chatting with self-hosted models.
- It's actively maintained — Enchanted's last functional code commits date to March 2025, the App Store build hasn't moved since August 2025, 113 issues sit open, and and the README's first line now points to Jaz as "the new iteration of this project" — a different product entirely.

### `/vs/outlier-vs-github-copilot/`
- Sources: plans and credits from github.com/features/copilot/plans and GitHub Docs; the 2026-06-01 billing change from “What changed with Copilot billing”; surfaces from the Copilot feature matrix; hosting, retention terms and the 2026-04-24 training policy from the model-hosting and Copilot-policy docs; local-model limits from code.visualstudio.com .

### `/vs/outlier-vs-gpt4all/`
- Credit where it's due: the "Enable Datalake" sharing toggle defaults to Off, so does off-device embedding, and the docs warn plainly that using a remote provider means "your prompts leave your computer to the API provider." Where the project stands as of July 2026 GPT4All's newest release is v3.10.0, published 2025-02-25.
- Nomic's homepage now describes the company as "Domain-Specific AI for Architecture, Engineering & Construction," and GPT4All appears in neither the navigation nor the pricing page.

### `/vs/outlier-vs-grok/`
- On platforms, xAI's own site says Grok is "Available on Web, iOS and Android," and the download footer lists those three plus Grok on X.
- An opt-out exists (Settings → Data Controls → "Improve the model" on mobile, Settings → Data → "Improve the Model" on grok.com), but it's opt-out rather than opt-in, it only covers conversations after you flip it, and it has holes: feedback you volunteer may still be used for training, and unauthenticated users in some regions outside the EU and UK can't opt out at all.

### `/vs/outlier-vs-meta-ai/`
- It runs on Muse Spark, announced April 8, 2026 as "the first in a new series of large language models built by Meta Superintelligence Labs." Muse Spark 1.1, from July 9, 2026, is Meta's "multimodal reasoning model built for agentic tasks," with a one-million-token context window it actively manages.
- The weights are closed — at launch Muse Spark went out only "in private preview via API to select partners," and Meta said it hopes to open-source future versions, a hope rather than a commitment.
- For Premium, Meta lists an "expanded monthly AI usage allowance," the ability to "generate more images and videos," and "more advanced reasoning." Meta publishes no price and says Meta One "is currently in limited testing and isn't available in all locations." Press coverage in May 2026 reported $7.99 and $19.99 a month for the two tiers with no annual plan — reported, not confirmed on a Meta page.
- Its AI Terms state: "Meta will review your interactions with AIs, including the content of your conversations with or messages to AIs, and this review may be automated or manual (human)." The help center adds that "Meta uses your interactions with AIs to improve AI at Meta," and that responses draw on your location and profile details like age, gender and interests.
- Queries can also leave Meta: it "may share certain information with select partners, like search engines," including your messages and your region when the AI can't answer.
- Meta excludes conversations touching religion, sexual orientation, political views, health, ethnic origin and union membership from ad targeting, and points to Ads Preferences — but that's a control, not an off switch, and the change is rolling out in "most regions." The mitigation Meta's own terms offer is telling: "Do not share information that you don't want the AIs to use and retain, such as information about sensitive topics." Deletion exists but is scoped — the app offers "Delete all chats and media," yet nothing says deletion pulls your data out of models already trained on it.

### `/vs/outlier-vs-microsoft-copilot/`
- Only subscribers get "deep integration with documents, emails, spreadsheets, calendars and more." The Mac build lags a little too — Copilot Pages and Deep Research aren't available in it.
- Before answering, it grounds your prompt against Microsoft Graph (mail, chats, files, calendar, meetings), scoped to what your Entra ID account can already see, then "sends the grounded prompt to the LLM" in Microsoft's datacentres.
- Microsoft says it "is no longer available for purchase" and support for existing subscribers ends 1 August 2026; Microsoft 365 Premium is the replacement.
- Personal only gets "higher usage than free for select Copilot features" — you're still metered.
- That's $360 a seat a year, and it's an add-on, not a replacement: "a separate license for a qualifying Microsoft 365 plan is required" — E3/E5, Business Standard/Premium, Office 365 E1/E3/E5 or similar.
- What happens to your data Commercially, Microsoft's written position is strong: "Prompts, responses, and data accessed through Microsoft Graph aren't used to train foundation LLMs," stored interaction data is encrypted and also excluded from training, and Copilot has opted out of Azure OpenAI abuse monitoring, which includes human review of content.
- Microsoft's privacy statement says it may use your data "to develop, train, and fine-tune our AI models, including large language models," and that "in some markets, this data can help train our AI models in Microsoft Copilot unless you opt out." The switches sit under Settings → Privacy.
- Opting out covers past, present and future conversations and propagates within 30 days — but it doesn't exclude them from use for "advertising, digital safety, security, and compliance purposes." History is kept 18 months by default.
- Microsoft says LLM calls route to nearby datacentres "but also can call into other regions where capacity is available during high utilization periods," and customers outside the EU "may have their queries processed in the US, EU, or other regions." Anthropic's models in Copilot are excluded from the EU Data Boundary, so EU/EFTA and UK tenants have them off by default.
- Microsoft also notes responses "aren't guaranteed to be 100% factual." Plenty of people run both , which is the sane answer for most Microsoft shops: Copilot for anything needing tenant data or the live web, Outlier for the confidential work and the plane rides.

### `/vs/outlier-vs-mistral-le-chat/`
- Vibe runs in three modes — Chat, Work for multi-step professional tasks, and Code for development — operating "across web, mobile, your code editor, and your terminal." That means a web app, iOS and Android apps, a terminal CLI, and VS Code and JetBrains plugins.
- An account is optional, and the docs say it "works fully offline with local models, or against any compatible API key you provide." Ecosystem depth.
- Free is "limited messages and web searches." Paid is "Up to 6x free" messages and "Up to 5x free" web searches, every tier marked "subject to fair usage limits." No absolute numbers are published.
- The policy covers "Your Input and Output, subject to your opt-out," and says Mistral doesn't train on your data "when you use Le Chat Enterprise or the paid version of our APIs." A paying Pro subscriber isn't in that exclusion.
- Mistral keeps input and output "until you delete your account or until you delete the conversation." There's no consumer equivalent of the API's zero-data-retention mode.
- A Memory feature also stores past interactions, and the policy warns that sensitive input such as health details "may be stored as a Memory." Outlier's answer is structural, not contractual: no server, so no retention policy, no training toggle, no transfer mechanism.

### `/vs/outlier-vs-msty/`
- The vendor's framing is "local and cloud models, side by side" with "local-first control." Locally it drives three engines — Ollama, MLX and llama.cpp — from one Local Models area, handling GGUF, MLX and Safetensors.
- On Apple Silicon the docs say Msty "generally recommends MLX when an MLX format is available," the right call on a Mac.
- What I'd check before buying: the free tier is personal use only — the terms say use "for the exercise of your trade or profession for which you are compensated" doesn't qualify, so paid work needs Aurum or Enterprise.

### `/vs/outlier-vs-notebooklm/`
- Then you chat with the notebook, and Google's docs say responses are "grounded exclusively in your notebook sources," with citations pointing back to the spot in a document you supplied.
- If the job is "read 200 PDFs and make me a cited podcast about them" — use Gemini Notebook.

### `/vs/outlier-vs-perplexity/`
- Perplexity says free users get "access to a limited number of answers per day" for Deep Research; the numbers people quote come from third-party trackers that disagree with each other.
- Even the Mac Personal Computer app, which reaches local files and 400+ connectors, orchestrates all of it "in a secure development sandbox on Perplexity servers," by Perplexity's own description.
- The privacy policy permits using collected data to "Improve or create services and products, including our AI models." The only training carve-out written into it is email content.
- Brave reported it 25 July 2025 and, after the 20 August 2025 disclosure, said Perplexity "still hasn't fully mitigated the kind of attack described here." Two more things a careful buyer should know: the iOS App Store privacy label discloses precise location, purchase history and device identifiers collected and linked to your identity ; and there's real legal overhang, including copyright suits from several publishers and an Amazon suit over Comet's shopping agent that produced a March 2026 injunction blocking the agent from Amazon.

### `/vs/outlier-vs-poe/`
- Pick Outlier if what you paste in is confidential — client files, source code, medical or legal drafts — and "providers may receive the contents of your chats" is a non-starter; if you work where the network isn't; or if metered points make you edit yourself before you type.

### `/vs/outlier-vs-privategpt/`
- PrivateGPT publishes no hardware guidance — reasonably, since performance comes from whatever server you point it at, but "will this run well on my laptop?" then has no documented answer.

### `/vs/outlier-vs-qwen-chat/`
- The Privacy Policy says Qwen collects "your prompts and other content you upload, such as text, files, images, audio and videos," plus device ID, IP address and interaction data.
- For voice and video it notes this "involves the processing of data that may be considered biometric identifiers." Two clauses deserve a slow read.
- Training on your content is the default; the training-data summary says users can opt out "by submitting their requests to us" — a request to a company, not a switch in the app.
- Second, the Terms require a perpetual, irrevocable, sub-licensable, worldwide licence over user content and deem all of it "non-confidential and non-proprietary." That rules the product out for NDA-bound or client-confidential material.
- It describes encryption in transit and at rest and a security programme following "a standard industry framework," but names no certification.
- The "non-confidential and non-proprietary" clause and the default training use make Qwen Chat a poor fit there, and model quality doesn't fix it.

### `/vs/outlier-vs-sourcegraph-cody/`
- The page carries a badge reading "Supported on Sourcegraph Enterprise," and that badge is the whole story.
- Both install guides now list one prerequisite: "A Sourcegraph Enterprise account with Cody enabled." The clients are still maintained — VS Code v1.155.0 shipped 2026-06-17 with 868,377 installs and a 3.98/5 average.
- Documented clients are VS Code, JetBrains IDEs, Visual Studio (Experimental), the web app, and a CLI you install with npm install -g @sourcegraph/cody on Node.js v20+ — itself "in the Experimental stage for Enterprise accounts." No standalone desktop or mobile client appears in that list.
- One caveat: the only documented local-inference path is the Ollama page, which still says support is "available for Cody Free and Pro plans" — plans switched off a year ago.

### `/vs/outlier-vs-tabnine/`
- Seat price isn't the whole bill: reserved token consumption is charged "based on actual LLM provider prices + 5% handling fee," and usage is unlimited only if you deploy your own LLM on-premises or via your own endpoints.
- Sources and receipts: Tabnine plan prices, annual billing, the "actual LLM provider prices + 5% handling fee" charge and the Headless Agents add-on from tabnine.com/pricing ; the $5,800 Enterprise tier from context.tabnine.com/pricing ; architecture, deployment, models, privacy and telemetry, editor support and release notes from docs.tabnine.com ; zero-retention wording from tabnine.com/code-privacy .

### `/vs/outlier-vs-text-generation-webui/`
- TextGen's README describes it as "100% offline and private, with zero telemetry, external resources, or remote update requests," and there's no vendor account behind it, so there's nothing to opt out of.
- One counterweight, not a gotcha: v4.9 restricted CORS to localhost "to prevent drive-by API access" and closed a path-traversal vector, so earlier versions were exposed to a web page quietly calling your local API.

### `/vs/outlier-vs-zed-ai/`
- For "read forty files and refactor the call graph," cloud wins.
- Zed's May 2026 post on local AI says the hardware for frontier models at good speed is "out of reach for consumers," and flags smaller context windows and lower throughput.

### `/vs/qwen-vs-llama/`
- The Qwen3.6 repo says it plainly: "All our open-weight models are licensed under Apache 2.0." No user cap, no field-of-use restrictions, no naming rules, no attribution, no form.
- A scale cap: above 700 million monthly active users, you "must request a license from Meta, which Meta may grant to you in its sole discretion." An Acceptable Use Policy incorporated by reference, barring military, nuclear, espionage and weapons work, critical-infrastructure operation and unlicensed professional practice.
- Attribution: "prominently display 'Built with Llama'", and derived model names must begin with "Llama." The Open Source Initiative has said publicly that Meta's license doesn't meet the Open Source Definition, citing the commercial restriction and the field-of-use policy.

### `/vs/self-hosted-vs-on-device-ai/`
- Three servers cover most of the field. vLLM (Apache-2.0) calls itself "a fast and easy-to-use library for LLM inference and serving" and supports NVIDIA, AMD and Intel GPUs plus x86/ARM/PowerPC CPUs, with plugins for Google TPUs, Intel Gaudi and Huawei Ascend. llama.cpp (MIT) ships llama-server , "a lightweight, OpenAI API compatible, HTTP server for serving LLMs," spanning Metal, CUDA, HIP, Vulkan, SYCL and WebGPU, with 1.5-bit through 8-bit quantization and CPU+GPU hybrid inference to partially accelerate models larger than total VRAM.
- The lever that makes servers different in kind, not degree, is --tensor-parallel-size — vLLM's "number of tensor parallel groups." Splitting one model's weights across many GPUs is how a deployment holds something no single accelerator can.
- The launch post claimed "up to 24x higher throughput compared to HF and up to 3.5x higher throughput than TGI" — that's June 2023 against 2023 baselines, so treat it as directional, not current.
- You can answer "what did we ask the model last Tuesday" org-wide — genuinely impossible across a fleet of desktop installs.
- AWS's data-privacy FAQ says "we do not access or use your content for any purpose without your agreement," but that page doesn't explicitly address AI/ML training use — you'd confirm that in the service terms, and the answer differs per provider.
- RunPod bills per second "from when a worker starts until it fully stops," and Flex workers scale to zero — with a configurable idle timeout, default five seconds, that's still billed, plus a cold start on the next request.

### `/vs/unified-memory-vs-vram/`
- NVIDIA calls it "a memory-bound operation." That splits local inference into two problems.

---
## All remaining claims, by page

### `/vs/4-bit-vs-8-bit-quantization/` — 4-bit vs 8-bit quantization for local LLMs: which should you run?
- **[MONEY]** Free tiers: Nano 4B and Lite 9B.
- **[DATE/VERSION]** Matt Kerr · Outlier · published 2026-07-23 Updated 2026-07-23 Quick answer 4-bit is the right default for almost all local LLM work, and it's faster as well as smaller: on llama.cpp's Llama-3.1-8B numbers, Q4_K_M generates 71.93 tokens/sec from a 4.58 GiB file while Q8_0 manages 50.93 tokens/sec from 7.95 GiB.
- **[DATE/VERSION]** The scales stay at higher precision — which is where the naming goes fuzzy. llama.cpp publishes the real figures for Llama-3.1-8B: Q4_K_M is 4.8944 bits per weight (4.58 GiB), Q8_0 is 8.5008 bpw (7.95 GiB), F16 is 16.0005 bpw (14.96 GiB).
- **[DATE/VERSION]** Generation is memory-bandwidth-bound — every token streams the whole weight set through the compute units, so fewer bits means fewer bytes moved. llama.cpp's Llama-3.1-8B run, generation at 128 tokens: Q4_K_M 71.93 t/s, Q6_K 58.67 t/s, Q8_0 50.93 t/s, F16 29.17 t/s.
- **[DATE/VERSION]** Prefill runs the other way, because prompt processing is compute-bound: F16 923.49 t/s at 512 tokens, Q8_0 865.09, Q4_K_M 821.81.
- **[DATE/VERSION]** What you pay for it in quality The canonical numbers are llama.cpp's own quality table (LLaMA-7B), given as perplexity deltas against fp16: Q4_K_S +0.1149, Q4_K_M +0.0535 , Q5_K_M +0.0142, Q6_K +0.0044, Q8_0 +0.0004 .
- **[DATE/VERSION]** Q4_K_M, Q5_K_S and Q5_K_M are labeled "recommended." Q8_0 is marked not recommended — not because it's bad, but because it's overkill: Q6_K is already within 0.005 perplexity of fp16 at 1.5 GB less.
- **[DATE/VERSION]** A 2026 benchmark across 13 llama.cpp quant formats on Llama-3.1-8B-Instruct puts Q4_K_S at an average of 69.17 against Q8_0's 69.41, GSM8K 77.33 vs 77.48 — inside noise, at a 70.83% size reduction instead of 46.87%.
- **[DATE/VERSION]** LLM.int8() reports Int8 inference without performance degradation up to 175B parameters, routing emergent outlier dimensions through a 16-bit matmul while over 99.9% of compute stays in 8-bit.
- **[DATE/VERSION]** F16 Q8_0 Q6_K Q4_K_M Bits per weight 16.0005 8.5008 — 4.8944 File size (Llama-3.1-8B) 14.96 GiB 7.95 GiB — 4.58 GiB Generation, 128 tok 29.17 t/s 50.93 t/s 58.67 t/s 71.93 t/s Prompt processing, 512 tok 923.49 t/s 865.09 t/s — 821.81 t/s Perplexity delta (7B table) baseline +0.0004 +0.0044 +0.0535 llama.cpp's own label — not recommended — recommended Caveat: sizes and throughput come from the Llama-3.1-8B run, the perplexity deltas from an older LLaMA-7B table.
- **[DATE/VERSION]** Q6_K's 8B size isn't published; on 7B it's 5.15 GB against F16's 13.0 GB.
- **[DATE/VERSION]** Q4_K_M costs about +0.05 perplexity, takes a 13 GB 7B model to under 4 GB, and llama.cpp marks it recommended while calling 8-bit overkill.
- **[DATE/VERSION]** Ollama ships it as the silent default: llama3.1:latest and llama3.1:8b resolve to the same 4.9 GB artifact as llama3.1:8b-instruct-q4_K_M , identical digest.
- **[DATE/VERSION]** A 0.24-point average-score gap is compatible with a model that emits a plausible but nonexistent API name in generated code, and nobody has published a good measurement of 4-bit's effect on exact-symbol recall.
- **[DATE/VERSION]** 4-bit also sits close to a cliff: llama.cpp calls Q3_K_S "very high quality loss" (+0.5505) and Q2_K "not recommended" (+0.8698), so a vendor quietly shipping Q3 to save RAM is selling a materially different product.
- **[DATE/VERSION]** You can back the bit width out of the downloads: Nano is 4B in 2.37 GB, Core 27B in 15.13 GB — both near 4.5 bits per weight.
- **[DATE/VERSION]** What it buys, measured: Core 27B matched Claude Opus on 98.9% of rubric checks in a 54-prompt head-to-head , and scored about 45% on a blind slice of SWE-bench Verified.
- **[DATE/VERSION]** Q6_K measures +0.0044 perplexity, indistinguishable from fp16 on that metric, and still generates faster than 8-bit.
- **[DATE/VERSION]** Task scores: arXiv 2601.14277 , single-author preprint, not peer reviewed.
- **[DATE/VERSION]** Outlier figures measured on M1 Ultra, 2026-07-23.
- **[NUMBER]** On a 16 GB Mac it's the difference between a 20B-class model and nothing: gpt-oss-20b was post-trained with MXFP4 quantization of its MoE weights and is documented to run within 16 GB.

### `/vs/deepseek-vs-qwen/` — DeepSeek vs Qwen: open model families compared (2026)
- **[MONEY]** Side by side DeepSeek Qwen Open license MIT Apache 2.0 Open sizes 284B-A13B, 1.6T-A49B 0.8B, 2B, 4B, 9B, 27B, 35B-A3B, 122B-A10B, 397B-A17B Open context 1M tokens (both) 262K native on 3.6-27B, ~1.01M with YaRN Task strengths High-volume server inference, long context, MIT-licensed OCR and infra Coding at small sizes; open vision, audio, ASR, TTS, embeddings Languages Chinese and English first-class for both; neither publishes a per-language list I could verify 16 GB Mac No Yes &#8212; 0.8B to 9B 24&#8211;32 GB Mac No Yes &#8212; up to 27B dense / 35B-A3B 64 GB Mac Not practically Yes &#8212; 397B-A17B with SSD expert streaming Hosted price /1M v4-flash $0.14 in / $0.28 out; v4-pro $0.435 / $0.87 qwen3.7-plus $0.4 / $1.6; qwen3.7-max $2.5 / $7.5 (promo) Hosted data location People's Republic of China Singapore and Mainland China Training opt-out In-product toggle plus email route No documented toggle; DPO email only Where each family genuinely wins DeepSeek wins on license simplicity at the frontier.
- **[MONEY]** DeepSeek wins on hosted price, decisively. deepseek-v4-flash is $0.14 per million input tokens on a cache miss and $0.0028 on a cache hit, with $0.28 output &#8212; the cache-hit path is fifty times cheaper than the miss, which matters a great deal for workloads that repeat a long prefix. deepseek-v4-pro runs $0.435 / $0.003625 / $0.87 on the same axes.
- **[MONEY]** Alibaba's headline rates are limited-time discounts &#8212; 50% off qwen3.7-max, 20% off qwen3.7-plus &#8212; with no published end date, so budget for roughly double; the Qwen Code free tier ended 2026-04-15, and the new-user free quota is 90 days, Singapore region, real-time inference only.
- **[DATE/VERSION]** Apache 2.0 asks for attribution, a copy of the license, and adds an explicit patent grant; MIT asks for even less.
- **[DATE/VERSION]** For a downstream product, MIT and Apache 2.0 are the difference between "publish it" and "call a lawyer first." Sizes: a ladder versus two very large rungs Qwen's open line covers 0.8B, 2B, 4B, 9B, 27B, 35B-A3B, 122B-A10B and 397B-A17B, released in waves between February 16 and April 22, 2026.
- **[DATE/VERSION]** Qwen3.5-4B: 2.37 GB download, 6 GB RAM, 71.7 tok/s on an M1 Ultra and about 32 tok/s on an M4 MacBook Air.
- **[DATE/VERSION]** Qwen3.5-9B: 5.04 GB, 12 GB RAM, 53.4 tok/s.
- **[DATE/VERSION]** Qwen3.6-27B: 15.13 GB, 24 GB RAM, 20.7 tok/s.
- **[DATE/VERSION]** Qwen3.6-35B-A3B: 19.0 GB, 24 GB RAM.
- **[DATE/VERSION]** Qwen3.5-397B-A17B: a 209 GB download needing a 64 GB machine, running at 2.1 tok/s by streaming experts from SSD with paged MoE at roughly 11 GB peak RSS.
- **[DATE/VERSION]** Our Code tier &#8212; Qwen3.6-27B &#8212; measures 0.866 on HumanEval, and on a blind slice of SWE-bench Verified the local 27B came in around 45% (18 of 40).
- **[DATE/VERSION]** In a 54-prompt head-to-head against Claude Opus it matched the rubric on 98.9% of checks.
- **[DATE/VERSION]** Qwen Code, its Apache-2.0 terminal agent, deliberately speaks to "OpenAI, Anthropic, Gemini, and Qwen APIs.
- **[DATE/VERSION]** Pick Qwen if you need a model that fits consumer hardware, if Apache 2.0's patent grant matters to your legal team, if you want open vision or speech models rather than text alone, or if you want a desktop client today.
- **[DATE/VERSION]** MIT is marginally less paperwork than Apache 2.0, and both are far less than a vendor community license.
- **[DATE/VERSION]** Qwen's Apache 2.0 statement and release timeline from github.com/QwenLM/Qwen3.5 ; architecture from the Qwen3.6-27B model card; hosted pricing, model list and free quota from Alibaba Cloud Model Studio (Singapore); data location and training basis from qwen.ai/privacypolicy , updated 2026-05-19.
- **[DATE/VERSION]** Checked 2026-07-23 &#8212; competitor pricing, model names and privacy policies change often, and several rates above are labeled limited-time or subject to adjustment, so verify at the source before budgeting against them.
- **[POLICY]** Any third-party provider or local model (Ollama / vLLM)," and states it doesn't train on your prompts or code.
- **[POLICY]** Who should pick which Pick DeepSeek if you run server-side inference at volume and price per token dominates, if you want frontier-scale open weights and hardware to serve them, or if a documented training opt-out is something your compliance review looks for.
- **[POLICY]** Sources and receipts: DeepSeek pricing and the 2026/07/24 deprecation from api-docs.deepseek.com ; V4 parameter counts, context and the MIT license from the V4-Pro and V4-Flash model cards; data location, training use and opt-out wording from DeepSeek's privacy policy and terms of use.
- **[NUMBER]** The decisive difference is size: Qwen ships eight open sizes from 0.8B to 397B-A17B, while DeepSeek's open V4 line starts at 284B parameters and tops out at 1.6T.
- **[NUMBER]** Qwen3.6-27B is the interesting rung: dense, 64 layers, a hybrid Gated DeltaNet plus Gated Attention architecture, 262,144 tokens of native context extensible to roughly 1,010,000 via YaRN.
- **[NUMBER]** V4-Flash is 284B total with 13B activated, 1M token context, mixed FP4/FP8 with the MoE experts in FP4.
- **[NUMBER]** V4-Pro is 1.6T total with 49B activated and the same 1M context.
- **[NUMBER]** Outlier tier sizes, RAM floors and throughput measured on an M1 Ultra (64 GB) and an M4 MacBook Air; HumanEval, the SWE-bench slice and the 54-prompt comparison are our own runs on our own quantizations.

### `/vs/gemma-vs-llama/` — Gemma vs Llama: Google and Meta's open model families in 2026
- **[DATE/VERSION]** Google's Gemma 4 (2 April 2026) is Apache 2.0, ungated, and ships in five sizes topping out at 31B, so it fits ordinary Macs.
- **[DATE/VERSION]** I build Outlier, a local AI app for Mac, and it ships Qwen-family and Gemma-family weights: six tiers on Apache 2.0 Qwen checkpoints, one on Gemma-4-26B-a4b, none on Llama.
- **[DATE/VERSION]** Training data cuts off January 2025, so anything newer has to arrive through retrieval.
- **[DATE/VERSION]** There's no small Llama 4 and nothing newer either: Scout and Maverick landed on Hugging Face 1–3 April 2025, and no Llama 5 exists.
- **[DATE/VERSION]** Meta's April 2026 flagship, Muse Spark, ships as a private API preview with no weight download, and llama.com now redirects to Meta's developer site.
- **[DATE/VERSION]** Licensing: the difference that decides things Gemma 4 is Apache 2.0.
- **[DATE/VERSION]** Google moved the family off its custom terms on 2 April 2026.
- **[DATE/VERSION]** Every official Gemma 4 repository in Google's Hugging Face org is tagged license:apache-2.0 and isn't gated — no access request, no queue.
- **[DATE/VERSION]** Gemma 3 and earlier, plus variants like PaliGemma and FunctionGemma, stay under the custom Gemma Terms of Use (dated 1 April 2026), with a Prohibited Use Policy, redistribution notices, and an obligation to pass restrictions downstream.
- **[DATE/VERSION]** Side by side Gemma 4 (Google) Llama 4 (Meta) Latest open release 2 April 2026 1–3 April 2025, no successor Sizes E2B, E4B, 12B, 26B-A4B (MoE), 31B dense Scout 108.6B total / 17B active, plus Maverick License Apache 2.0 (Gemma 3 and earlier: Gemma Terms) Community License (source-available) Commercial conditions None beyond Apache 2.0 700M MAU ceiling, "Built with Llama," "Llama" name prefix EU developers No restriction Grant withheld for multimodal models Download Ungated Gated: terms plus request queue Languages 140+ pre-trained, per Google Multilingual; deepest fine-tune ecosystem Practical on a Mac Yes — day-one MLX 4-bit, official QAT int4 Not at Llama 4 sizes; Llama 3.x instead Strengths by task, and language coverage Gemma 4's edge is capability per gigabyte.
- **[DATE/VERSION]** Gemma 4 was Apple-silicon-ready immediately — MLX 4-bit conversions of E2B, E4B, 26B-A4B and 31B hit mlx-community on 2 April 2026, release day.
- **[DATE/VERSION]** Google also publishes quantization-aware-trained int4 GGUF builds (the 12B and 31B qat-q4_0-gguf repos, May–June 2026), and QAT holds quality better than naive post-hoc quantization.
- **[DATE/VERSION]** One number from my own build: Outlier's Quick tier is Gemma-4-26B-a4b-it, a 15.61 GB download with a 16 GB RAM floor.
- **[DATE/VERSION]** As of mid-2026 the popular mlx-community Llama conversions are all Llama 3.x (3.1 8B, 3.2 1B and 3B, 3.3 70B), with Llama 4 absent.
- **[DATE/VERSION]** Apache 2.0 from a frontier lab, ungated, with no user ceiling, no branding obligation, no naming rule and no geography clause, isn't a marginal improvement on Llama's terms — it's a different category of freedom.
- **[DATE/VERSION]** Go in knowing you adopt the license conditions along with the model, and that the open line has been quiet since April 2025.
- **[DATE/VERSION]** Sources and receipts: Gemma 4 sizes and modalities from deepmind.google and the 12B-it model card ; the Apache 2.0 move from the Google Open Source Blog ; older terms and output rights at ai.google.dev/gemma/terms ; runtimes from the Gemma docs ; hosted-tier handling from Gemini API pricing and terms .
- **[NUMBER]** The 12B instruction-tuned build is 11.95B parameters with a context window up to 256K tokens; it takes text, image, audio and video in and produces text only.
- **[NUMBER]** A roughly 12B model with a 256K context that ingests images, audio and video is a lot of surface area for something that fits on a laptop, and Google describes the family as pre-trained across more than 140 languages — well past what most locally-runnable models handle.
- **[NUMBER]** Llama 4 is a different story — 108.6B parameters is north of 50 GB at 4 bits before overhead.

### `/vs/gguf-vs-mlx-model-formats/` — GGUF vs MLX: how the two local model formats actually differ
- **[MONEY]** Free tier is Nano 4B and Lite 9B.
- **[DATE/VERSION]** The type table is where GGUF's reach shows: roughly forty tensor and quantization type codes, from F32, F16 and BF16 down through the Q*_K k-quants, the IQ* importance-matrix quants, ternary TQ1_0/TQ2_0, and MXFP4. llama.cpp advertises 1.5-bit through 8-bit integer quantization and ships an imatrix tool that computes an importance matrix over a text dataset to improve quantized quality.
- **[DATE/VERSION]** The hardware floor is real: Apple silicon, macOS 14.0 or later, native Python 3.10+.
- **[DATE/VERSION]** Side by side GGUF (via llama.cpp) MLX (via MLX LM) What it is Binary container format + GGML executors Array framework + safetensors weights Author Georgi Gerganov / ggml-org Apple machine learning research License MIT MIT Hardware Metal, CUDA, HIP, SYCL, Vulkan, WebGPU, OpenCL, CPU Apple silicon; also CUDA and CPU Linux builds OS floor None; Intel Macs fine macOS 14.0+, Apple silicon HF catalog 192,308 models tagged gguf 19,656 models tagged mlx Quantization ~40 type codes, 1.5–8 bit, imatrix calibration DWQ, AWQ, GPTQ, dynamic per-layer; cascadable Fine-tuning Not the primary path LoRA + full FT, distributed HTTP server llama-server , OpenAI-compatible mlx_lm.server , not for production Native app path Swift, Rust, Go, Node, Java, C# bindings MLX Swift for macOS and iOS Cost Free Free Where each one genuinely wins GGUF wins on reach, and it isn't close.
- **[DATE/VERSION]** The benchmark problem The most-cited head-to-head numbers come from Ollama, which moved its Apple silicon path onto MLX in preview on 2026-03-30.
- **[DATE/VERSION]** Their published figures, tested on M5 hardware: prefill 1,154 tok/s on 0.18 versus 1,810 on 0.19; decode 58 versus 112 tok/s.
- **[DATE/VERSION]** Version 0.18 ran a Q4_K_M GGUF and 0.19 ran NVFP4 through MLX — engine, version and quantization scheme all changed at once.
- **[DATE/VERSION]** Ollama has kept investing — a 2026-06-11 update added NVIDIA's NVFP4 4-bit format, up to 20% faster output through fused Metal kernels, and a snapshot system for agent workloads, with the claim that NVFP4 roughly halves the quality loss of 4-bit quantization relative to unquantized BF16.
- **[DATE/VERSION]** Hugging Face counts retrieved 2026-07-23; they move daily.
- **[NUMBER]** The preview also carried hard limits: a Mac with more than 32 GB of unified memory, and only one accelerated model at first.

### `/vs/grammarly-vs-local-ai/` — Grammarly vs local AI: what you give up, what you gain
- **[MONEY]** Free is $0: spelling and grammar correction, tone detection, 100 AI prompts a month.
- **[MONEY]** Pro is $30 per member per month, $60 quarterly, or $144 per year — that last figure is where the $12/month in the marketing comes from, an annual average rather than a month-to-month price.
- **[MONEY]** Nano and Lite are free; Pro is $20/month or $149/year, lifetime from $99.
- **[MONEY]** The free tier is real.
- **[MONEY]** Core correction and tone detection at $0, not a crippled demo.
- **[MONEY]** The free tiers work straight after download — no email, no usage history attached to an identity.
- **[MONEY]** Month to month it's $30 against $20.
- **[MONEY]** Annually it's $144 against $149 — Grammarly is five dollars cheaper and I won't pretend otherwise.
- **[MONEY]** Lifetime licenses from $99 change that past year one.
- **[DATE/VERSION]** What Grammarly actually is Grammarly checks grammar, spelling, clarity and tone and rewrites text, as an overlay that follows you around the machine: Mac (macOS 10.15+) and Windows apps, browser extensions, iPhone and Android keyboards, a web editor, Google Docs and Office integrations.
- **[DATE/VERSION]** Checked text goes to AWS servers in the United States: TLS 1.2 in transit, AES-256 at rest.
- **[DATE/VERSION]** Seven tiers, from Nano (4B, 2.37 GB, 6 GB RAM) through Core and Code 27B (15.13 GB, 24 GB RAM) to Plus 397B-a17b, which streams experts off the SSD and wants 64 GB.
- **[DATE/VERSION]** Not a chatbot pointed at prose — the output of a long grammatical-error-correction research program (GECToR is on their GitHub, Apache 2.0).
- **[DATE/VERSION]** Runs on any Mac back to macOS 10.15, including 8 GB Intel machines, with no download and no battery cost.
- **[DATE/VERSION]** What I have is a 54-prompt run against Claude Opus , where the local Core 27B matched on 98.9% of rubric checks and 100% on the nine hardest prompts, plus a blind slice of SWE-bench Verified at about 45%.
- **[DATE/VERSION]** Sources: plan features and limits from grammarly.com/plans ; pricing, the offline statement, hosting, retention and the training default from Grammarly's support articles and security page; AI subprocessors from superhuman.com/legal/subprocessors ; ISO/IEC 42001 from the April 2025 announcement.
- **[DATE/VERSION]** Checked 2026-07-23 — competitor pricing, limits and privacy defaults change; verify against Grammarly's pages.
- **[POLICY]** Grammarly says it uses aggregated, de-identified samples rather than raw documents, doesn't sell content, and bars its model providers from training on user text.
- **[POLICY]** No opt-out to hunt for, because there's no upload.
- **[NUMBER]** Outlier needs Apple Silicon and 6 GB of RAM minimum.
- **[NUMBER]** Who should pick which Pick Grammarly if you want correction everywhere you type without thinking about it; you write in more than one language or a non-American English variant; procurement needs certifications; you're on an Intel Mac, a PC, an 8 GB laptop or a phone; or your team needs shared style guides.

### `/vs/local-ai-vs-api-for-developers/` — Local AI vs a hosted LLM API: a developer's comparison
- **[MONEY]** The money, and the ceilings attached to it Claude API list pricing, per million tokens: Opus 4.8 $5 in / $25 out , Sonnet 5 $2/$10 introductory through August 31 2026, then $3/$15.
- **[MONEY]** OpenAI's list runs from gpt-5.6-sol at $5 input / $0.50 cached input / $30 output down to gpt-5.4-nano at $0.20/$0.02/$1.25.
- **[MONEY]** Batch takes 50% off both directions (Opus 4.8 becomes $2.50/$12.50) and stacks with caching.
- **[MONEY]** The other way: hosted web search adds $10 per 1,000 searches on top of tokens, and Anthropic's newer tokenizer (Opus 4.7+, Sonnet 5, Fable 5) emits roughly 30% more tokens for the same text — identical content costs more at an unchanged rate.
- **[MONEY]** Spend caps are $500 (Start), $1,000 (Build) and $200,000 (Scale): over a rate limit you get a 429 with retry-after, over the cap usage pauses until next month.
- **[MONEY]** Local inference has none of that arithmetic — though an idle API costs $0 and idle hardware doesn't.
- **[MONEY]** But that property belongs to the execution mode, not the brand — Ollama also sells hosted tiers ($20/month Pro, $100/month Max) processed server-side.
- **[MONEY]** Side by side Axis Local runtime Hosted API Cost model Hardware up front, ~$0 per token after Per MTok forever; batch 50% off, cache reads 0.1x Capability ceiling Bounded by RAM/VRAM Frontier scale, no local memory constraint Concurrency One box; vLLM batching for a team 10,000 RPM / 10M ITPM at Scale Data path Never leaves the machine Leaves it; no training by default, abuse logs ≤30 days Offline Yes No — latency floor, vendor availability Ops burden Quantization, context sizing, updates, packaging Vendor's Server-side extras Build them yourself Caching, batch, web search, code sandboxes Model lifecycle Frozen until you change it Vendor deprecates; retired IDs return 404 Where each genuinely wins The hosted API wins outright when… You need the capability ceiling.
- **[MONEY]** Free tier: Nano 4B and Lite 9B.
- **[DATE/VERSION]** What each one actually does A local runtime is a process on your machine that loads a quantized weights file into memory, runs the forward pass on whatever accelerator you have, and keeps the KV cache in your own RAM. llama.cpp is the substrate most of the ecosystem sits on — Metal on Apple Silicon, plus CUDA, HIP, SYCL, Vulkan and CPU paths, at quantizations from 1.5-bit to 8-bit.
- **[DATE/VERSION]** For scale: Outlier's largest tier, a 397B-A17B MoE, is a 209 GB download needing 64 GB of RAM, and manages 2.1 tok/s by streaming experts off the SSD.
- **[DATE/VERSION]** Tooling too: as of mid-2026 LM Studio's documentation publishes no open-source license for the desktop app itself, though it's been free at home and at work since July 2025.
- **[DATE/VERSION]** Any open-weight model, any quantization from 1.5-bit to 8-bit, custom fine-tunes and LoRAs, your own sampling.
- **[DATE/VERSION]** MIT/Apache runtimes plus Apache-2.0 weights means shipping commercially with no vendor relationship.
- **[DATE/VERSION]** Third-party pricing, limits and policies were current 2026-07-23 and change often — check the source first.
- **[POLICY]** Anthropic doesn't by default use commercial-product inputs or outputs for training, except what you submit as feedback or a bug report; OpenAI doesn't train on API data unless you opt in.
- **[POLICY]** It generates abuse-monitoring logs for all API usage, retained up to 30 days by default, and Zero Data Retention needs prior approval and isn't available on every endpoint ( /v1/conversations and /v1/assistants aren't eligible).
- **[NUMBER]** Start tier for Opus 4.x allows 1,000 requests, 2M input tokens and 400K output tokens per minute; Scale reaches 10,000 / 10M / 2M, and cache reads don't count toward the input limit on most models.
- **[NUMBER]** Where the hardware ceiling actually bites OpenAI's open-weight release states the limit cleanly: gpt-oss-120b (117B params, 5.1B active) fits on a single 80GB GPU, while only the much smaller gpt-oss-20b (21B, 3.6B active) is documented to run within 16GB — both via MXFP4 quantization of the MoE weights.
- **[NUMBER]** Scale tier reaches 10,000 requests/minute, Batch halves bulk work, idle costs nothing.
- **[NUMBER]** Outlier figures measured on an M1 Ultra (64 GB); my 54-prompt benchmark is self-published, so weigh it accordingly.

### `/vs/m1-vs-m4-for-local-ai/` — Apple M1 vs M4 for local AI: memory, bandwidth, and what actually fits
- **[MONEY]** M1 (2020) M4 (2024) M4 Pro M4 Max Max unified memory 16GB 32GB 64GB 128GB Memory bandwidth ~68GB/s (implied) 120GB/s 273GB/s up to 546GB/s GPU cores up to 8 10 up to 20 up to 40 7B Q4_0 prefill 117.96 tok/s 221.29 tok/s 439.78 tok/s 885.68 tok/s 7B Q4_0 generation 14.15 tok/s 24.11 tok/s 50.74 tok/s 83.06 tok/s Top Outlier tier that fits Lite 9B (Quick 26B-a4b at the 16GB ceiling) Core/Code 27B, Vision 35B-a3b Plus 397B-a17b Plus, with headroom Sold new by Apple No — used/refurb Yes, from $599 Yes, from $1,399 Yes Two caveats.
- **[MONEY]** The prices Apple publishes: Mac mini with M4 and 16GB at $599, Mac mini with M4 Pro at $1,399.
- **[MONEY]** That's roughly $37 per gigabyte of unified memory at the entry point, and it's the cheapest new Mac that runs mid-size models decently.
- **[MONEY]** Buying new on a budget: the $599 M4 Mac mini is a fair entry point, but spend the configure-to-order money on memory first — and compare current M5 machines before you commit.
- **[MONEY]** Serious about big models: you want M4 Pro or Max with 64GB or more, so $1,399 and up.
- **[DATE/VERSION]** Unified memory shipped in November 2020 and hasn't changed shape since, so a 16GB M1 holds a model that would otherwise need a 16GB card.
- **[DATE/VERSION]** In llama.cpp's community table (LLaMA 7B, Q4_0), M1 generates 14.15 tok/s and base M4 generates 24.11 — 1.70x.
- **[DATE/VERSION]** Prefill is the other half, and it's compute-bound, so GPU core count shows up: 117.96 tok/s on M1, 221.29 on M4, 439.78 on M4 Pro, 885.68 on M4 Max.
- **[DATE/VERSION]** In Outlier's tiers that's Lite 9B versus Core 27B, the tier that matched Claude Opus on 98.9% of rubric checks across a 54-prompt head-to-head .
- **[DATE/VERSION]** Outlier's Plus tier (397B-a17b, 209GB download) needs 64GB and streams experts from SSD to hold peak RSS near 11GB; it runs at 2.1 tok/s on my M1 Ultra — useful for hard problems, nobody's idea of chat.
- **[DATE/VERSION]** Outlier tier sizes and tok/s measured in-app on an M1 Ultra (64GB), July 2026.
- **[NUMBER]** Unified memory is why a Mac is in this conversation On a typical PC a model has to fit the graphics card's VRAM: 12GB card, 12GB budget, and the system RAM sitting next to it doesn't help.
- **[NUMBER]** M4 is a documented 120GB/s, a 1.76x ratio.
- **[NUMBER]** And 14 tok/s on a 7B model is faster than most people read.
- **[NUMBER]** Going from 16GB to 32GB (or 64, or 128) moves you out of "7-8B only" and into 13B-32B territory — a category change, not a percentage.
- **[NUMBER]** Who should pick which Already own a 16GB M1: keep it.
- **[NUMBER]** Own an 8GB M1: capacity is your wall and tuning won't move it.
- **[NUMBER]** Nano (2.37GB download, 6GB minimum) works; a 27B model never will.
- **[NUMBER]** Sources and receipts: Specs, ceilings and bandwidth from Apple Newsroom ( M1 , M4 , M4 Pro/Max , M5 ) and Apple's M1 MacBook Air tech specs ; the ~68GB/s M1 figure is implied by Apple's comparisons, not published.
- **[NUMBER]** ANE position from MLX issue #18 ; 8GB guidance from LM Studio .

### `/vs/mac-mini-vs-mac-studio-local-ai/` — Mac mini vs Mac Studio for local AI
- **[MONEY]** As of 23 July 2026 a Mac mini holds at most 48GB at 273GB/s (M4 Pro, from $1,599); a Mac Studio holds 36GB at 410GB/s from $2,499, 64GB at 546GB/s from $3,499, or 96GB at 819GB/s from $5,299.
- **[MONEY]** Side by side mini M4 mini M4 Pro Studio M4 Max Studio M3 Ultra Starting price $799 $1,599 $2,499 $5,299 Unified memory 16GB → 24GB 24GB → 48GB 36GB → 64GB (16/40 chip, $3,499) 96GB, not configurable Memory bandwidth 120GB/s 273GB/s 410 / 546GB/s 819GB/s GPU cores 10 16 or 20 32 or 40 60 or 80 Base storage 256GB 512GB 512GB 1TB Max continuous power 155W 155W 480W 480W Thunderbolt TB4 3× TB5 4× TB5 4× TB5 $ per GB, base config ~$50 ~$67 ~$69 ~$55 Largest Outlier tier Quick 26B-a4b Vision 35B-a3b Plus 397B-a17b at 64GB Plus 397B-a17b Upgradeable later No No No No Thermals, noise, and sustained load Inference is a sustained load, not a burst.
- **[MONEY]** Price per usable gigabyte — and the June price rise Divide starting price by base memory and the lineup isn't linear: roughly $50/GB for the $799 M4 mini, $67 for the $1,599 M4 Pro mini, $69 for the $2,499 M4 Max Studio, and — despite the sticker — about $55/GB for the $5,299 M3 Ultra, which also has the bandwidth to use those gigabytes.
- **[MONEY]** Apple's education price list carries a pricing date of 25 June 2026, dating a change: the mini started at $599 in October 2024, the Studio at $1,999 in March 2025.
- **[MONEY]** The $799 M4 mini is a real entry point — 16GB standard, a first-party ML stack in MLX, Metal and Core ML, and good third-party support across llama.cpp, Ollama and LM Studio.
- **[MONEY]** Who should pick which The $799 M4 Mac mini if you're finding out whether local AI fits your work.
- **[MONEY]** The M4 Max Mac Studio if the machine will be under sustained load — agent loops, batch jobs, video work alongside model work — or if you need 64GB, which requires the 16-core CPU / 40-core GPU configuration at $3,499.
- **[DATE/VERSION]** Every spec and price below came off Apple's own pages on 23 July 2026.
- **[DATE/VERSION]** 24GB (M4 mini upgraded, M4 Pro mini base): dense 27B models become practical — 15.13GB on disk, about 20.7 tok/s on an M1 Ultra.
- **[DATE/VERSION]** Outlier's 397B-a17b tier is a 209GB download that streams experts from SSD — about 2.1 tok/s, a batch speed rather than a conversational one.
- **[DATE/VERSION]** On my M1 Ultra a 4B model measures 71.7 tok/s; the same model measures 32 tok/s on an M4 MacBook Air.
- **[DATE/VERSION]** Apple's March 2025 announcement described configuring M3 Ultra up to 512GB and running models with over 600 billion parameters on device; the 128GB, 256GB and 512GB options are gone, as is the 64GB M4 Pro mini.
- **[DATE/VERSION]** Third-party reporting (MacRumors, May 2026) blames the DRAM shortage — I couldn't confirm that from a primary Apple source, only the resulting lineup.
- **[DATE/VERSION]** Apple shipped M5 Pro (up to 307GB/s, 64GB) and M5 Max (up to 614GB/s, 128GB) in the MacBook Pro in March 2026, claiming over 4× the peak GPU compute of M4 Pro for AI.
- **[DATE/VERSION]** The M3 Ultra Mac Studio only if 96GB at 819GB/s is the actual requirement; you're buying bandwidth on a chip announced in March 2025.
- **[DATE/VERSION]** Prices read from Apple's US buy flows for Mac mini and Mac Studio on 2026-07-23, cross-checked against Apple's US Education Institution Price List (pricing date 25 June 2026).
- **[DATE/VERSION]** The DRAM-shortage explanation is third-party reporting (MacRumors, May 2026), not primary-confirmed.
- **[NUMBER]** On the second, the spread is enormous: 120GB/s on M4, 273GB/s on M4 Pro, 410GB/s on M4 Max (546GB/s with the 16-core CPU / 40-core GPU chip), 819GB/s on M3 Ultra.
- **[NUMBER]** 16GB (base M4 mini): a 4B model is a 2.37GB download needing 6GB of RAM; a 9B model is 5.04GB needing 12GB.
- **[NUMBER]** A 26B MoE model at 15.61GB has a 16GB minimum — it runs, but that's the floor.
- **[NUMBER]** A 35B MoE vision model at 19.0GB also lands.
- **[NUMBER]** 64GB (M4 Max Studio, 16/40 chip only): the floor for very large paged-MoE models.
- **[NUMBER]** 96GB (M3 Ultra Studio): the same models with headroom, at 819GB/s instead of 410.
- **[NUMBER]** Neither is in a desktop — so you can order a MacBook Pro with 128GB today and no Mac Studio above 96GB.
- **[NUMBER]** For any model that fits inside a card's VRAM, expect more tokens per second there — so if your model fits in 24 or 32GB and speed is all you're buying, buy that instead.
- **[NUMBER]** Getting 96GB of GPU-addressable memory out of discrete cards means stacking them, with the power supply, chassis and noise that implies.
- **[NUMBER]** 819GB/s inside a 480W envelope has no direct consumer-PC equivalent at this size or noise level.
- **[NUMBER]** The M4 Pro Mac mini (24–48GB) if you know you want a 27B-class daily driver, quietly and cheaply.
- **[NUMBER]** 273GB/s is a real step up from 120, at less than half a Studio's entry price.
- **[NUMBER]** If your models fit in 48GB this isn't your machine, and if you needed 256GB, the machine you wanted isn't for sale.
- **[NUMBER]** The free Nano and Lite tiers need 6GB and 12GB of RAM, so you can test the premise before buying hardware.

### `/vs/mac-vs-nvidia-gpu-local-ai/` — Apple unified memory vs an NVIDIA RTX GPU for local LLMs
- **[MONEY]** The 5090 has 32GB of GDDR7 on a 512-bit interface, 1,792 GB/sec of bandwidth and 21,760 CUDA cores at $1,999; below it, 16GB on the 5080 ($999) and 5070 Ti ($749), 12GB on the 5070 ($549).
- **[MONEY]** Side by side Apple silicon (Mac Studio) NVIDIA GeForce RTX 50 Memory capacity 36–128GB (M4 Max); 96GB+ (M3 Ultra) 12 / 16 / 32GB (5070 / 5080 / 5090) Memory bandwidth 410 or 546 GB/s (M4 Max); 819 GB/s (M3 Ultra) 672 / 960 / 1,792 GB/s What fits at 4-bit Over 600B params per Apple Fine to ~30B; not 70B Throughput (7B Q4_0) ~714–1,240 prefill / ~70–94 gen ~14,000 prefill / ~290 gen (5090) Power envelope 480W max, whole machine 575W listed, card only Entry price From $1,999 (whole computer) $549–$1,999 (card only) Upgrade path None — soldered at purchase Swap or add cards; resale market Where the NVIDIA card genuinely wins Prompt processing isn't close, and it's the argument I'd lead with.
- **[MONEY]** DGX Spark pairs a 20-core Arm CPU with a Blackwell GPU over 128GB of coherent LPDDR5x at 273 GB/s on a 140W SoC; NVIDIA's marketplace has listed it at $4,699 — reported, not confirmed.
- **[MONEY]** On price, $1,999 buys either a complete Mac Studio with 36GB or one 5090 with 32GB: roughly $55 per gigabyte of unified memory versus $62 per gigabyte of VRAM plus a host.
- **[MONEY]** If the ~75% cap holds, Apple's effective number is nearer $74 per usable gigabyte.
- **[MONEY]** Tom's Hardware reported in March 2026 that Apple pulled the 512GB M3 Ultra option and raised the 256GB upgrade to $2,000; the same shortage reportedly pushed NVIDIA's SUPER refresh toward 2027.
- **[MONEY]** Who should pick which Pick an RTX card if your models fit in 32GB and speed is the point; if you fine-tune; if you need day-one support for new formats; if you're prototyping for cloud deployment; or if you own a PC and want the cheapest credible entry — a $549 card, not a whole machine.
- **[MONEY]** Sources and receipts: Apple bandwidth, memory ranges, 480W power, the 600B-parameter claim and the $1,999 start from apple.com/mac-studio/specs and Apple Newsroom (March 2025); GeForce specs and prices from NVIDIA's RTX 50 announcement.
- **[MONEY]** Not confirmed from primary sources: the 5090's 575W TGP, RTX PRO 6000 specs, DGX Spark's $4,699 price, GeForce's lack of NVLink, the ~75% macOS working-set cap (Apple Developer Forums) and the 512GB removal plus delayed SUPER refresh (Tom's Hardware).
- **[MONEY]** The free tier needs 6GB of RAM.
- **[DATE/VERSION]** The tier above flips it: Plus is 397B-a17b, a 209GB download that runs on a 64GB Mac by streaming experts off the SSD at about 11GB peak RSS — 2.1 tok/s, which is slow.
- **[DATE/VERSION]** From the Apple side, for scale: Core 27B runs at 20.7 tok/s on my M1 Ultra and Nano 4B hits 32 tok/s on an M4 MacBook Air — quicker than you read, with no fans audible.
- **[NUMBER]** Apple tops out at 819 GB/s; a 5090 moves 1,792 GB/s.
- **[NUMBER]** Community-submitted llama.cpp scoreboard results, all Llama 2 7B Q4_0, put a 5090 at roughly 14,000 tok/s prefill and 290 tok/s generation against about 1,240 / 94 on an M2 Ultra and 714 / 70 on an M4 Max — near 11x and 3x.
- **[NUMBER]** A 70B model at 4-bit is roughly 40GB of weights before any KV cache, so it doesn't fit in 32GB. llama.cpp will offload the overflow to system RAM over PCIe and throughput collapses.
- **[NUMBER]** Nano 4B, 2.37GB download, 6GB RAM; Lite 9B, 5.04GB / 12GB; Quick 26B-a4b, 15.61GB / 16GB; Core and Code 27B, 15.13GB / 24GB; Vision 35B-a3b, 19.0GB / 24GB.
- **[NUMBER]** All fit a 32GB 5090 and would run quicker there than on my M1 Ultra.
- **[NUMBER]** The math swings to Apple only above 32GB, where consumer GeForce has nothing to sell you — NVIDIA's answer is the RTX PRO 6000 Blackwell at 96GB and up to 600W: workstation money for one card.
- **[NUMBER]** Pick Apple silicon if you want models that don't fit in 32GB at all; if the machine is a laptop or sits where 575W of card is a non-starter; if you build or use native macOS software, since CUDA is licensed only for systems with NVIDIA GPUs.
- **[NUMBER]** Outlier figures measured on a 64GB M1 Ultra.

### `/vs/mac-vs-pc-for-local-ai/` — Mac vs PC for local AI: unified memory vs a discrete GPU
- **[MONEY]** Apple announced the M4 Max Mac Studio at $1,999 in March 2025 and the March 2026 MacBook Pro line from $2,199 to $3,899.
- **[MONEY]** Sources and receipts: Mac Studio bandwidth and the 480 W figure from apple.com/mac-studio/specs ; the 512 GB configuration and $1,999 start price from Apple's March 2025 newsroom post; M5 pricing and bandwidth from Apple's March 2026 MacBook Pro announcement.
- **[DATE/VERSION]** Apple's ML research team measured footprints on a 24 GB MacBook Pro — Qwen 8B is 17.46 GB at BF16 and 5.61 GB at 4-bit, Qwen 14B 4-bit is 9.16 GB, GPT-OSS 20B at MXFP4 is 12.08 GB, and a Qwen 30B MoE 4-bit is 17.31 GB.
- **[DATE/VERSION]** Nano (4B) is 2.37 GB and wants 6 GB of RAM; Lite (9B) 5.04 GB at 12 GB; Quick (26B-a4b) 15.61 GB at 16 GB; Core and Code (both 27B) 15.13 GB at 24 GB; Vision (35B-a3b) 19.0 GB at 24 GB; Plus (397B-a17b) is 209 GB on a 64 GB machine, paging MoE experts off the SSD at ~11 GB resident.
- **[DATE/VERSION]** M4 to M5 lifted bandwidth from 120 GB/s to 153 GB/s and produced time-to-first-token speedups of 3.33×–4.06×, but generation speedups of only 1.19×–1.27×.
- **[DATE/VERSION]** Call that 2.2× an M3 Ultra, 2.9× an M5 Max.
- **[DATE/VERSION]** The biggest practical advantage. vLLM treats CUDA, ROCm and Intel XPU as first-class; Apple Silicon lives in a separate plugin, vLLM-Metal, at v0.2.0 as of April 2026. bitsandbytes gives NVIDIA official support and calls Apple Silicon experimental — its macOS wheel is CPU-only.
- **[POLICY]** Training on your own data is well-trodden on the PC, newer on the Mac.
- **[NUMBER]** An RTX 5090 pairs 32 GB of VRAM with roughly 1,792 GB/s of bandwidth, so any model that fits generates tokens about 2–3× faster than on the highest-bandwidth Mac.
- **[NUMBER]** Apple says a Mac Studio can be configured up to 512 GB of unified memory, so it runs models that won't load on a consumer GPU at all — just more slowly.
- **[NUMBER]** No wall at 32 GB — and no 1,792 GB/s bus.
- **[NUMBER]** Against a 32 GB card, a 4-bit model up to about 30B is comfortable and quick; a 70B isn't.
- **[NUMBER]** Apple lists 410 GB/s for the 32-core M4 Max, 546 GB/s for the 40-core and 819 GB/s for M3 Ultra; on laptops, 307 GB/s for M5 Pro and 614 GB/s for M5 Max.
- **[NUMBER]** NVIDIA's GeForce news pages put the RTX 5090 at about 1,792 GB/s — the spec page omits it.
- **[NUMBER]** A third-party community suite puts an H100 at ~7,760 tokens/sec of prompt evaluation on Llama 3 8B against ~1,024 for an M2 Ultra, while generation was 144 vs 76.
- **[NUMBER]** Nor is there a real laptop equivalent: a discrete-GPU laptop with useful VRAM is heavy, loud and thermally limited, where a MacBook Pro carries 128 GB on battery.
- **[NUMBER]** But getting past 32 GB on the PC isn't cheap either.
- **[NUMBER]** NVIDIA's workstation documentation describes an RTX PRO 6000 Blackwell at 96 GB of GDDR7 with ECC at full bandwidth — capacity and bandwidth together, which no Mac matches, at a professional price.
- **[NUMBER]** NVIDIA's own unified-memory box, DGX Spark, has 128 GB but only 273 GB/s, below an entry M4 Max.
- **[NUMBER]** AMD documents the Ryzen AI Max+ 395 at 128 GB unified, 96 GB reassignable as VRAM.
- **[NUMBER]** Side by side Apple Silicon Mac PC + discrete GPU Memory model One unified CPU/GPU pool Separate fixed VRAM Capacity ceiling 512 GB (M3 Ultra); 128 GB laptop 32 GB (RTX 5090); 96 GB pro Bandwidth 307–819 GB/s ~1,792 GB/s (RTX 5090) What fits 4-bit 27B on 24 GB; 397B MoE on 64 GB 4-bit up to ~30B on 32 GB Sustained load 480 W whole machine 575 W card, 1,000 W PSU Price per usable GB Better above 32 GB Better below 32 GB Upgrade path None — soldered Swap GPU, add RAM or a card Laptop option Yes, on battery Heavy, loud, throttled Where the PC with a discrete GPU genuinely wins These advantages are real, and several are decisive.
- **[NUMBER]** 1,792 GB/s against 819 GB/s isn't close.
- **[NUMBER]** Who should pick which Build the PC if you want to fine-tune or train, you work with diffusion and video models, your models fit in 32 GB and you want maximum tokens per second, your workload is prefill-heavy, or local dev needs to mirror a Linux/CUDA production target.
- **[NUMBER]** RTX 5090 VRAM and 575 W from NVIDIA's product page; the ~1,792 GB/s figure is on NVIDIA's GeForce news pages, not the spec page.

### `/vs/macbook-air-vs-pro-local-ai/` — MacBook Air vs MacBook Pro for local AI: fanless vs actively cooled
- **[MONEY]** Roughly $69 per gigabyte at the 13-inch entry price is the cheapest way to get a GPU that can address 16–32GB of weights, in a silent 2.7-pound machine.
- **[MONEY]** A fanless $1,099 laptop pulling well under 20 watts while holding a 15GB model in memory the GPU reads directly is a trade no discrete card offers.
- **[DATE/VERSION]** Against Outlier's published tier minimums: 16GB Air (base): Nano 4B (2.37 GB, 6GB minimum) and Lite 9B (5.04 GB, 12GB) are comfortable; Quick 26B-a4b (15.61 GB, 16GB minimum) sits right at the line.
- **[DATE/VERSION]** My own numbers are narrower but measured: Outlier's Nano 4B runs 71.7 tok/s on an M1 Ultra desktop and 32 tok/s on an M4 MacBook Air, and Core 27B does 20.7 tok/s on the M1 Ultra.
- **[DATE/VERSION]** Sources and receipts: Memory ceilings and bandwidth from Apple's tech specs ( 126320 , 126318 ); pricing, fanless design, and AI multipliers from Apple Newsroom, March 2026 and October 2025; High Power Mode from Apple's Power Modes article; recommendedMaxWorkingSetSize from Apple's Metal docs.
- **[NUMBER]** The MacBook Air (M5) tops out at 32GB of unified memory at 153GB/s and is fanless; the MacBook Pro reaches 128GB at up to 614GB/s on the M5 Max, and it alone has High Power Mode.
- **[NUMBER]** Pro at 64GB: clears the floor for Plus 397B-a17b — a 209 GB download that pages experts off the SSD at ~11 GB peak RSS.
- **[NUMBER]** M5 also doubled base storage to 512GB, which matters when models run 15GB each.
- **[NUMBER]** 128GB at 614GB/s isn't matched by another laptop class, High Power Mode is a real user-accessible lever, and the bandwidth advantage shows up on every token.
- **[NUMBER]** Who should pick which Buy the MacBook Air if local AI is a daily tool rather than your whole job — 24GB or 32GB, 13- or 15-inch.
- **[NUMBER]** Don't buy the 16GB base if you care about this: memory is soldered, and it's the one decision you can't walk back.
- **[NUMBER]** Buy the M5 Pro if you want 64GB, keep long conversations open, or run agents for hours.
- **[NUMBER]** You get High Power Mode, 307GB/s, and the headroom to stay there.
- **[NUMBER]** Buy the M5 Max only if you need models above the 64GB line, and know 128GB requires the 40-core GPU part.
- **[NUMBER]** Ignore two things while deciding: battery ratings (Apple's 18–24 hour figures are video-streaming tests, not inference) and any tokens/second number quoted without a model, quantization, and context length.
- **[NUMBER]** Outlier tier sizes and tok/s measured on an M1 Ultra (64GB) and an M4 Air.
- **[NUMBER]** I couldn't confirm the 24GB/32GB Air upgrade prices from a primary source, so I haven't quoted one.
- **[NUMBER]** Nano and Lite are free forever and run fine on a 16GB Air.

### `/vs/mistral-vs-qwen/` — Mistral vs Qwen: the open model families compared
- **[MONEY]** No — OCR, Codestral, Moderation are premier No — qwen3.7-max is Model Studio only 16GB Mac Ministral 3 8B, 4-bit MLX, 5.6 GB 0.8B–9B (4B ≈ 2.4 GB, 9B ≈ 5.0 GB) 24–32GB Mac Nothing open between 14B and 119B Qwen3.6-27B, 4-bit MLX, ~16.1 GB Apple Silicon docs Community MLX; cards lead with vLLM mlx-lm and mlx-vlm in the official README Open agent CLI mistral-vibe — API key required Qwen Code — Ollama / vLLM supported Cheapest hosted Ministral 3 3B, $0.10 / $0.10 per 1M qwen3.5-flash, $0.10 / $0.40 per 1M Where each family genuinely wins Mistral wins on jurisdiction and on the small multimodal slot.
- **[MONEY]** Mistral is also more legible commercially — published per-model list prices (Small 4 at $0.15/$0.60, Large 3 at $0.50/$1.50, Medium 3.5 at $1.50/$7.50 per million tokens), a 50% batch discount, 90% off cached input, and clear consumer tiers at $14.99 and $24.99.
- **[DATE/VERSION]** Who ships what, and in what sizes Qwen's open catalogue is the wider of the two: Qwen3.6-27B and Qwen3.6-35B-A3B (April 2026), sitting on top of the Qwen3.5 line — 397B-A17B, 122B-A10B, 35B-A3B, 27B, then 9B, 4B, 2B and 0.8B, all released between February and April 2026.
- **[DATE/VERSION]** Mistral 3 (December 2025) brought Mistral Large 3 — 675B total, 41B active — plus Ministral 3 at 3B, 8B and 14B, each in base, instruct and reasoning variants.
- **[DATE/VERSION]** Mistral Small 4 followed in March 2026: 119B total, 6.5B active across 128 experts, 256k context.
- **[DATE/VERSION]** Licensing: the axis that decides what you can ship Qwen's repo says it flatly — all their open-weight models are Apache 2.0 — and the Qwen3.6-27B card carries the apache-2.0 tag.
- **[DATE/VERSION]** Mistral Small 4 and Ministral-3-8B-Instruct-2512 are Apache 2.0 on their cards too.
- **[DATE/VERSION]** And licensing is per-model, not per-vendor: as of mid-2026 some third-party write-ups describe one of Mistral's speech models as non-commercial rather than Apache 2.0.
- **[DATE/VERSION]** Community 4-bit MLX builds land immediately — mlx-community/Qwen3.6-27B-4bit is about 16.1 GB and runs from one mlx_lm.server command.
- **[DATE/VERSION]** MLX conversions come from the community instead, and they do arrive — 4-bit Ministral 3 8B is 5.6 GB — but each release is a wait.
- **[DATE/VERSION]** Ollama shows the same split: Qwen 3.5 and 3.6 are in the library, while the newest Mistral entries are mistral-medium-3.5 and mistral-large-3.
- **[DATE/VERSION]** In practice, on a 16GB Mac that 5.6 GB Ministral 3 8B fits with room for KV cache and is multimodal at 256k context — a genuinely good small-model story.
- **[DATE/VERSION]** Qwen's 4B and 9B fit the same slot; Outlier ships them at 2.37 GB and 5.04 GB.
- **[DATE/VERSION]** On 24-32GB, Qwen3.6-27B at 4-bit is the interesting option (our Core tier is that model, 15.13 GB, 24 GB minimum).
- **[DATE/VERSION]** Both vendors open-source a CLI coding agent under Apache 2.0, but Qwen Code points at local models via Ollama or vLLM and speaks the OpenAI, Anthropic and Gemini protocols, while the mistral-vibe README requires a Mistral API key and documents no local endpoint at all.
- **[DATE/VERSION]** Both do vision: Ministral 3 8B bundles a 0.4B encoder into a ~9B package, and Outlier's Vision tier is Qwen3.6-35B-A3B at 19.0 GB.
- **[DATE/VERSION]** Ministral 3 8B is a strong 16GB package: Apache 2.0, vision included, 256k context, 5.6 GB at 4-bit.
- **[DATE/VERSION]** Both also move fast enough to hurt: Qwen shipped 3.5, then 3.6, then a closed 3.7 in roughly six months; Mistral went Large 3 to Small 4 to Medium 3.5 in about four.
- **[DATE/VERSION]** They're both Apache 2.0 — nothing stops you running Ministral 3 8B for a fast multimodal path and a Qwen 27B for heavy reasoning inside the same product.
- **[DATE/VERSION]** My own choice is on the record: Outlier runs Qwen3.5-4B, Qwen3.5-9B, Gemma-4-26B-a4b-it, Qwen3.6-27B, Qwen3.6-35B-A3B and Qwen3.5-397B-A17B — six Apache 2.0, one under Gemma's terms.
- **[DATE/VERSION]** On our measurements the local 27B matched Claude Opus on 98.9% of rubric checks across a 54-prompt head-to-head and scored about 45% on a blind slice of SWE-bench Verified.
- **[DATE/VERSION]** Sources and receipts: Qwen sizes, the Apache 2.0 statement and MLX support from github.com/QwenLM/Qwen3.6 and the Qwen3.6-27B card ; 4-bit build sizes from mlx-community.
- **[DATE/VERSION]** Pricing from mistral.ai/pricing/api and Alibaba Cloud Model Studio (updated 2026-07-15, international deployment).
- **[NUMBER]** Mistral has nothing open in that band, and it's exactly the range a 24GB Mac can hold.
- **[NUMBER]** Mistral Small 4 will not fit 16GB at any useful quantization — 119B total is 119B total, even at 6.5B active.
- **[NUMBER]** Its sparse shape does flatter a 64GB machine, which is the same bet our Plus tier makes with Qwen3.5-397B-A17B: a 209 GB download that streams experts from SSD at roughly 11 GB peak RSS.
- **[NUMBER]** Strengths by task, and the language question Context favours Qwen at local sizes: Qwen3.6-27B is natively 262,144 tokens, extensible toward about 1,010,000 with RoPE scaling, against 256k for Mistral Small 4 and Ministral 3 8B.

### `/vs/mlx-vs-llama-cpp/` — Apple MLX vs llama.cpp: picking a local inference runtime on Mac
- **[DATE/VERSION]** Measuring MLX on an M5 MacBook Pro against a comparable M4 in November 2025, Apple saw time-to-first-token improve 3.33x–4.06x but token generation only 1.19x–1.27x, tracking the bandwidth jump from 120 GB/s to 153 GB/s.
- **[DATE/VERSION]** GGUF and MLX are not interchangeable llama.cpp uses GGUF, with integer quantization from 1.5-bit to 8-bit and conversion tooling in-tree.
- **[DATE/VERSION]** MLX uses its own format via mlx_lm.convert , defaulting to 4-bit, with nvfp4 added in v0.32.0.
- **[DATE/VERSION]** MLX's Python path needs native arm64 Python 3.10+ — Rosetta breaks it — so you're bundling a Python runtime inside a notarized .app unless you move to mlx-swift .
- **[DATE/VERSION]** Side by side Axis Apple MLX (+ mlx-lm) llama.cpp License / cost MIT, free MIT, free Hardware Apple silicon, macOS 14+; CUDA on Linux; no Intel Mac Metal, CUDA, HIP, Vulkan, SYCL, OpenCL, WebGPU, x86/ARM CPU Model format MLX-converted, 4-bit default, nvfp4 in v0.32.0 GGUF, 1.5-bit through 8-bit Model coverage Thousands of Hub models; conversion required, new archs lag 50+ families plus multimodal; usually first to a new model Serving Basic OpenAI-shaped server, explicitly not for production llama-server: auth, batching, slots, tools, KV reuse, web UI Native embedding mlx-swift for macOS/iOS/visionOS; Xcode needed for shaders libllama, zero deps, 30+ bindings; Swift path is bumpier Training LoRA and full fine-tuning, autodiff, distributed Inference-first Maturity v0.32.0, pre-1.0, API stability not promised build b10092 (2026-07-23), 5,000+ releases, no LTS branch Where each one genuinely wins MLX wins on Apple silicon throughput, and on being more than an inference engine.
- **[DATE/VERSION]** A reproducible third-party suite (apple-silicon-llm-bench) reports MLX-Swift ahead on decode for small and mid-size models on an M4 Max: Qwen 2.5 0.5B at 531 vs 297 tok/s, Qwen 3.5 2B at 292 vs 150, Gemma 4 E2B at 185 vs 119.
- **[DATE/VERSION]** Ollama's March 2026 numbers after moving its Apple path to MLX show decode 112 vs 58 tok/s on Qwen3.5-35B-A3B in NVFP4, with its own caveats: preview build, more than 32 GB of unified memory, few models supported.
- **[DATE/VERSION]** LM Studio's docs describe shipping llama.cpp variants alongside an Apple-silicon-only MLX engine, and Ollama went MLX-first then, per its June 2026 post, brought GGUF back through llama.cpp for breadth.
- **[DATE/VERSION]** M5-vs-M4 figures from Apple Machine Learning Research (2025-11-19).
- **[DATE/VERSION]** Ollama figures from ollama.com/blog/mlx (tested 2026-03-29, preview build); independent decode numbers from apple-silicon-llm-bench .
- **[DATE/VERSION]** Release state checked 2026-07-23.
- **[NUMBER]** MLX gave me room to build what isn't in either runtime: the Plus tier is a 397B-a17b MoE streaming experts from SSD at roughly 11 GB peak RSS, which needed paging control no general-purpose engine hands you.

### `/vs/notion-ai-vs-local-ai/` — Notion AI vs local AI: what you give up, what you gain
- **[MONEY]** These are adjacent categories — one is a workspace feature, the other is a model on your laptop — and people compare them mostly because both land around $20 a month.
- **[MONEY]** There's no standalone AI add-on on the current pricing page, so the entry price is Business, listed at $20 per member per month, times every seat.
- **[MONEY]** Nano and Lite are free with no account; Pro is $20/month or $149/year.
- **[MONEY]** Side by side Notion AI Outlier Where inference runs Notion-hosted and third-party provider infrastructure Your Mac's GPU Models GPT-5.2, Opus 4.5/4.8, Gemini 3, Grok 4.3, GLM 5.2, Auto Qwen3.5/3.6 and Gemma-4, 4B to 397B-a17b What it can see Your workspace, plus Slack, Drive, GitHub, Outlook, Box Only what you put in the conversation Entry price for AI Business, listed $20/member/month; Free and Plus get a trial allowance Free (Nano + Lite), or $20/mo · $149/yr per person Usage-based cost Custom Agent credits at $10 per 1,000; Workers billed from Oct 15, 2026 None Offline Pages yes; no AI feature documented as offline-capable Fully offline after the download Collaboration Shared pages, assignable and scheduled agents None — one user, one machine Platforms macOS 12+, Windows 10 21H2+, iOS 17+, Android 8+, web; no Linux app listed Apple Silicon Macs only Compliance SOC 2 Type 2, ISO 27001/27701/27017/27018, BSI C5, HIPAA with a BAA (Enterprise) Not applicable — nothing processed off-device Where Notion AI is clearly better This section isn't a formality.
- **[MONEY]** Notion AI comes with Business, but the automation layer is metered on top: Custom Agents have consumed Notion Credits since May 4, 2026 at $10 per 1,000, and Workers begin requiring credits on October 15, 2026 at roughly $0.0023 per run.
- **[MONEY]** Notion's own per-run estimates span a 10× range — about $0.03–$0.11 for a Q&A agent up to $0.10–$0.30 for a daily brief — because cost scales with content read, steps, frequency, and model.
- **[MONEY]** One daily-brief agent works out to $3–$9 a month on top of seats.
- **[DATE/VERSION]** As of the 3.6 release on July 1, 2026 you can pick GPT-5.2, Claude Opus 4.5 or 4.8, Gemini 3, Grok 4.3, or the open-weight GLM 5.2 — or let "Auto" route per task — and switch without losing workspace context.
- **[DATE/VERSION]** Seven tiers run from Nano (4B, 2.37 GB, fits in 6 GB of RAM) to Plus (397B-a17b, 209 GB on disk, streaming experts from SSD at about 11 GB peak RSS).
- **[DATE/VERSION]** A quantized 27B on a laptop doesn't match Claude Opus 4.8 or GPT-5.2 on the hardest reasoning.
- **[DATE/VERSION]** In a 54-prompt head-to-head against Claude Opus , Outlier's Core 27B matched on 98.9% of rubric checks, including all nine of the hardest prompts.
- **[DATE/VERSION]** Sources and receipts: Notion figures come from Notion's own pages, read July 2026 — notion.com/pricing and the Notion AI FAQ for tiers and availability, notion.com/help/notion-ai-security-practices for inference, training, and retention, the Custom Agents and Workers pricing pages for credits, the 3.6 release notes (2026-07-01) for models, and notion.com/help plus notion.com/security for platforms, offline behavior, and compliance.
- **[POLICY]** By default neither Notion nor its AI subprocessors use customer data to train models, and Notion says its contracts prohibit it; training is opt-in through a program called AI LEAP.
- **[POLICY]** Notion's default of not training on customer data is a policy backed by contracts, and I've no reason to doubt it — but it's still a promise about what a third party does with content you sent them.
- **[NUMBER]** Retention diverges by tier — zero data retention with providers on Enterprise, 30 days or fewer below it — and some features can use data-retaining LLMs, off by default, which an admin can turn on workspace-wide.
- **[NUMBER]** That stops being philosophical when you're handling an unsigned deal, a patient note, or a client's source code, and it matters more below Enterprise, where Notion's own docs put provider retention at up to 30 days rather than zero.

### `/vs/otter-ai-alternative-local/` — Otter.ai alternative: doing meeting notes locally on a Mac
- **[MONEY]** As of July 2026: Basic $0, Pro $16.99/user/month monthly or $8.33 annually, Business $30 or $19.99 annually, Enterprise custom.
- **[MONEY]** API and webhooks are Enterprise-only, SSO/SCIM is listed as needing a 100-user minimum, HIPAA is an Enterprise add-on, and an Otter MCP server is included from the free plan up.
- **[MONEY]** Nano and Lite are free; Pro is $20/month or $149/year, with lifetime licenses from $99.
- **[MONEY]** Side by side Otter.ai Outlier Where processing happens Otter's servers (AWS S3) Your Mac, always Records / joins meetings Yes — Zoom, Meet, Teams; bot-free on desktop No Speech-to-text Yes, live, speaker labels, six languages No — bring your own transcript Summaries, action items Yes, automatic Yes, from pasted text Search across past meetings Yes — AI Chat over the corpus No index; one document at a time Cost $0 / $8.33–16.99 / $19.99–30 per user/mo Free tier; $20/mo or $149/yr; lifetime from $99 Usage caps 300 min/mo free, 1,200 Pro; unlimited from Business None Works offline No Yes Account required Yes No Vendor trains on your data Policy describes training on de-identified audio Nothing is uploaded Teams and admin Workspaces, permissions, SSO/SCIM, retention No Platforms Web, macOS, Windows, iOS, Android, Chrome Apple Silicon Macs only Auditability Closed source; ToS bars reverse engineering Weights published on Hugging Face Where Otter genuinely wins These aren't reluctant concessions.
- **[MONEY]** AI Chat queries every meeting you've had, not one file at a time, and results flow into Salesforce, HubSpot, Slack, Jira, Notion and Google Workspace, an Enterprise REST API, and a hosted MCP server available even on the free plan.
- **[DATE/VERSION]** Its bot joins Zoom, Google Meet and Microsoft Teams from your calendar — including meetings you skip — and the Mac/Windows desktop app, announced in October 2025, can record bot-free instead of sending a bot into the call.
- **[DATE/VERSION]** You also stop metering, and the summarizing holds up: on a 54-prompt head-to-head, Core 27B matched Claude Opus on 98.9% of rubric checks .
- **[DATE/VERSION]** All read July 2026; promotions were running, so displayed prices may sit below list.
- **[POLICY]** Otter says it de-identifies first, and that human review of audio requires explicit customer consent.
- **[POLICY]** On the primary pages I could read, I found no described self-serve opt-out from Otter training on your de-identified recordings; the opt-outs the policy describes cover sale/sharing and targeted advertising.
- **[POLICY]** Otter's own ASR and speaker-ID models are trained on enormous volumes of meeting audio across six languages and a wide accent range.

### `/vs/outlier-vs-aider/` — Outlier vs Aider: on-device Mac app vs terminal AI pair programmer
- **[MONEY]** Nano and Lite are free; Pro is $20/month or $149/year and enables all seven.
- **[MONEY]** Pro $20/mo or $149/yr.
- **[MONEY]** Aider's board publishes dollar cost per run too, which is the counterweight: $29.08 for that 225-exercise benchmark on gpt-5 (high), $146.32 on o3-pro (high).
- **[DATE/VERSION]** What Aider actually is Aider is a terminal pair programmer from Aider AI LLC, open source under Apache 2.0.
- **[DATE/VERSION]** Seven tiers: Nano 4B (2.37 GB), Lite 9B, Quick 26B-a4b, Core 27B, Code 27B, Vision 35B-a3b, and Plus 397B-a17b (209 GB, streamed from SSD by a paged MoE loader at roughly 11 GB peak RSS).
- **[DATE/VERSION]** What the coding numbers actually say Our real measurements, not a leaderboard boast: on a blind slice of SWE-bench Verified, the local 27B measured about 45% (18 of 40) , and Code 27B scores 0.866 on HumanEval .
- **[DATE/VERSION]** Core 27B also matched Claude Opus on 98.9% of rubric checks across a 54-prompt head-to-head .
- **[DATE/VERSION]** For the ceiling: Aider publishes its own polyglot benchmark — 225 Exercism exercises across C++, Go, Java, JavaScript, Python, and Rust — with gpt-5 (high) topping the board at 88.0%.
- **[DATE/VERSION]** Apache 2.0, with the agent loop and prompts readable in the repo — forkable, auditable, and you can see exactly what gets sent.
- **[DATE/VERSION]** The last tagged release is v0.86.0 (2025-08-09), the newest PyPI upload 0.86.2 (2026-02-12), the most recent commit to main 2026-05-22, against 1,756 open issues.
- **[DATE/VERSION]** Commits continue and the repo isn't archived, but the polyglot leaderboard's newest dated entry is 2025-10-03, the README still recommends a mid-2025 model set, and there's no documented Model Context Protocol support.
- **[DATE/VERSION]** Sources and receipts: Aider details from aider.chat/docs — install, LLM support, repo map, Ollama notes, browser UI, analytics, and privacy policy (Aider AI LLC, last updated 2025-04-12) — plus the polyglot leaderboard , the GitHub repo and API metadata, and PyPI package metadata for aider-chat , all checked 2026-07-23.
- **[DATE/VERSION]** Outlier tier sizes, throughput, and the ~11 GB Plus peak RSS measured on an M1 Ultra Mac Studio; SWE-bench Verified slice (18/40) and HumanEval 0.866 are our own internal runs, not third-party leaderboard results.
- **[POLICY]** No git integration Repo-scale context Tree-sitter repo map of files and key symbols, graph-ranked and fitted to a token budget (default --map-tokens 1k ), plus files you add Whatever you paste or attach in a conversation Telemetry Opt-in analytics; never collects code, chat, or keys.
- **[POLICY]** Permanent opt-out: aider --analytics-disable None to opt out of — the model runs locally Does your code leave the machine?
- **[POLICY]** Aider's privacy policy (Aider AI LLC, last updated April 12, 2025) covers device, usage, and analytics info; it says nothing about training on your inputs, and it wouldn't, because Aider doesn't operate a model.
- **[NUMBER]** 47.6k GitHub stars, roughly 6.8M PyPI installs, ~15B tokens/week, a top-20 spot on OpenRouter, and 88% of the last release's new code written by Aider itself.

### `/vs/outlier-vs-anythingllm/` — Outlier vs AnythingLLM: bundled Mac app vs open-source model-agnostic shell
- **[MONEY]** Nano and Lite are free; Pro is $20/month or $149/year.
- **[MONEY]** Side-by-side AnythingLLM Outlier Interface Desktop GUI, Docker server, cloud web UI, Android, browser extension, REST API Mac desktop GUI only Who it's for Tinkerers, developers, teams — and end users on desktop Mac end users Setup effort One-click desktop install; Docker/cloud need real configuration Install and open Model management You choose: 20+ providers, local or cloud, 9 vector DBs Seven fixed local tiers, no provider settings Bundled vs assembled Assembled — no model of its own; desktop adds a downloader Bundled — models, runtime and app ship together Platform support macOS (Apple Silicon + Intel), Windows x64/ARM, Linux, Docker, Android Apple Silicon Macs only License MIT, open source Proprietary app; model weights published on Hugging Face Price Desktop and Docker free; cloud $50 or $99/mo; a paid desktop Pro tier exists, price not in the docs Free tier (Nano + Lite); Pro $20/mo or $149/yr Data leaves the device No on desktop by default (telemetry on unless disabled); yes if you connect a cloud provider No Where AnythingLLM genuinely wins Several of these aren't close, and pretending otherwise would waste your time.
- **[MONEY]** AnythingLLM Cloud has no built-in LLM by design — the hosted instance has no GPU and limited CPU and RAM — so $50 or $99 a month buys hosting, with model API costs on top; cloud also drops custom agents and MCP for security reasons.
- **[DATE/VERSION]** The difference in posture is that Outlier ships the models: seven tiers from Nano (4B, 2.37 GB, 6 GB RAM, 71.7 tok/s on M1 Ultra) through Core and Code 27B up to Plus, a 397B-a17b MoE streaming experts from SSD in ~11 GB peak RSS.
- **[DATE/VERSION]** The v1.13.0 Model Router goes further, mixing local and cloud models inside one conversation by rules — a thoughtful way to keep sensitive traffic local and escalate only hard queries.
- **[DATE/VERSION]** Roughly 63.7k GitHub stars, monthly releases (v1.15.0 on 2026-06-25), commits the same week I wrote this.
- **[DATE/VERSION]** And since v1.15.0 the desktop app's on-device "Magic Features" (system-wide dictation, highlight-to-act, predictive typing) carry free daily limits, with Pro removing them and the watermark on AI-generated documents.
- **[DATE/VERSION]** On measured quality, Core 27B matched Claude Opus on 98.9% of rubric checks across a 54-prompt head-to-head and 100% on the nine hardest prompts; Code 27B scores 0.866 on HumanEval, and on a blind slice of SWE-bench Verified the local 27B measured about 45%.
- **[DATE/VERSION]** Sources and receipts: license, stars and releases from github.com/Mintplex-Labs/anything-llm and the GitHub API (read 2026-07-23); builds and the account-free install from anythingllm.com/download ; cloud pricing and the no-built-in-LLM limitation from anythingllm.com/cloud and its limitations page ; desktop-vs-Docker availability, telemetry defaults and system requirements from docs.anythingllm.com; Magic Features and Pro from the v1.15.0 notes .

### `/vs/outlier-vs-cline/` — Outlier vs Cline: on-device Mac app vs open-source VS Code agent
- **[MONEY]** Outlier's free tier is Nano (4B) and Lite (9B), no account, no caps; Pro is $20/month or $149/year for all seven tiers, lifetime from $99.
- **[MONEY]** ClinePass $4.99 then $9.99/mo.
- **[MONEY]** Free tier (Nano + Lite).
- **[MONEY]** Pro $20/mo or $149/yr, lifetime from $99.
- **[MONEY]** The $6.80 figure is user-reported in issue #7558, not a vendor statement.
- **[DATE/VERSION]** Six Apache 2.0, one Gemma Terms.
- **[DATE/VERSION]** On a blind slice of SWE-bench Verified the local 27B measured about 45% (18 of 40) , and it scores 0.866 on HumanEval.
- **[DATE/VERSION]** Core 27B did match Claude Opus on 98.9% of rubric checks in a 54-prompt head-to-head — but that's answer quality, not agentic issue-resolution.
- **[DATE/VERSION]** Apache 2.0, whole client, auth and data handling included — readable, auditable, forkable.
- **[DATE/VERSION]** Sources and receipts: Cline claims verified against cline.bot/pricing , cline.bot/cline-pass , cline.bot/privacy , cline.bot/tos (both effective September 2025), docs.cline.bot , github.com/cline/cline , and the VS Code Marketplace listing (4,743,250 installs, v4.0.10).
- **[DATE/VERSION]** Outlier tier specs, the SWE-bench Verified slice (18/40) and HumanEval 0.866 were measured by me on an M1 Ultra Mac Studio.

### `/vs/outlier-vs-continue-dev/` — Outlier vs Continue.dev: local Mac AI vs an open-source coding agent
- **[MONEY]** Snapshotted 2026-06-03: Starter at $3 per million tokens in and out; Team at $20 per seat per month with $10 of credits and SSO; Company at custom pricing with SAML/OIDC, BYOK and an SLA.
- **[MONEY]** Outlier is free on Nano and Lite; Pro is $20/month or $149/year for all seven tiers.
- **[MONEY]** Works with Wi-Fi off Cost Free (Apache-2.0); you pay your provider Free tier; Pro $20/mo or $149/yr Agentic ability Inherited from your model ~45% on a blind SWE-bench Verified slice Repo-scale context Your backend's context window Tier and Mac RAM (24 GB for Code 27B) Maintenance Read-only, ~935 open issues, no patches Actively shipping Agentic ability, repo context, and my honest numbers On a blind slice of SWE-bench Verified — real repositories, real issues, an agent that reads code, edits files and runs tests — Outlier's local 27B measured about 45%, or 18 of 40 .
- **[DATE/VERSION]** It ships no model, so whether your code leaves the machine depends on the backend you configure — and after Cursor acquired Continue Dev, Inc. in June 2026, the hosted hub is off and the repository calls itself read-only and no longer maintained.
- **[DATE/VERSION]** The license is Apache-2.0.
- **[DATE/VERSION]** VS Code v2.0.0 and v2.1.0 both landed 2026-06-19; the CLI ended at 1.5.47; JetBrains last shipped v1.0.67 on 2026-03-27. hub.continue.dev no longer resolves in DNS.
- **[DATE/VERSION]** Seven tiers, from Nano 4B (2.37 GB, 6 GB RAM, 71.7 tok/s on my M1 Ultra) through Code 27B (15.13 GB, 24 GB RAM) to Plus 397B-a17b, which streams MoE experts from SSD.
- **[DATE/VERSION]** Six tiers are Apache 2.0 weights; Quick is Gemma Terms of Use.
- **[DATE/VERSION]** One gap worth naming: the privacy policy, updated 2026-02-05, says you aren't required to provide personal data to use the open-source software — but it never states whether user code is used for training, and no opt-out is documented.
- **[DATE/VERSION]** Code 27B scores 0.866 on HumanEval .
- **[DATE/VERSION]** Apache-2.0 — fork it, relicense it, ship it.
- **[DATE/VERSION]** And the final 2.0.0, stripped of telemetry and auth, is a clean fork base.
- **[DATE/VERSION]** Two asterisks: the VS Code Marketplace average is a modest 3.31 across 176 ratings, and the docs still present Continue as actively maintained, contradicting the homepage and README.
- **[DATE/VERSION]** Apache-2.0 means a maintained fork can exist — but that's now a problem with your name on it.
- **[DATE/VERSION]** Sources and receipts: Continue's status, license and release dates from continue.dev , the continuedev/continue README and GitHub API, and npm , retrieved July 2026.
- **[DATE/VERSION]** Continue pricing is an archived 2026-06-03 snapshot from before the acquisition, no longer purchasable.
- **[DATE/VERSION]** Outlier tier sizes and throughput measured on an M1 Ultra Mac Studio; HumanEval 0.866 and the ~45% (18/40) blind SWE-bench Verified slice measured in-house, not leaderboard submissions; more in the 54-prompt head-to-head .
- **[NUMBER]** The code survives: the repo isn't archived, and still shows ~35,000 stars and 5,100 forks.
- **[NUMBER]** Which model powers it is whatever you configured; Continue's Ollama guide points at open-weight options like Qwen2.5-Coder, DeepSeek-Coder 6.7B and DeepSeek-R1 32B, budgeting about 32 GB of RAM for a 32B.
- **[NUMBER]** I measured both on my own hardware; they aren't leaderboard placements; read them as a floor for what a 15 GB model on a laptop can do.

### `/vs/outlier-vs-deepseek-app/` — Outlier vs the DeepSeek app: local Mac AI vs a free cloud chat service
- **[MONEY]** Outlier's paid tier competes against $0.
- **[MONEY]** V4-Flash costs $0.14 per million input tokens on a cache miss and $0.28 output; V4-Pro, $0.435 and $0.87 — OpenAI-compatible, with an Anthropic-compatible endpoint too.
- **[MONEY]** A million input plus a million output tokens comes to about $0.42 on V4-Flash and $1.31 on V4-Pro, with cache hits dropping input to $0.0028 and $0.003625 per million.
- **[MONEY]** Pro is $20/month or $149/year for all seven tiers; lifetime Pro starts at $99.
- **[DATE/VERSION]** Outlier runs the model on your own Apple Silicon Mac — no account, no caps, works offline, nothing uploaded — but it has no web search, no mobile app, and can't host anything near DeepSeek's 1.6-trillion-parameter V4-Pro.
- **[DATE/VERSION]** The iOS listing, "DeepSeek - AI Assistant," is marked Free with no in-app purchases , needs iOS 15.0 or later, and supports iPhone, iPad and iPod touch only.
- **[DATE/VERSION]** NIST's Center for AI Standards and Innovation put V4-Pro at an IRT-estimated Elo of 800 against GPT-5.4 mini's 749 across nine benchmarks, and more cost efficient on 5 of 7.
- **[DATE/VERSION]** Seven tiers ship, from Nano 4B (2.37 GB, 6 GB RAM, 71.7 tok/s on an M1 Ultra) through Core 27B up to Plus 397B-a17b, which pages MoE experts off the SSD at roughly 11 GB peak RSS.
- **[DATE/VERSION]** On quality: Core 27B matched Claude Opus on 98.9% of rubric checks across a 54-prompt head-to-head , and 100% on the nine hardest.
- **[DATE/VERSION]** Wiz Research found an exposed, unauthenticated database in January 2025 holding over a million entries including chat messages and API keys; South Korea's data-protection commission later found undisclosed transfers of over a million users' data.
- **[DATE/VERSION]** Sources and receipts: Surfaces from deepseek.com ; iOS details from the App Store (v2.2.2, July 11, 2026); pricing, concurrency and the July 24, 2026 deprecation from api-docs.deepseek.com ; V4 parameters and MIT licensing from Hugging Face; absent client repos from the deepseek-ai org ; data handling from DeepSeek's privacy policy (2026-02-10), Terms of Use (2026-03-27) and Open Platform Terms (2026-04-29); benchmarks from NIST CAISI .
- **[DATE/VERSION]** Outlier specs measured on an M1 Ultra, 2026-07-23.
- **[POLICY]** Outlier's half is short: the model runs locally, nothing is transmitted, there's no account to attach a history to, and no opt-out because there's no collection.
- **[NUMBER]** DeepSeek says 1M context is the default across all official services, with 384K max output.
- **[NUMBER]** 1.6T total parameters won't fit in 64 GB of unified memory at any quantization I'd ship, and a million tokens of context is the default on every official surface — no Mac holds that much KV cache.
- **[NUMBER]** Nothing to download or manage, history syncs across devices, same behavior on an 8 GB laptop or a borrowed browser.

### `/vs/outlier-vs-enchanted/` — Outlier vs Enchanted: bundled Mac app vs open-source Ollama client
- **[MONEY]** Side by side Enchanted Outlier Interface Native GUI client only; no CLI, no web UI Native GUI app; no CLI, no web UI Who it's for Developers, tinkerers, LLM researchers (per its own App Store listing) End users who want a chat app with nothing to assemble Setup effort Install and run Ollama separately, then point the app at it Download app, pick a tier, it fetches the weights Model management Whatever your Ollama has pulled; you manage it via Ollama Seven fixed tiers managed in-app Inference engine None bundled — external Ollama server Bundled, on-device (Apple Silicon) Download size 7.2 MB (no weights) App + 2.37 GB to 209 GB per tier Platforms macOS 14+, iOS/iPadOS 17+, visionOS 1.1+ macOS 12+, Apple Silicon only — no iPhone, iPad, Vision Pro, Windows or Linux API compatibility Ollama API only (OpenAI-compatible support requested in 4 open issues) Local models only Licence Apache-2.0, full Swift source on GitHub Closed source; weights published on Hugging Face Price Free, no in-app purchases Free tier (Nano + Lite); Pro $20/mo or $149/yr Maintenance status Last functional commits 2025-03-18; App Store build unchanged since 2025-08-19 Actively shipping Where Enchanted genuinely wins Several of these aren't close.
- **[DATE/VERSION]** The README is blunt about it: you need to run your own Ollama server, version 0.1.14 or later.
- **[DATE/VERSION]** The app is 7.2 MB because there's nothing in it but the interface.
- **[DATE/VERSION]** Nano (4B, 2.37 GB, 6 GB RAM) and Lite (9B, 5.04 GB, 12 GB RAM) are free with no account.
- **[DATE/VERSION]** Pro adds Quick, Core, Code, Vision and Plus — Core 27B runs about 20.7 tok/s on an M1 Ultra, and Plus 397B streams its experts from SSD to fit in roughly 11 GB of peak RSS on a 64 GB machine.
- **[DATE/VERSION]** Apache-2.0, roughly 6,000 GitHub stars, the entire Swift source public.
- **[DATE/VERSION]** Our Core 27B matched Claude Opus on 98.9% of rubric checks across a 54-prompt head-to-head , and our local 27B measured about 45% on a blind slice of SWE-bench Verified.
- **[DATE/VERSION]** Sources and receipts: Enchanted facts verified 2026-07-23 from primary sources — the GitHub repo API and commit history ( github.com/gluonfield/enchanted : Apache-2.0, 5,977 stars, 113 open issues, last functional commits 2025-03-18), its README, PRIVACY.md, entitlements file and Xcode project, and Apple's iTunes lookup API plus the App Store listing (free, no in-app purchases, 7.2 MB, version 1.9.0 dated 2025-08-19, Developer Tools category).
- **[NUMBER]** An app that does inference on-device is hard-capped by the RAM of the machine it's installed on — Outlier's Plus tier needs 64 GB, full stop.

### `/vs/outlier-vs-github-copilot/` — Outlier vs GitHub Copilot: local coding AI vs cloud coding AI
- **[MONEY]** You can’t download those weights, pin a version, or archive one, and the free tier offers no model choice at all: auto selection only.
- **[MONEY]** Business and Enterprise data is excluded by contract, so the strongest protection goes to buyers with procurement, not the individual on a $100 Max plan.
- **[MONEY]** Cost, and how predictable it is Copilot Free is $0 for up to 2,000 completions and 50 chat requests a month.
- **[MONEY]** Pro is $10/user/month with $15 in credits, Pro+ $39 with $70, Max $100 with $200.
- **[MONEY]** One credit is $0.01, billing is per model, and published input prices run $0.20 to $10.00 per million tokens.
- **[MONEY]** Copilot Pro at $10 is cheaper than Outlier Pro at $20, and I won’t spin that.
- **[MONEY]** Outlier’s free tier is Nano and Lite, no account, no caps.
- **[MONEY]** Pro is $20/month or $149/year for all seven tiers, lifetime from $99.
- **[MONEY]** Code 27B, open weights Code leaves machine Yes — Azure, AWS, Google Cloud, OpenAI No — on-device, works offline Trained on by default Free/Pro/Pro+/Max yes since 2026-04-24 (opt-out); Business no No data to train on Cost $0 / $10 / $39 / $100 monthly, usage-metered credits Free / $20 monthly / $149 yearly / $99 lifetime Caps Free: 2,000 completions.
- **[MONEY]** Governance, and a free tier that isn’t a demo.
- **[MONEY]** Content exclusion, org policy, audit logs, a Data Protection Agreement, a duplication filter for public-code matches of 65 lexemes or more, and 2,000 completions a month at $0.
- **[DATE/VERSION]** Which model is doing the work Copilot routes to other companies’ models: OpenAI’s GPT-5 family, Anthropic’s Claude Haiku 4.5 through Opus 4.8, Google’s Gemini 3.x, GitHub’s Raptor mini, Microsoft’s MAI-Code-1-Flash, Moonshot’s Kimi K2.7 Code — a lot of frontier capability behind one login.
- **[DATE/VERSION]** Outlier ships seven tiers you download once, from Nano 4B up to Plus 397B-a17b, including Code 27B (15.13 GB, 24 GB RAM).
- **[DATE/VERSION]** Six are Apache 2.0, Quick is under the Gemma Terms of Use, and the weights are published openly — what you’ve downloaded can’t be deprecated out from under you.
- **[DATE/VERSION]** Code 27B scores 0.866 on HumanEval .
- **[DATE/VERSION]** Core 27B separately matched Claude Opus on 98.9% of rubric checks across 54 prompts .
- **[DATE/VERSION]** Outlier figures measured on M1 Ultra; HumanEval 0.866 and the 18/40 SWE-bench Verified slice ran in my own harness, not a leaderboard.
- **[DATE/VERSION]** Pricing as of 2026-07-23.
- **[POLICY]** GitHub holds zero-data-retention agreements with OpenAI and Anthropic, and says Google commits not to train on GitHub data — better than a default API relationship.
- **[POLICY]** The opt-out is real but manual.
- **[NUMBER]** The largest models Copilot serves are far beyond anything that fits in 64 GB of unified memory.

### `/vs/outlier-vs-gpt4all/` — Outlier vs GPT4All: two local AI apps compared
- **[MONEY]** GPT4All is MIT-licensed and free for commercial use, no account, no paid tier — Nomic's pricing page covers only its Platform and Developer API, from $40 per user per month with a $1,000 monthly minimum, and doesn't mention GPT4All.
- **[MONEY]** Nano and Lite are free with no account; Pro is $20/month or $149/year for all seven tiers, lifetime from $99.
- **[MONEY]** Side-by-side GPT4All Outlier Interface GUI + Python SDK + local API server; no CLI Native Mac GUI; no CLI, SDK, or server Built for Tinkerers and developers, usable by non-experts End users who want it to just work Setup effort Choose a model, optionally tune threads/GPU layers Choose a tier; no runtime settings Model management Curated catalog plus any HuggingFace GGUF Seven fixed tiers, pre-sized and tuned Bundled vs assembled LocalDocs, embeddings, API server in the box Chat only; no RAG, search, or images Model sizes Catalog targets roughly 3–13B 4B up to 397B-a17b (64 GB Mac) Platforms Windows x64, Windows ARM, macOS 12.6+, Linux x86-64 Apple Silicon Macs only, macOS 12+ Licensing MIT, open source, commercial use allowed Closed-source app; weights published, Apache 2.0 base models Price Free, no paid tier Free (Nano + Lite); Pro $20/mo or $149/yr Runs offline Yes, by default Yes, by default Last release v3.10.0, 2025-02-25 Shipping through July 2026 Where GPT4All genuinely wins Free and MIT-licensed.
- **[DATE/VERSION]** GPT4All hasn't shipped a release since February 2025.
- **[DATE/VERSION]** Three things ship alongside the GUI: a Python SDK ( pip install gpt4all ), a local OpenAI-compatible API server on port 4891 that stays off until you enable it and per the docs accepts HTTP only on 127.0.0.1, and LocalDocs, which indexes a folder of files and shows which snippets it retrieved.
- **[DATE/VERSION]** The GitHub API reports the repo was last pushed 2025-05-27, and that commit was a CI config change — the last substantive commits are from February 2025.
- **[DATE/VERSION]** PyPI still shows bindings 2.8.2, and 772 issues are open with no visible triage.
- **[DATE/VERSION]** An issue titled "Is GPT4all dead?" has been open since August 2025 with no maintainer reply — every comment is from someone outside the organization.
- **[DATE/VERSION]** Community comments in the "Development stopped?" thread claim the frozen backend can't load newer architectures — in January 2026 they describe Qwen3 as unsupported and put the ceiling near Mistral Small 3.2.
- **[DATE/VERSION]** Outlier ships seven fixed tiers, sizing done for you: Nano 4B (2.37 GB, 6 GB RAM) through Lite 9B, Quick 26B-a4b, Core 27B, Code 27B, and Vision 35B-a3b, up to Plus 397B-a17b (209 GB, 64 GB RAM), which streams experts from SSD and peaks near 11 GB RSS.
- **[DATE/VERSION]** GPT4All runs on Windows (down to an Intel Core i3 2nd Gen), Windows ARM, macOS Monterey 12.6+, and Ubuntu/Linux x86-64, plus a community Flathub build.
- **[DATE/VERSION]** The same window can talk to Groq, OpenAI, or Mistral — added in v3.10.0 — so one app covers local and cloud.
- **[DATE/VERSION]** 77,000+ GitHub stars since March 2023 means tutorials and forum answers for almost anything you'll hit.
- **[DATE/VERSION]** On measured quality: Core 27B matched Claude Opus on 98.9% of rubric checks across a 54-prompt head-to-head , and scored about 45% (18/40) on a blind slice of SWE-bench Verified.
- **[DATE/VERSION]** Sources and receipts: GPT4All license, stars, open issues, and last-push date from the GitHub API and the releases page (read 2026-07-23).
- **[NUMBER]** Pick Outlier if you're on an Apple Silicon Mac, you want models past the 13B range — Core 27B, or Plus 397B on a 64 GB machine — and you'd rather not think about quantization or which GGUF to download.

### `/vs/outlier-vs-grok/` — Outlier vs Grok: local Mac AI vs xAI's cloud assistant
- **[MONEY]** A free tier that isn't a trial. $0/month includes real-time web and X search, voice mode and connectors, with SOC 2 Type I and II listed even there.
- **[MONEY]** Cheap long-context API. grok-4.3 is $1.25/$2.50 per million input/output tokens with a 1M window; grok-4.5 is $2.00/$6.00 under 200k context and $4.00/$12.00 above it.
- **[MONEY]** What it costs over a year xAI's pricing page publishes exactly two consumer prices: Free at $0/month and SuperGrok at $30/month, which is where Grok 4.5, higher rate limits and image and video generation live.
- **[MONEY]** So the only annual figure you can compute from xAI's own material is $360/year, at twelve monthly payments.
- **[MONEY]** Third-party trackers list Heavy at $300/month and an annual plan at $300/year; I couldn't confirm either on an xAI-owned page, so treat both as unverified.
- **[MONEY]** Outlier Pro is $20/month or $149/year, with lifetime Pro from $99.
- **[MONEY]** Nano 4B (2.37 GB, 6 GB RAM, 71.7 tok/s on M1 Ultra) and Lite 9B are free forever; Pro at $20/month or $149/year adds five more tiers up to Plus 397B-a17b.
- **[MONEY]** Or if you want no account, no caps, a session that keeps working on a plane, and $149/year instead of $360.
- **[MONEY]** The $300/month Heavy and $300/year annual figures on third-party trackers are unconfirmed .
- **[DATE/VERSION]** Every figure below comes from xAI's own pages, checked 2026-07-23.
- **[DATE/VERSION]** The flagship is Grok 4.5 with a 500,000-token context window, and Grok 4.3 and the 4.20 variants go to a million.
- **[DATE/VERSION]** There's no native macOS app, and the official iOS listing (Grok AI by X Corp., free, iOS 17+, rated 4.88 across ~1.31 million ratings) shows no Mac devices.
- **[DATE/VERSION]** Grok Build is an Apache-2.0 Rust coding agent installed with a one-line curl … | bash , with binaries for macOS, Linux and Windows and support for MCP servers, parallel subagents, plan mode, skills, hooks, git worktrees, headless CI and sandboxed execution.
- **[DATE/VERSION]** 500k tokens on Grok 4.5, a million on Grok 4.3 and the 4.20 line.
- **[DATE/VERSION]** Grok 4.5 was trained on datacenter compute.
- **[DATE/VERSION]** The Grok Build agent, the Python SDK and the protobufs are Apache-2.0, and Grok's own system prompts are AGPL-3.0 — rare, and it deserves credit.
- **[DATE/VERSION]** Grok-1 shipped under Apache 2.0 in March 2024.
- **[DATE/VERSION]** On 17 February 2026 the Irish Data Protection Commission opened a statutory inquiry into X Internet Unlimited Company over the apparent creation and publication of non-consensual intimate or sexualised images of EU/EEA data subjects, including children, via generative AI functionality associated with Grok on X.
- **[DATE/VERSION]** For quality, the number I'd point at: Core 27B matched Claude Opus on 98.9% of rubric checks across a 54-prompt head-to-head , and 100% on the nine hardest.
- **[NUMBER]** A 2–30 GB model on a laptop won't match it on the hardest reasoning or broadest recall.
- **[NUMBER]** Private Chat keeps content out of training, hides it from history, and deletes it within 30 days barring legal holds; business, enterprise and API traffic is excluded from training outright; and xAI says it doesn't sell user data.

### `/vs/outlier-vs-koboldcpp/` — Outlier vs KoboldCpp: native Mac app vs single-file local server
- **[MONEY]** Pro is $20/month or $149/year for all seven; lifetime licenses start at $99.
- **[MONEY]** Side-by-side KoboldCpp Outlier Interface Terminal launch → browser UI (KoboldAI Lite) + HTTP API Native Mac chat window Who it's for Tinkerers, writers/roleplayers, developers wiring a local backend End users who want a Mac app that opens and works Setup effort Download one file, chmod, clear Gatekeeper, source your own model Install, pick a tier, wait for download Model management Bring your own GGUF; any architecture, any quant Seven curated tiers; no third-party model loading Bundled models None — not included with the download All seven, in-app Beyond text Image gen/edit, video, Whisper STT, TTS, music, vision Vision tier only; no image gen, no voice Platforms Windows, Linux, macOS ARM64, Android (Termux), Docker, Colab, RunPod macOS on Apple Silicon only Signed / notarized on Mac No Yes License AGPL-3.0 (llama.cpp / GGML components MIT) Proprietary app; open weights on Hugging Face Price Free, no tiers, no account Free tier (Nano + Lite); Pro $20/mo or $149/yr Runs offline Yes Yes Where KoboldCpp genuinely wins This section isn't a courtesy.
- **[MONEY]** Outlier gates five of seven tiers behind $20/month.
- **[DATE/VERSION]** KoboldCpp is a free, AGPL-3.0 single-file server you launch from a terminal and use through a browser UI — it runs any GGUF model you supply, on Windows, Linux, macOS ARM64, or Android.
- **[DATE/VERSION]** Every claim about KoboldCpp below comes from its own README, wiki FAQ, and GitHub release data, checked on 2026-07-23.
- **[DATE/VERSION]** What KoboldCpp actually is KoboldCpp is a local inference server maintained by LostRuins, first published in March 2023 and still pushed almost daily.
- **[DATE/VERSION]** As of v1.117.1 it also serves Ollama-compatible embeddings and streaming endpoints with tool calling, which means existing tooling can point at it without code changes.
- **[DATE/VERSION]** Seven tiers ship inside the app: Nano 4B (2.37 GB, 6 GB RAM), Lite 9B, Quick 26B-a4b, Core 27B, Code 27B, Vision 35B-a3b, and Plus 397B-a17b, which streams experts from SSD and peaks around 11 GB of RSS on a 64 GB machine.
- **[DATE/VERSION]** AGPL-3.0, with the llama.cpp and GGML pieces under MIT.
- **[DATE/VERSION]** Ten releases between February and July 2026, tracking upstream llama.cpp closely, so new architectures land fast.
- **[DATE/VERSION]** Active since March 2023, 11,181 stars and 737 forks as of today, with a community large enough that most setup problems are already documented.
- **[DATE/VERSION]** Plus 397B-a17b runs on a 64 GB Mac via paged MoE at about 2.1 tok/s.
- **[DATE/VERSION]** Core 27B matched Claude Opus on 98.9% of rubric checks across a 54-prompt head-to-head , and hit ~45% on a blind slice of SWE-bench Verified.
- **[DATE/VERSION]** Sources and receipts: KoboldCpp details from its GitHub repository , its wiki FAQ , the AGPL-3.0 LICENSE.md , and GitHub release metadata for v1.117.1 (published 2026-07-09), all checked 2026-07-23; star, fork, and release-cadence figures are from the GitHub API on that date.
- **[NUMBER]** The FAQ gives rough guidance (a 7B model wants at least 8 GB of RAM, 13B at least 16 GB), and Metal acceleration works on Apple Silicon, but the tuning is on you.

### `/vs/outlier-vs-llama-cpp/` — Outlier vs llama.cpp: a Mac app vs the engine underneath local AI
- **[MONEY]** Pro is $20/month or $149/year for all seven tiers, lifetime from $99.
- **[MONEY]** Side by side llama.cpp Outlier Interface CLI + local HTTP server with browser WebUI Native macOS app window Who it's for Developers and tinkerers End users on a Mac Setup effort Install, choose flags, run a server binary Download, double-click Model management Bring your own GGUF; auto-discovery, dropdown switching Seven fixed tiers, quantized for you Bundled vs assembled Engine only — no model Model, UI and tuning in one download Platforms macOS, Linux, Windows, Android, iOS Apple Silicon Macs only License MIT, fully open source Proprietary app; weights published Price Free, no tiers Free tier; Pro $20/mo or $149/yr Runs offline Yes Yes Where llama.cpp wins outright Free forever, under MIT.
- **[DATE/VERSION]** It's MIT-licensed — commercial use allowed — and there's no pricing at all: no tiers, no seats, no license key. ggml.ai, the company formed around it, was acquired by Hugging Face in February 2026, with a public commitment that the project stays 100% open source and the core team keeps full technical autonomy.
- **[DATE/VERSION]** Seven tiers ship in it: Nano 4B (2.37 GB, 6 GB RAM, 71.7 tok/s on M1 Ultra), Lite 9B, Quick 26B-a4b, Core 27B, Code 27B, Vision 35B-a3b, and Plus 397B-a17b, which streams experts from SSD at ~11 GB peak RSS.
- **[DATE/VERSION]** The base weights are Qwen and Gemma models — six tiers Apache 2.0, Quick under the Gemma Terms of Use — and I publish the quantized weights at huggingface.co/Outlier-Ai .
- **[DATE/VERSION]** Interface, setup, and who each one is for This is the axis that decides it for most people. llama.cpp is command-line first: even the Homebrew path ends with you running a server binary with flags, then opening a browser tab at 127.0.0.1:8080 .
- **[DATE/VERSION]** In exchange you get range: 1.5-bit through 8-bit quantization — the biggest lever for fitting a good model on a laptop — plus LLaMA, Mistral, Phi, Qwen and multimodal families like LLaVA and Qwen2-VL.
- **[DATE/VERSION]** 1.5-bit through 8-bit is a dial Outlier doesn't expose.
- **[DATE/VERSION]** OpenAI-compatible /v1/chat/completions , embeddings, reranking, function calling, schema-constrained output — and since January 2026 an Anthropic-compatible /v1/messages endpoint, so Claude Code can be pointed at a local model with ANTHROPIC_BASE_URL=http://127.0.0.1:8080 .
- **[DATE/VERSION]** The receipt: Core 27B matched Claude Opus on 98.9% of rubric checks across a 54-prompt head-to-head , and measured about 45% on a blind slice of SWE-bench Verified.

### `/vs/outlier-vs-meta-ai/` — Outlier vs Meta AI: local Mac AI vs Meta's cloud assistant
- **[MONEY]** Pro — $20/month or $149/year — adds Quick 26B-a4b, Core 27B, Code 27B, Vision 35B-a3b, and Plus, a 397B-a17b model that streams experts from SSD at roughly 11 GB peak RAM.
- **[MONEY]** Outlier's free tier stops at 9B.
- **[MONEY]** Outlier's math is simpler: $0 for Nano and Lite forever, $149/year for Pro, or $99 and up once for lifetime.
- **[DATE/VERSION]** And there's no desktop client: the App Store listing is iPhone and iPad only, iOS 17.2+, rated 13+.
- **[DATE/VERSION]** Nano (4B, 2.37 GB, 6 GB RAM) and Lite (9B, 5.04 GB, 12 GB RAM) are free.
- **[DATE/VERSION]** On an M1 Ultra, Nano measures 71.7 tok/s and Core 20.7.
- **[DATE/VERSION]** Six tiers are Apache 2.0, with weights on Hugging Face .
- **[DATE/VERSION]** On quality: Core 27B matched Claude Opus on 98.9% of rubric checks across a 54-prompt head-to-head, and 100% on the nine hardest.
- **[DATE/VERSION]** Sources and receipts: Muse Spark launch and closed-weights status from Meta's April 8, 2026 announcement; 1.1 capabilities from ai.meta.com (July 9, 2026).
- **[DATE/VERSION]** Quotes from Meta's AI Terms and help pages; ad personalization from Meta's October 2025 post; platform and privacy-label details from the App Store listing.
- **[POLICY]** Outlier's version of this section is short: no server, no account, no telemetry on your prompts, nothing to opt out of.

### `/vs/outlier-vs-microsoft-copilot/` — Outlier vs Microsoft Copilot: local Mac AI vs Microsoft's cloud
- **[MONEY]** The consumer app is free, but Microsoft states it can't reach your documents or email and doesn't run inside Word, Excel or Outlook; the version that reads your work — Microsoft 365 Copilot — is $30 per user per month billed yearly, on top of a qualifying Microsoft 365 licence.
- **[MONEY]** Worth knowing if you're budgeting: Copilot Pro, the standalone $20/month consumer plan, is gone.
- **[MONEY]** Pro is $20/month or $149/year for all seven, lifetime from $99.
- **[MONEY]** What Copilot actually costs per year Consumer pricing as of July 2026: Microsoft 365 Personal is $9.99/month or $99.99/year for one person.
- **[MONEY]** Family is $12.99/month or $129.99/year for up to six.
- **[MONEY]** Premium is $19.99/month or $199.99/year for up to six, and includes Office with Copilot built in, up to 6 TB of storage, and agents like Researcher in Word and Analyst in Excel.
- **[MONEY]** Eligible existing subscribers are offered a promotional $99.99 first year.
- **[MONEY]** On the work side, Microsoft 365 Copilot is $30.00 per user per month paid yearly, or $31.50 on monthly billing with an annual commitment.
- **[MONEY]** Copilot Business , the small-business SKU, lists at $21.00/user/month, promotionally $18.00 on annual commitment between 1 July and 30 September 2026, first year only; $25.20 on monthly commitment.
- **[MONEY]** Or if you work offline, or you're tired of metering, or $149/year against $360/seat/year plus a base licence changes the maths.
- **[DATE/VERSION]** As of July 2026 that model can be OpenAI's GPT-5.6 family; Anthropic's Claude models are available too, with Anthropic onboarded as a Microsoft subprocessor.
- **[DATE/VERSION]** Seven tiers, from Nano (4B, 2.37 GB, needs 6 GB RAM) through Core 27B to a 397B-a17b Plus tier that streams experts from SSD.
- **[DATE/VERSION]** Core 27B matched Claude Opus on 98.9% of rubric checks across 54 prompts, and measured about 45% on a blind slice of SWE-bench Verified.
- **[DATE/VERSION]** GPT-5.6-class models and Claude run in Microsoft's datacentres, so an old laptop gets the same answers as a Mac Studio.
- **[DATE/VERSION]** Microsoft's stopgap, Restricted SharePoint Search, is capped at 100 sites, is explicitly "not a security boundary," and is being retired — new enablement is blocked from 31 July 2026.
- **[DATE/VERSION]** Sources and receipts: Copilot pricing from microsoft.com consumer plan comparison , Microsoft 365 Copilot enterprise and Copilot Business , checked July 2026.
- **[NUMBER]** Outlier's quality is bounded by your RAM — Plus needs 64 GB.

### `/vs/outlier-vs-mistral-le-chat/` — Outlier vs Mistral Le Chat (now Vibe): local Mac AI vs a European cloud assistant
- **[MONEY]** Pro is $14.99/month, an account is required, every prompt runs on Mistral's servers, and on consumer tiers your input trains their models unless you find the opt-out.
- **[MONEY]** Pro is $20/month or $149/year for all seven tiers, lifetime from $99.
- **[MONEY]** Image generation is included even on the free tier.
- **[MONEY]** Price. $14.99/month undercuts the $20/month that ChatGPT Plus, Claude Pro, and Outlier Pro all charge.
- **[MONEY]** Verified students pay $5.99/month for up to 12 months.
- **[MONEY]** What it costs over a year Mistral doesn't publish an annual plan, so the honest arithmetic is twelve monthly payments: $14.99 × 12 = $179.88 a year, before tax .
- **[MONEY]** The App Store listing shows a second in-app purchase at $149.99 alongside the $14.99 one, consistent with annual billing — but it doesn't label the period, so treat that as an inference, not a price.
- **[MONEY]** Outlier Pro is $20/month or $149/year (about $12.42/month yearly), lifetime from $99.
- **[MONEY]** Mistral Team is $24.99/user/month with a $50/month minimum , so a solo user on Team pays for two seats.
- **[MONEY]** Who should pick which Pick Mistral Vibe if you need live web results, image generation, voice, or a phone app; you want one $14.99 subscription covering chat and coding; you're a student eligible for $5.99; you want agents that run while your laptop is shut; or you're an EU organization that wants a GDPR-native vendor with an on-premises path.
- **[MONEY]** Pick Outlier if you handle material you can't upload — client files, patient notes, unreleased code, legal drafts — and want that guaranteed by architecture, not a setting; you work offline; or you'd rather pay a fixed $149/year with nothing metered.
- **[MONEY]** The $149.99 App Store tier is an inference about annual billing, not a stated price.
- **[DATE/VERSION]** Work mode runs on Mistral Medium 3.5, a 128B dense model with a 256k context window; coding runs on the Devstral 2 family.
- **[DATE/VERSION]** Seven tiers, from Nano (4B, 2.37 GB, runs in 6 GB of RAM) up to Plus 397B-a17b, which streams experts from SSD and needs a 64 GB machine.
- **[DATE/VERSION]** Mistral Large 3 (675B) and Devstral Small 2 (24B) are Apache-2.0 on Hugging Face; Medium 3.5 (128B) is under a modified MIT license.
- **[DATE/VERSION]** The CLI is real open source and isn't cloud-locked. github.com/mistralai/mistral-vibe is Apache-2.0, ~4,700 stars, actively pushed as of July 2026.
- **[DATE/VERSION]** Devstral 2 reports 72.2% on SWE-bench Verified.
- **[DATE/VERSION]** In a 54-prompt head-to-head, Core 27B matched Claude Opus on 98.9% of rubric checks and 100% on the nine hardest prompts, so for everyday writing and reasoning the local gap is smaller than parameter counts suggest.
- **[DATE/VERSION]** Sources and receipts: Prices, tiers, interfaces, features from mistral.ai/pricing (July 2026); rebrand and modes from the Vibe docs ; offline CLI behavior from the CLI install guide ; session caps from Vibe Code Web limits ; training, retention, transfer, and Memory language quoted from the privacy policy .
- **[POLICY]** EU providers prioritized, Standard Contractual Clauses for transfers, a published DPA, self-serve deletion, a training opt-out, and on-premises or private-cloud deployment for enterprise.
- **[POLICY]** Training is opt-out, not opt-in.
- **[NUMBER]** 100+ connectors, custom remote MCP servers, Workflows, scheduled tasks, hooks, a code-interpreter sandbox, 15 GB storage on Pro.

### `/vs/outlier-vs-msty/` — Outlier vs Msty: two local AI apps, two different jobs
- **[MONEY]** The free tier is substantive rather than a teaser: local and online chat, Agent Mode, Knowledge Stacks for retrieval, an MCP Toolbox, Persona, Prompt, Skill and Media studios, memories and web search all sit at $0.
- **[MONEY]** Paid "Aurum" is $149/year or $349 once for a lifetime seat; Enterprise is $300 per user per year, five seats minimum.
- **[MONEY]** Free means Nano and Lite, no account; Pro is $20/month or $149/year, lifetime from $99.
- **[MONEY]** Side by side Msty Studio Outlier Interface Desktop GUI; browser version (Aurum) via a Sidecar proxy Native Mac GUI only Who it's for Tinkerers who want model choice and cloud keys in one place End users who want a Mac app that already works Setup effort Install, pick a model; Msty installs the engine for you Install, pick a tier, download starts Model management You choose: 3 engines, GGUF/MLX/Safetensors, 13 cloud providers Seven curated tiers, no picker beyond them Bundled vs assembled Assembled — you bring models and keys Bundled — weights ship with it Platforms macOS (Apple Silicon + Intel), Windows x64, Linux x64 Apple Silicon Macs only Cloud models Yes, bring your own key None Source code Closed; docs and some forks public Closed; weights public Free tier $0, personal use only $0, Nano + Lite, no account Paid $149/yr, $349 lifetime, 2 devices $20/mo or $149/yr, lifetime from $99 Bundled versus assembled — the real fork in the road This is the difference that decides it for most people.
- **[MONEY]** A lifetime option. $349 once, price-protected against future increases.
- **[MONEY]** Prices rose on 2 December 2025 (Aurum yearly $129 to $149, lifetime $249 to $349).
- **[MONEY]** Who should pick which Pick Msty if you own a Windows or Linux machine or an Intel Mac; you enjoy swapping models; you want local and cloud side by side with your own keys; you need web search, MCP tools or retrieval over your own documents; or you want a lifetime license and a usable free tier.
- **[DATE/VERSION]** Nano 4B (2.37 GB, 6 GB RAM, 71.7 tok/s on M1 Ultra), Lite 9B, Quick 26B-a4b, Core 27B and Code 27B (15.13 GB, 24 GB, 20.7 tok/s), Vision 35B-a3b, and Plus 397B-a17b, which needs 64 GB and streams experts from SSD.
- **[DATE/VERSION]** Six are Apache 2.0, Quick carries the Gemma Terms of Use, and the weights are public .
- **[DATE/VERSION]** Core 27B matched Claude Opus on 98.9% of rubric checks across a 54-prompt head-to-head — a number attached to a build I ship, not a configuration you assembled.
- **[DATE/VERSION]** Sources: Msty pricing, tiers and the December 2025 price change from msty.ai/studio/pricing ; builds, engines and providers from docs.msty.ai ; privacy claims from msty.ai/privacy ; licensing and device limits from msty.ai/terms ; open-source status from the vendor's public GitHub org.
- **[DATE/VERSION]** All read July 2026 — competitor pricing and policies change, so verify at the source before you buy.
- **[DATE/VERSION]** Outlier throughput measured on an M1 Ultra Mac Studio (64 GB); the 98.9% figure comes from the 54-prompt head-to-head .

### `/vs/outlier-vs-notebooklm/` — Outlier vs Google NotebookLM (Gemini Notebook): local AI vs a cloud research assistant
- **[MONEY]** The free tier is Nano plus Lite, no account.
- **[MONEY]** Pro is $20/month or $149/year for all seven tiers, with lifetime licenses from $99.
- **[MONEY]** 500,000 words or 200 MB per source, no page limit, 300 sources per notebook on the $19.99 Pro tier and 600 on top Ultra.
- **[MONEY]** A free tier that's a real product, not a demo: 100 notebooks, 50 sources each, 50 chats and 3 Audio Overviews a day, at $0.
- **[MONEY]** What it costs over a year Gemini Notebook can't be bought on its own; paid tiers ride on a Google AI subscription — Plus at $4.99/month, Pro at $19.99/month, Ultra from $99.99/month with a $199.99 option.
- **[MONEY]** Google's page lists monthly prices only, with no official annual SKU, so annualising is just twelve times the rate: $59.88, $239.88, $1,198.80.
- **[MONEY]** Some press coverage puts Plus nearer $8/month in the US, which conflicts with Google's own page, so check your country.
- **[MONEY]** Outlier Pro is $20/month or $149/year, or a lifetime license from $99.
- **[DATE/VERSION]** What Gemini Notebook (formerly NotebookLM) is Google renamed NotebookLM to Gemini Notebook in a rollout that began 16 July 2026, across Workspace and personal Google accounts alike.
- **[DATE/VERSION]** Since July 2026 each notebook also gets a secure cloud computer that runs code against your sources and returns PDF, Excel, PowerPoint, JSON, charts or images.
- **[DATE/VERSION]** Google says the product now runs on Gemini 3.5 and Antigravity, reaching Ultra and some Workspace customers first.
- **[DATE/VERSION]** Seven tiers ship in the app, from Nano (4B, 2.37 GB, runs on 6 GB of RAM) through Core 27B and Code 27B up to Plus, a 397B mixture-of-experts model that streams experts from SSD and peaks near 11 GB of RSS on a 64 GB machine.
- **[DATE/VERSION]** Six tiers are Apache 2.0; Quick is under the Gemma Terms of Use.
- **[DATE/VERSION]** Web, first-party iOS/iPadOS and Android apps, and notebooks that sync into the Gemini app — including the native Gemini app for Mac from April 2026.
- **[DATE/VERSION]** On a 54-prompt head-to-head, Core 27B matched Claude Opus on 98.9% of rubric checks and 100% on the nine hardest; on a blind slice of SWE-bench Verified the local 27B measured about 45%.
- **[DATE/VERSION]** Sources and receipts: Rename, user counts and cloud code execution from blog.google and Workspace Updates (16 July 2026).
- **[POLICY]** Training is opt-in via the thumbs-up/down button, not opt-out.
- **[POLICY]** Click it and that content goes to trained review teams, disconnected from your Google Account, retained up to three years.
- **[POLICY]** Workspace and Education accounts get no human review at all, and no training.
- **[NUMBER]** The ceilings are big: 500,000 words or 200 MB per source, no page limit.

### `/vs/outlier-vs-perplexity/` — Outlier vs Perplexity: local Mac AI vs a cloud answer engine
- **[MONEY]** Nano and Lite are free with no account; Pro is $20/month or $149/year for all seven.
- **[MONEY]** What it costs over a year Perplexity Pro is $20/month, stated on Perplexity's own Max announcement and matching the App Store in-app purchase listing; Max is listed at $200.
- **[MONEY]** Enterprise Pro is $40/user/month ($400/year) and Enterprise Max $325/user/month ($3,250/year).
- **[MONEY]** Third-party trackers report discounted annual plans and a $10/month education tier, but I couldn't confirm those — perplexity.ai/pricing returns HTTP 403 to automated fetching — so treat them as unconfirmed.
- **[MONEY]** Outlier Pro is $20/month or $149/year — $12.42/month.
- **[MONEY]** Lifetime Pro starts at $99, and Nano and Lite stay free.
- **[MONEY]** The API is priced separately and is reasonable: Sonar at $1 per million input and output tokens, Sonar Pro at $3/$15, plus request fees of $5–$14 per thousand depending on search context size.
- **[MONEY]** The Search API bills $5.00 per 1,000 requests, and third-party models routed through the Agent API carry no Perplexity markup.
- **[MONEY]** Pick it if you work on planes or in dead zones, if usage caps have interrupted you mid-task, or if you'd rather pay $149 a year than $240.
- **[DATE/VERSION]** The models are a mix: Perplexity's own Sonar, built on Llama 3.3 70B and further trained for search, plus third-party frontier models routed through its Agent API — Claude, GPT-5, Gemini and Grok among them.
- **[DATE/VERSION]** Seven tiers ship in the app, from Nano 4B (2.37 GB, 6 GB RAM, 71.7 tok/s on an M1 Ultra) through Core 27B and Code 27B up to Plus 397B-a17b, which streams its experts from SSD and peaks near 11 GB RSS.
- **[DATE/VERSION]** Core 27B matched Claude Opus on 98.9% of rubric checks across a 54-prompt head-to-head , and 100% on the nine hardest.
- **[DATE/VERSION]** Code 27B scores 0.866 on HumanEval, and on a blind slice of SWE-bench Verified the local 27B measured about 45%.
- **[DATE/VERSION]** An MIT-licensed MCP server, Apache-2.0 GPU kernels and SDKs, and R1-1776, an open-weights post-trained DeepSeek-R1 on Hugging Face.
- **[DATE/VERSION]** Six tiers use Apache 2.0 base models; Quick ships under the Gemma Terms of Use, and weights are published at huggingface.co/Outlier-Ai .
- **[POLICY]** Sonar's weights are not published, and Perplexity's Terms of Service assign all rights to the company and prohibit reverse engineering.

### `/vs/outlier-vs-poe/` — Outlier vs Poe: local Mac AI vs Quora's model aggregator
- **[MONEY]** Poe's annual plans run $49.99 to $2,499.99; Outlier Pro is $149/year, and its two smallest models are free.
- **[MONEY]** Poe says it's free for most usage, with plans from $4.99/month.
- **[MONEY]** Nano and Lite are free; Pro is $20/month or $149/year for all seven.
- **[MONEY]** The page advertises a 17% saving against monthly billing, and Apple's App Store listing corroborates the middle rung at $19.99 monthly, $199.99 yearly.
- **[MONEY]** Outlier Pro is $149/year, or $99–$200 once for a lifetime license, and token volume doesn't move the bill.
- **[MONEY]** The cheapest real plan is cheap. $49.99/year undercuts a single-vendor $20/month plan, and it isn't a crippled trial.
- **[MONEY]** Poe's $49.99/year tier keeps frontier breadth and image generation on hand cheaply; Outlier takes the confidential, offline and high-volume work.
- **[DATE/VERSION]** The catalog named on Poe's pricing and API pages includes GPT-5.5, Claude-Opus-4.7, Gemini-3.1-Pro, Grok-4, DeepSeek-R1, and image and video models like Nano-Banana-Pro, Veo-3.1 and Sora-2.
- **[DATE/VERSION]** Seven tiers ship in the app, from Nano (4B, a 2.37 GB download, 6 GB RAM minimum, 71.7 tok/s on my M1 Ultra and 32 tok/s on an M4 MacBook Air) through Core and Code at 27B, up to Plus at 397B-a17b, which streams experts from SSD and peaks near 11 GB of RSS on a 64 GB Mac.
- **[DATE/VERSION]** Six base models are Apache 2.0; Quick is under Gemma's terms.
- **[DATE/VERSION]** A documented bot protocol, an Apache-2.0 SDK ( fastapi_poe ), monetization and multi-bot chats make Poe a platform, not just a chat window — and it costs your machine no RAM, no disk, no fans.
- **[DATE/VERSION]** The honest quality receipt: Core 27B matched Claude Opus on 98.9% of rubric checks across a 54-prompt head-to-head , and 100% on the nine hardest.
- **[DATE/VERSION]** One gap: Poe's help center — canonical for free-tier allowances and per-model point costs — returns HTTP 403 to automated fetching, so reported free-allowance cuts in March 2026 are unconfirmed at the source and left out above.
- **[POLICY]** Credit where due: Poe's privacy center says official bots built on OpenAI, Anthropic, Google and Meta models do not train on your chats, and only third-party developer bots may.
- **[POLICY]** The catch: that control is per bot, not per account, and no global training opt-out is documented.
- **[NUMBER]** There's a real developer platform on top: a documented bot protocol, server bots, monetization, group chats, and an OpenAI-compatible REST API at api.poe.com/v1 (plus an Anthropic-compatible endpoint) that Poe documents as working with Cursor, Cline, Continue and the llm CLI, capped at 500 requests per minute.

### `/vs/outlier-vs-privategpt/` — Outlier vs PrivateGPT: a Mac app vs a self-hosted API layer
- **[MONEY]** Pro is $20/month or $149/year for all seven tiers, with lifetime licenses from $99.
- **[MONEY]** Side by side PrivateGPT Outlier Interface CLI ( private-gpt serve ) + REST API + a developer Workbench web UI on localhost:8080 Native macOS GUI Who it's for Developers building private AI features and products End users who want to chat, write and code locally Setup effort Homebrew / uv / Docker, plus a separate inference server; Python 3.11 exactly on the uv path Download, open, pick a tier Runs models itself No — you supply the OpenAI-compatible server Yes — engine bundled Model management Yours: pull chat + embedding models via Ollama/LM Studio/llama.cpp/vLLM Seven curated tiers, one-click download, RAM guidance published Bundled vs assembled Assembled: no weights ship with it Bundled: app + engine + weights Platforms macOS, Linux, Windows, Docker Apple Silicon Macs only Licensing Apache 2.0, fully auditable Closed-source app; open weights on Hugging Face Price Free, no seats or tokens (commercial Zylon tier is contact-sales) Free tier; Pro $20/mo or $149/yr Team / server deployment Yes — Docker, Linux, on-prem, air-gapped No — single-user desktop app Where PrivateGPT genuinely wins Several of these aren't close, so I'll say them flatly.
- **[DATE/VERSION]** What PrivateGPT actually is in 2026 The canonical project is the GitHub repo zylon-ai/private-gpt , started in May 2023 and licensed under Apache 2.0.
- **[DATE/VERSION]** As of 23 July 2026 it has 57,354 stars and 7,607 forks.
- **[DATE/VERSION]** Version 1.0.0, shipped 3 June 2026, was a ground-up rewrite that moved model execution out of the project.
- **[DATE/VERSION]** You set OPENAI_API_BASE to point at an OpenAI-compatible server you run yourself; Ollama, LM Studio, llama.cpp and vLLM are named explicitly. v1.0.1 followed on 18 June 2026 with bug fixes and prompt-caching work.
- **[DATE/VERSION]** Before that came v0.6.2 in August 2024, and pre-1.0 PrivateGPT did run models itself — so nearly every walkthrough written between 2023 and mid-2026 describes software that no longer works that way.
- **[DATE/VERSION]** The uv path pins Python 3.11 exactly — the docs say 3.10 and 3.12+ aren't supported.
- **[DATE/VERSION]** It ships seven tiers: Nano 4B (2.37 GB, 6 GB RAM, 71.7 tok/s on M1 Ultra), Lite 9B (5.04 GB, 12 GB), Quick 26B-a4b (15.61 GB, 16 GB), Core 27B and Code 27B (15.13 GB, 24 GB, 20.7 tok/s), Vision 35B-a3b (19.0 GB, 24 GB), and Plus 397B-a17b (209 GB, 64 GB, 2.1 tok/s, streaming experts from SSD at ~11 GB peak RSS).
- **[DATE/VERSION]** The base models are Qwen and Gemma derivatives — six tiers Apache 2.0, Quick under the Gemma Terms of Use — and the weights are published at huggingface.co/Outlier-Ai .
- **[DATE/VERSION]** Apache 2.0 means every claim about where your data goes is verifiable in the source.
- **[DATE/VERSION]** Core 27B matched Claude Opus on 98.9% of rubric checks across a 54-prompt head-to-head , and 100% on the nine hardest prompts; on a blind slice of SWE-bench Verified the local 27B measured about 45% (18/40).
- **[DATE/VERSION]** Sources and receipts: PrivateGPT star/fork counts, license and creation date from the GitHub API on 2026-07-23; release dates from the releases page ; architecture, install paths, Python version, Workbench caveats and web-tool behavior from docs.privategpt.dev ; commercial tier from zylon.ai .
- **[NUMBER]** One thing to install instead of two, no Python version to pin, no embedding model to choose, and a published RAM figure for every tier so you know before downloading whether it'll run on your 16 GB Mac.

### `/vs/outlier-vs-qwen-chat/` — Outlier vs Qwen Chat: the same model family, two delivery models
- **[MONEY]** Outlier runs Qwen's published open weights on your own Apple Silicon Mac: no account, no caps, nothing uploaded, works with Wi-Fi off, $149/year for all seven tiers.
- **[MONEY]** Outlier's free tiers cost nothing either, but you download a 2.37 GB model first.
- **[MONEY]** What it costs over a year For anyone using the chat app: $0 .
- **[MONEY]** On Alibaba Cloud Model Studio, international list price for qwen3.7-max is $2.50 per million input tokens and $7.50 per million output (currently shown with a limited-time 50% discount); qwen3.7-plus is $0.40 in / $1.60 out at the 0–256K tier.
- **[MONEY]** Token Plan (Team Edition) credits run $30 to $200 a month — $360 to $2,400 a year.
- **[MONEY]** Outlier Pro is $20/month or $149/year for all seven tiers; lifetime licences start at $99.
- **[DATE/VERSION]** Same lineage, opposite delivery — Qwen Chat serves bigger models nobody can self-host, Outlier serves Apache-2.0 ones that never leave the device.
- **[DATE/VERSION]** It's now branded Qwen Studio — qwen.ai still serves the old /qwenchat route, but the page title, buttons and iOS listing all read "Qwen Studio." It's operated by Alibaba Cloud (Singapore) Private Limited; the Privacy Policy and Terms are both dated 19 May 2026.
- **[DATE/VERSION]** The part that makes this comparison strange: same family, different weights Outlier's tiers are built on Qwen3.5-4B, Qwen3.5-9B, Qwen3.6-27B, Qwen3.6-35B-A3B and Qwen3.5-397B-A17B, all Apache-2.0. (The exception is Quick, a Gemma model under Gemma's terms.) Those are Alibaba's published open weights, downloaded once and run on your machine.
- **[DATE/VERSION]** The Qwen org's newest open releases are Qwen3.6-27B and Qwen3.6-35B-A3B, both from 24 April 2026 — and both are already in Outlier as the Core, Code and Vision tiers.
- **[DATE/VERSION]** Outlier's largest tier, Plus 397B, is a 209 GB download needing a 64 GB Mac, at 2.1 tokens/second on an M1 Ultra.
- **[DATE/VERSION]** Core 27B, Plus 397B Trained on your content Yes by default; opt out by request No No *On 23 July 2026 an App Store lookup returned nothing for the US or German storefronts, while Singapore, UK and Japan returned the app.
- **[DATE/VERSION]** On a 54-prompt head-to-head, Core 27B matched Claude Opus on 98.9% of rubric checks and 100% of the nine hardest, and on a blind slice of SWE-bench Verified it measured about 45%.
- **[DATE/VERSION]** Sources and receipts: Qwen's model list, feature flags, upload ceilings and subscription settings were read from its own public config endpoints at chat.qwen.ai and qwen.ai on 23 July 2026.
- **[DATE/VERSION]** Pricing from Alibaba Cloud Model Studio docs (updated 15 July 2026); open weights checked against the Qwen org on Hugging Face.
- **[POLICY]** Inference happens on your Mac: no account, no conversation telemetry, no opt-out to find.
- **[NUMBER]** Native clients cover macOS, Windows, iOS and Android — the Mac DMG is about 146 MB.
- **[NUMBER]** Video up to 2 GB and one hour, audio up to three hours, 20 MB documents.
- **[NUMBER]** It's on your phone. iOS and Android clients plus Windows and web, and it's fine on an 8 GB Mac.
- **[NUMBER]** Free API access is a one-million-token trial per model, valid 90 days.

### `/vs/outlier-vs-sourcegraph-cody/` — Outlier vs Sourcegraph Cody: local coding AI vs enterprise cloud AI
- **[MONEY]** Departing users were moved to Amp with $10 and $40 in credits; Enterprise customers, the post said, were unaffected.
- **[MONEY]** Cost, and the side-by-side Cody has no self-serve purchase and no published per-seat price — it appears nowhere on sourcegraph.com/pricing, where the only figure is an Enterprise plan "Starting at $16K." Outlier is free for Nano and Lite with no account, $20/month or $149/year for all seven tiers, lifetime from $99.
- **[MONEY]** No editor extension Model Cloud: Opus 4.8, GPT-5.4, Gemini 3.5; default Sonnet 4.5 On-device: 7 tiers, Nano 4B → Plus 397B Code leaves the machine Yes — up to 28 KB per request, even when self-hosted No — on-device, works offline Cost Enterprise contract only; platform "Starting at $16K" Free (Nano + Lite); Pro $20/mo or $149/yr Agentic ability Quick/inline edit, auto-edit, Prompt Library, MCP ~45% on a blind SWE-bench Verified slice Repo-scale context Org-wide index and code graph, permission-scoped Only what's on your Mac Account required Yes — Enterprise account with Cody enabled No The coding receipts, honestly Here's my side, measured rather than lifted from a leaderboard.
- **[MONEY]** Sources and receipts: plan changes from the June 25, 2025 announcement ; clients, models, Gateway and FAQ details from sourcegraph.com/docs/cody ; data terms from the Cody notice ; the $16K figure from sourcegraph.com/pricing ; repo status from cody-public-snapshot .
- **[MONEY]** Sourcegraph publishes no per-seat Cody price , so I've left out the ~$59/user/month figure on third-party review sites — no primary source confirms it.
- **[DATE/VERSION]** Which model does the work Cody routes to frontier cloud models: Claude Opus 4.8 through 4.5, Sonnet 5/4.6/4.5 and Haiku 4.5; Gemini 2.5 Pro, 3.1 Pro and 3.5 Flash; GPT-5.4 through GPT-5, GPT-4o and o3.
- **[DATE/VERSION]** Default chat is Sonnet 4.5.
- **[DATE/VERSION]** Outlier ships seven tiers you download once and run locally, from Nano 4B (2.37 GB) up to Plus 397B-a17b (209 GB, streaming experts from SSD at ~11 GB peak RSS).
- **[DATE/VERSION]** The coding tiers are Core and Code 27B: 15.13 GB, 24 GB of RAM, 20.7 tok/s on an M1 Ultra, weights published at huggingface.co/Outlier-Ai .
- **[DATE/VERSION]** Cody's client source isn't public any more: github.com/sourcegraph/cody 404s, and the Apache-2.0 cody-public-snapshot repo is archived, last pushed 2025-08-01.
- **[DATE/VERSION]** Code 27B scores 0.866 on HumanEval.
- **[DATE/VERSION]** Core 27B also matched Claude Opus on 98.9% of rubric checks across a 54-prompt head-to-head , and 100% on the nine hardest.
- **[DATE/VERSION]** It's also below what the strongest cloud coding agents resolve; on a hard multi-file bug, Sonnet 4.5 or Opus 4.8 lands the fix more often than a local 27B does.
- **[DATE/VERSION]** Opus 4.8 and GPT-5.4 don't care about your RAM, quantization or thermals, and the model list refreshes without re-downloading tens of gigabytes.
- **[DATE/VERSION]** All checked July 2026.
- **[DATE/VERSION]** Outlier numbers measured on an M1 Ultra (64 GB): SWE-bench Verified blind slice 18/40, HumanEval 0.866 on Code 27B, rubric parity in the 54-prompt benchmark ; pricing as of 2026-07-23.
- **[POLICY]** The Cody notice states Sourcegraph and its partner LLMs don't use code from Cody Enterprise or Pro teams to train models, and that partner LLMs retain no input or output, embeddings included, beyond the time it takes to generate the output.
- **[POLICY]** Fine-tuning is opt-in, and enterprises can bypass the Gateway with their own infrastructure.
- **[POLICY]** Contractual no-training on Enterprise code, zero retention beyond generation, opt-in fine-tuning, plus bring-your-own-key if you'd rather the vendor never see prompts.
- **[NUMBER]** Forty-five percent is a real result for a 15 GB model running with the network off.
- **[NUMBER]** It behaves the same on an 8 GB laptop as on a workstation; Outlier does not.
- **[NUMBER]** The coding tiers want 24 GB of RAM, and Outlier can't see a repository that isn't on your disk.

### `/vs/outlier-vs-tabnine/` — Outlier vs Tabnine: local Mac coding AI vs an enterprise cloud agent platform
- **[MONEY]** Outlier is a $20/month Mac app that runs the model on your own Apple Silicon: no account, no meter, nothing uploaded.
- **[MONEY]** These products barely overlap in shape — one is procurement software for engineering organizations, the other is a $20 app you download.
- **[MONEY]** What it actually costs Tabnine's pricing page lists the Code Assistant Platform at $39 per user/month and the Agentic Platform at $59, both annual — $468 or $708 per seat per year, with no free plan, tier, or trial shown.
- **[MONEY]** Headless Agents is a paid add-on, and the Enterprise Context Engine is sold separately at $5,800.
- **[MONEY]** Pro is $20/month or $149/year for all seven tiers, and lifetime Pro starts at $99.
- **[MONEY]** Side by side Tabnine Outlier Where it lives IDE plugins + terminal CLI + web admin console Standalone Mac app; no editor extension Model Tabnine's own, plus Claude / GPT-5.x / Gemini 3.x and open weights; bring-your-own endpoint Seven local tiers; Code 27B for coding Code leaves the machine Yes — remote GPU cluster; no-train, zero-retention policy; telemetry has no documented opt-out No — inference on device Works offline No documented offline mode Yes, with Wi-Fi off Cost $39 or $59/user/mo, annual; tokens at provider price + 5%; Context Engine $5,800 Free tier; $20/mo or $149/yr; lifetime from $99 Agentic ability IDE and CLI agents, headless CI/CD agents, admin policy, code review No headless agents, no CI, no admin console Repo-scale context Enterprise Context Engine, sold separately Bounded by local RAM Platforms Windows, Linux, macOS 13+ macOS 12+, Apple Silicon only Where Tabnine genuinely wins Frontier-model quality on demand.
- **[MONEY]** Pick Outlier if you're an individual developer or a small shop on Apple Silicon; $468 to $708 per seat plus metered tokens is out of proportion to your work; you want a physical guarantee that client code never leaves the laptop rather than a contractual one; or you'd rather pay $149 a year, or $99 once, with no meter running.
- **[DATE/VERSION]** Tabnine can route you to Claude Opus or GPT-5.x class models; Outlier's Code 27B measured HumanEval 0.866 and about 45% on a blind SWE-bench Verified slice, which is below the strongest cloud coding agents.
- **[DATE/VERSION]** Beyond its own proprietary hosted models, the docs list Anthropic Claude (4.8 Opus down through 4 Sonnet), OpenAI (GPT-5.5, GPT-5.3 Codex, GPT-4o), Google Gemini 3.x, plus open weights — Devstral, MiniMax-M2.7, GLM-4.7, Qwen-3-Coder-480B.
- **[DATE/VERSION]** For coding, most people sit on Code 27B: a 15.13 GB download that wants 24 GB of RAM.
- **[DATE/VERSION]** Six tiers are Apache 2.0 and the weights are published, so you can inspect what you're running.
- **[DATE/VERSION]** Code 27B measured HumanEval 0.866 , and on a blind slice of SWE-bench Verified it resolved about 45% (18 of 40) — my own measurement on my own hardware, not a leaderboard submission, and a 40-instance slice is noisy.
- **[DATE/VERSION]** Release notes show five releases in the first three weeks of July 2026.
- **[DATE/VERSION]** Checked 2026-07-23 — competitor pricing and policies change, so verify before you buy.
- **[DATE/VERSION]** Outlier's HumanEval 0.866 and ~45% (18/40) SWE-bench slice were measured by me on my own hardware; Core 27B's 98.9% rubric parity with Claude Opus is in the 54-prompt benchmark .
- **[POLICY]** Tabnine's data policy is genuinely strong for a cloud product, and I'll say so plainly: it does not train on your code, code is never retained on its servers, and context is deleted immediately after the server answers.
- **[POLICY]** But that's a policy, not physics — and telemetry still flows: plugin configuration, machine specs, hashed user identifiers, IDE details, completion stats, with no documented opt-out.
- **[POLICY]** There's nothing to retain.
- **[POLICY]** Who should pick which Pick Tabnine if you're buying for a team; you need completion inside JetBrains, Eclipse, or Visual Studio; you need agents running in CI; you need policy, license scanning, and audit trails to clear a security review; you have mixed Windows, Linux, and Mac engineers; or you want frontier-model quality with a written no-train, zero-retention commitment on top.
- **[NUMBER]** If Tabnine hands your hard multi-file refactor to Claude Opus, that's a stronger model than anything fitting in 24 GB of unified memory.

### `/vs/outlier-vs-text-generation-webui/` — Outlier vs text-generation-webui (oobabooga): two local AI apps compared
- **[MONEY]** Nano and Lite are free; Pro is $20/month or $149/year for all seven.
- **[MONEY]** Side by side text-generation-webui (TextGen) Outlier Interface Gradio UI in an Electron window + API server; CLI is config, not chat Native Mac window; no server, no CLI Who it's for Developers, tinkerers, self-hosters End users who want it to just work Setup Unzip, xattr -cr on macOS, then pick a model yourself Install, pick a tier, done Models Bring your own, from all of Hugging Face Seven curated tiers, 4B to 397B Bundled vs assembled App bundled, model assembled by you Both bundled Backends Five, swappable live (llama.cpp only on Mac) One, not user-selectable Platforms Windows, Linux, macOS (arm64 + x86_64) Apple Silicon Macs only Mobile No app; LAN browser via --listen None API OpenAI- and Anthropic-compatible None Licence AGPL-3.0, source available Closed app; weights public Price $0 Free tier, or $20/mo, $149/yr Where text-generation-webui genuinely wins It's free and it's yours.
- **[DATE/VERSION]** It's AGPL-3.0 and entirely free — no account, no subscription, no metering.
- **[DATE/VERSION]** It started in December 2022 and it's one of the largest projects in this space: 47,482 stars, ~5,980 forks, 836 open issues at the time of writing. v4.7 through v4.9 all shipped inside about three weeks in May 2026; v4.9 added MTP speculative decoding, web-search snippet extraction, and a live tokens-per-second readout.
- **[DATE/VERSION]** Five inference backends — llama.cpp, ik_llama.cpp, Transformers, ExLlamaV3 and TensorRT-LLM — swap without restarting, and the PC side gets separate portable builds for CUDA 12.4, CUDA 13.1, ROCm 7.2, Vulkan and CPU-only.
- **[DATE/VERSION]** Seven tiers ship with it, from Nano 4B (2.37 GB, 6 GB RAM, 71.7 tok/s on an M1 Ultra) through Core 27B and Code 27B up to Plus 397B-a17b, which streams experts from SSD at about 11 GB peak RSS.
- **[DATE/VERSION]** TextGen is a Gradio web UI wrapped, since v4.7.3, in a bundled Electron shell, so it opens in its own window rather than a browser tab.
- **[DATE/VERSION]** TextGen is AGPL-3.0 — read it, fork it, audit it, keep running your exact version forever regardless of what the maintainer does next.
- **[DATE/VERSION]** Core 27B matched Claude Opus on 98.9% of rubric checks across a 54-prompt head-to-head , and 100% on the nine hardest; the Code tier scores 0.866 on HumanEval.
- **[DATE/VERSION]** Sources and receipts: TextGen claims come from primary sources — the repo and README at github.com/oobabooga/textgen , the GitHub API repo record, the v4.9 and v4.7.3 release notes, requirements_apple_silicon.txt and docs/What Works.md .
- **[DATE/VERSION]** Repo statistics were read 2026-07-23 and change constantly.
- **[POLICY]** Both have opt-in network features that break that posture — TextGen's web search queries DuckDuckGo and --public-api routes traffic through a Cloudflare tunnel.
- **[NUMBER]** 47k stars, an extension ecosystem, a wiki and an active subreddit — somebody has already documented your problem.

### `/vs/outlier-vs-windsurf/` — Outlier vs Windsurf (Codeium): local coding AI vs a cloud agent IDE
- **[MONEY]** Paid subscribers can opt out on the Data Controls page, which also enables Zero Data Retention; the free tier has no documented opt-out.
- **[MONEY]** What you pay Devin Desktop: Free at $0 with a light agent quota and unlimited Tab completions; Pro at $20/mo, adding frontier models from OpenAI, Anthropic and Google plus cloud agents; Max at $200/mo for higher quotas; Teams at $80/mo base plus $40 per seat.
- **[MONEY]** You also can't compute what $20 buys in advance: quota numbers aren't published, only that your daily quota exceeds a seventh of your weekly one, and overflow is billed at API list prices.
- **[MONEY]** Outlier: the free tier is Nano and Lite, no account, no cap.
- **[MONEY]** Pro is $20/month or $149/year for all seven tiers; Lifetime Pro starts at $99.
- **[MONEY]** SWE-1.5 Code leaves machine No Yes, inference and indexing Trained on your data No Yes by default; opt-out paid only Works offline Yes No documented offline mode Cost Free; $20/mo, $149/yr, $99 lifetime; no caps Free; $20/mo; $200/mo Max; unpublished quotas Agentic ability Local loop; ~45% blind SWE-bench slice Local + cloud agents, subagents, MCP Repo-scale context Local RAM only; retrieval on device Cloud-indexed embeddings, whole repo Agentic ability and repo context: my honest receipts This is where Outlier is behind, and I'd rather say so up front.
- **[MONEY]** Pick Outlier if your code sits under an NDA or a rule that makes cloud indexing a non-starter; you want a structural guarantee rather than a toggle you pay to enable; you work offline; or you want a flat $149/year instead of usage-based overflow billing.
- **[DATE/VERSION]** Six are Apache 2.0, the weights are on Hugging Face, and on an M1 Ultra Nano runs about 71.7 tok/s and Core 27B about 20.7.
- **[DATE/VERSION]** Devin Desktop routes to a catalog Cognition puts at 150+ models on Pro and 276+ on Enterprise — OpenAI, Anthropic, Google, DeepSeek, Moonshot, Zhipu, Minimax, xAI — plus its own SWE-1.5/1.6/1.7, described as frontier-size at hundreds of billions of parameters and served on Cerebras at up to 950 tok/s.
- **[DATE/VERSION]** Credits became quotas in March 2026, with existing subscribers grandfathered indefinitely.
- **[DATE/VERSION]** Code 27B scores 0.866 on HumanEval .
- **[DATE/VERSION]** Throughput is the third — 950 tok/s on Cerebras against 20.7 on an M1 Ultra.
- **[DATE/VERSION]** Core 27B matched Claude Opus on 98.9% of rubric checks in a 54-prompt head-to-head — but that's general capability, not agentic coding.
- **[DATE/VERSION]** Sources and receipts: Every Devin Desktop claim comes from Cognition's own primary sources, checked 2026-07-23: windsurf.com's redirect, the product and rebrand pages, devin.ai/pricing, the docs for quota, Devin Local, ACP, remote indexing and models, and the Platform ToS.
- **[DATE/VERSION]** Outlier's numbers are mine: ~45% (18/40) on a blind SWE-bench Verified slice, 0.866 HumanEval, tok/s on an M1 Ultra.
- **[POLICY]** Its agent harness runs on your machine, but every model is vendor-hosted: your code goes to the cloud for inference and indexing, and training on it is the default unless you pay to opt out.
- **[POLICY]** Turn Wi-Fi off and it keeps working, and there's no training opt-out to hunt for because there's nothing to opt out of.
- **[POLICY]** Cognition's Platform Terms of Service, effective June 30, 2026, say it may use Customer Data for model training.
- **[POLICY]** One caveat: Cognition's enterprise security page says it does not train on customer data by default, contradicting those consumer terms — that page appears to cover enterprise deployments only.
- **[NUMBER]** A hundreds-of-billions-parameter model can't sit resident on a 16 GB laptop at all, and 950 tok/s on Cerebras is orders of magnitude past consumer Apple silicon.

### `/vs/outlier-vs-zed-ai/` — Outlier vs Zed AI: on-device Mac models vs a cloud-first code editor
- **[MONEY]** What it costs Zed's Personal plan is $0 — "$0 forever" on the pricing page — with 2,000 accepted edit predictions a month and unlimited AI use on your own keys.
- **[MONEY]** Pro is $10/month including $5 of tokens; past that it's API list price plus 10%, billed at month end or per additional $10 incurred, whichever comes first.
- **[MONEY]** Business is $30/seat/month with no seat minimum, no free trial and no bundled credits.
- **[MONEY]** The two-week Pro trial carries $20 of credits and excludes Anthropic's Opus models.
- **[MONEY]** Credit where it's due: in September 2025 Zed moved from 500 prompts a month to token billing and cut Pro from $20 to $10.
- **[MONEY]** Outlier's free tier is Nano and Lite, no account.
- **[MONEY]** Pro is $20/month or $149/year for all seven tiers, lifetime from $99.
- **[MONEY]** Side by side Zed AI (default) Zed AI (local config) Outlier Where it lives Editor + CLI; macOS, Linux, Windows Same editor Standalone Mac app (Apple Silicon) Model Claude / GPT / Gemini (closed); Zeta 7B for edit prediction Ollama, LM Studio, llama.cpp Seven on-device tiers, 4B to 397B-a17b Code leaves machine Yes, under zero-retention terms No No Cost $0 with own keys · Pro $10/mo · Business $30/seat $0 to Zed Free tier · Pro $20/mo or $149/yr · lifetime $99+ Agentic ability Agent panel, ACP agents, MCP servers Partial — no External Agents or Terminal Threads Chat-based; no in-repo agent Repo-scale context Frontier context windows Server-dependent; Ollama defaults 4096 tokens Bounded by your Mac's RAM Where Zed's AI genuinely wins Frontier reasoning on demand. ~45% on a blind SWE-bench Verified slice is below what the best cloud coding agents deliver.
- **[MONEY]** The free tier is usable, not a demo.
- **[DATE/VERSION]** It's open source under GPL-3.0-or-later (Apache-2.0 where marked), runs natively on macOS, Linux and Windows, and ships a CLI.
- **[DATE/VERSION]** The one open-weight piece is Zeta , the edit-prediction model — fine-tuned from Qwen2.5-Coder-7B, Apache-2.0, training dataset published on Hugging Face.
- **[DATE/VERSION]** Outlier ships seven tiers, all on your Mac: Nano 4B (2.37 GB, 6 GB RAM) through Code 27B (15.13 GB, 24 GB RAM) up to Plus 397B-a17b, which streams experts from SSD and wants 64 GB.
- **[DATE/VERSION]** Six are Apache 2.0; Quick is under the Gemma Terms of Use.
- **[DATE/VERSION]** Code 27B scores 0.866 on HumanEval .
- **[DATE/VERSION]** Core 27B did match Claude Opus on 98.9% of rubric checks across a 54-prompt head-to-head — but that's answer quality, not multi-step agentic repair.
- **[DATE/VERSION]** Outlier's context is bounded by the RAM in your Mac, and Plus 397B runs at 2.1 tok/s on an M1 Ultra — thorough, not quick.
- **[DATE/VERSION]** GPL-3.0-or-later for the whole editor, so you can read exactly what the AI integration sends and when.
- **[DATE/VERSION]** Sources and receipts: Zed plans and billing from zed.dev/pricing plus the September 2025 token-billing post; retention, training, model and local-runtime details from zed.dev/docs/ai/ ( privacy-and-security , ai-improvement , models , llm-providers , use-a-local-model , edit-prediction ); license and platform from zed-industries/zed ; Zeta from huggingface.co/zed-industries/zeta ; age and arbitration from Zed's March 2026 terms post.
- **[DATE/VERSION]** Checked July 2026 — competitor pricing and policies change, so verify at the source.
- **[POLICY]** Zed doesn't retain that data, and its hosted providers operate under zero-data-retention agreements — with one documented carve-out: provider-designated safety models keep data briefly, around 30 days, for safety review rather than training.
- **[POLICY]** Your input isn't used for training by default, and edit-prediction collection is opt-in behind three conditions, restricted to open-source-licensed projects, and admin-controlled on Business.
- **[NUMBER]** The local path is documented, but it's a configuration you opt into rather than the architecture — local edit prediction drops External Agents and Terminal Threads, and Ollama's context defaults to 4096 tokens unless you raise max_tokens .

### `/vs/qwen-vs-llama/` — Qwen vs Llama: open model families compared in 2026
- **[MONEY]** The developer free tier ended 2026-04-15, leaving a 1M-token trial valid 90 days.
- **[MONEY]** Who should pick which Pick Qwen if you're shipping commercial software with weights bundled or auto-downloaded, you need a size that fits a consumer Mac, or you want a cheap hosted escalation path — Qwen-Flash starts at $0.05 per million input tokens.
- **[MONEY]** No account, nothing uploaded, free tier included.
- **[DATE/VERSION]** Every Qwen open-weight model is Apache 2.0 and ungated, the line runs 0.8B to 397B, and three generations shipped since February 2026.
- **[DATE/VERSION]** Llama ships under Meta's own license — a 700-million-user commercial cap, an acceptable-use policy, a "Built with Llama" attribution rule and a manual-approval download form — and Meta has published no new open-weight base model since April 2025.
- **[DATE/VERSION]** Qwen is Apache 2.0.
- **[DATE/VERSION]** Outlier's Quick tier is Gemma-based, under Google's separate Gemma Terms of Use — so six of my seven tiers are Apache 2.0 Qwen, and Gemma is the one exception.
- **[DATE/VERSION]** Sizes, and what actually runs on a Mac Qwen's ladder is unusually complete: Qwen3.5 spans 0.8B, 2B, 4B, 9B, 27B, 35B-A3B, 122B-A10B and 397B-A17B, and Qwen3.6 added a 35B-A3B MoE plus a dense 27B in April 2026.
- **[DATE/VERSION]** Measured off my own build, not a spec sheet: Qwen3.5-4B is 2.37GB needing 6GB RAM (71.7 tok/s on an M1 Ultra, 32 on an M4 Air); Qwen3.5-9B, 5.04GB and 12GB; Qwen3.6-27B, 15.13GB and 24GB at 20.7 tok/s; Qwen3.6-35B-A3B, 19.0GB and 24GB; Qwen3.5-397B-A17B, 209GB and 2.1 tok/s on a 64GB machine, streaming experts from SSD.
- **[DATE/VERSION]** Llama's counterexample is real, though — Llama-3.2-1B-Instruct pulls ~10.4M a month, more than any single Qwen3.6 checkpoint, and Meta ships its own SpinQuant-INT4 and QLoRA-INT4 on-device builds.
- **[DATE/VERSION]** Side-by-side Axis Qwen (Alibaba) Llama (Meta) Newest weights Qwen3.6, April 2026 Llama 4, April 2025 Sizes 0.8B to 397B-A17B Llama 4: 109B, 400B; Llama 3.x: 1B to 70B License Apache 2.0 Llama 4 Community License Commercial cap None Above 700M monthly users Field-of-use limits None Acceptable Use Policy Attribution None "Built with Llama" plus naming rule Download gate Ungated Manual review, six fields Context / vision 262K, multimodal at 27B 10M on Scout, multimodal 16GB Mac Yes, through the 9B tier 3.2 1B/3B yes; Llama 4 no 64GB Mac Yes, through 397B-A17B 3.3 70B yes; Scout awkward Where each family genuinely wins, and where each falls down Qwen wins on license, ladder and cadence.
- **[DATE/VERSION]** Apache 2.0 across the whole open line is the cleanest legal posture a major lab offers.
- **[DATE/VERSION]** Qwen Code, the official terminal agent, is Apache 2.0 and points at a local Ollama or vLLM endpoint.
- **[DATE/VERSION]** Llama 3.3 70B has the widest hosted-provider availability of any open model.
- **[DATE/VERSION]** The newest artifact of any kind in Meta's Hugging Face org is dated 2025-04-28 — roughly fifteen months of nothing while Qwen shipped three generations. llama.com no longer exists; it redirects to developer.meta.com, a JavaScript shell where the license isn't server-rendered, so GitHub is now the reliable source.
- **[DATE/VERSION]** Cadence cuts both ways — Qwen3.5 shipped in February 2026 and was superseded in April, and Qwen3.6's config still carries a qwen3_5 architecture string, so pin an exact checkpoint.
- **[DATE/VERSION]** Pricing from Alibaba Cloud Model Studio, updated 2026-07-15.
- **[DATE/VERSION]** Download counts are 30-day figures read in July 2026 and move constantly.
- **[NUMBER]** There's a real Qwen for an 8GB, 16GB, 32GB and 64GB Mac.
- **[NUMBER]** A 4-bit Scout is well past 16GB, so on a Mac you fall back to Llama 3.x, where the 1B and 3B are excellent.
- **[NUMBER]** Long context plus vision at a size that runs 4-bit on a 32GB Mac is rare.
- **[NUMBER]** On base checkpoints: Qwen3.6-35B-A3B ~6.14M per 30 days against Scout's 462K and Maverick's 64K.

### `/vs/self-hosted-vs-on-device-ai/` — Self-hosting an LLM on a server vs running it on-device
- **[MONEY]** Side by side Axis Self-hosted server On-device Model size ceiling Effectively unbounded via tensor parallelism — 671B-class is servable Capped by installed memory; SSD paging extends it at a speed cost Concurrency Many simultaneous users per GPU via continuous batching One person at a time Memory bandwidth H100 SXM 3.35 TB/s; H100 NVL 3.9 TB/s at 94 GB Consumer unified memory, well below datacenter parts Recurring cost Hourly, forever — $0.69/hr (RTX 4090) to $4.29/hr (H100 SXM) and up Hardware you already own; no per-hour line Network Required for every token None after the model download Auth & security Operator-supplied: TLS, keys, rate limits, monitoring No listening endpoint to misconfigure Ops burden Cluster, storage, secrets, upgrades, on-call An app install Apple Silicon Second-class on the server stack The native target Where self-hosting genuinely wins These aren't concessions.
- **[MONEY]** The cost and ops math people skip RunPod Secure Cloud lists H100 PCIe at $2.89/hr and RTX 4090 at $0.69/hr, storage billed separately.
- **[MONEY]** Run either around the clock — 730 hours a month — and that's roughly $2,110/month for the H100 and roughly $504/month for the 4090.
- **[MONEY]** Lambda lists one H100 SXM at $4.29/GPU/hr (about $3,100/month) with no egress fees.
- **[MONEY]** Hugging Face Inference Endpoints, if you'd rather not touch metal, run $0.80/hr on an L4 up to $9.25/hr on a B200.
- **[DATE/VERSION]** Its Core tier is Qwen3.6-27B at 15.13 GB, needs 24 GB of RAM, and runs about 20.7 tok/s on an M1 Ultra.
- **[DATE/VERSION]** Its largest tier is a 397B-a17b MoE: a 209 GB download that needs a 64 GB Mac and pages experts off the SSD to hold peak RSS near 11 GB, at 2.1 tok/s.
- **[DATE/VERSION]** Worth noting the Core weights are Apache-2.0 Qwen3.6-27B, the same checkpoint you'd serve from vLLM.
- **[DATE/VERSION]** An H100 SXM moves 3.35 TB/s.
- **[DATE/VERSION]** Ollama binds 127.0.0.1 and its FAQ's answer for network exposure is Nginx, ngrok or Cloudflare Tunnel; auth is what the operator adds. vLLM's --api-key is a header check, a floor rather than a security model.
- **[DATE/VERSION]** Llama 3.3's license requires a separate license from Meta above 700 million monthly active users and mandates "Built with Llama" attribution.
- **[DATE/VERSION]** Qwen3.6-27B and gpt-oss-20b, by contrast, are plain Apache-2.0.
- **[DATE/VERSION]** License terms read from the Llama 3.3, DeepSeek-V3, Qwen3.6-27B, gpt-oss-20b and Open WebUI license files.
- **[DATE/VERSION]** GPU pricing and vendor policies change often — everything here was current as of 2026-07-23, so re-check the source pages before budgeting against them.
- **[NUMBER]** An AWS g6e.48xlarge, a common target, is eight L40S cards at 48 GB each: 384 GB of VRAM in one box.
- **[NUMBER]** DeepSeek-V3 is 671B total parameters with 37B activated per token; gpt-oss-120b needs an 80 GB GPU.
- **[NUMBER]** Open WebUI, the common self-hosted front end, is BSD-3-Clause plus a clause prohibiting altering or removing its branding unless you're under 50 end users per 30 days or hold written permission.
- **[NUMBER]** Run both if that's your actual week — a small on-device model for everything routine and confidential, a server for the jobs needing 671B parameters or forty concurrent requests.

### `/vs/unified-memory-vs-vram/` — Unified memory vs dedicated VRAM for LLM inference
- **[MONEY]** Side by side Apple silicon (unified) NVIDIA GB10 (unified) Discrete GPU (VRAM) Capacity Up to 512GB (M3 Ultra) 128GB LPDDR5x 32GB (5090) / 96GB (PRO 6000) Bandwidth 153–819GB/s by chip 273GB/s ~1,792GB/s (5090 figure secondary) What fits 600B-class, per Apple 200B, per NVIDIA What fits the card, then a cliff 7B Q4_0 prefill / decode 714 / 70 t/s (M4 Max) n/a 14,073 / 290 t/s (5090) Power 480W whole Mac Studio 140W SoC 575W card; 600W (PRO 6000) Price per GB of pool not verified ~$37 ~$62 / ~$89 (secondary) Upgrade path Soldered at purchase Fixed; two units link Swap, add cards, rent in cloud Thermals, power, and sustained load An RTX 5090 draws 575W for the card alone, with an 850W supply recommended; the PRO 6000 is rated 600W.
- **[MONEY]** Price per usable gigabyte Where official prices exist: DGX Spark's Founders Edition went from $3,999 to $4,699 in February 2026, which NVIDIA attributed directly to industry-wide memory supply constraints — about $37 per gigabyte of pool.
- **[MONEY]** The 5090's $1,999 launch MSRP is secondary-sourced, roughly $62/GB.
- **[MONEY]** Secondary reporting puts the 96GB PRO 6000 at $8,565 at launch, about $89/GB, and higher on NVIDIA's marketplace by mid-2026.
- **[MONEY]** Tom's Hardware reports Apple withdrew the 512GB option and raised the 96GB-to-256GB upgrade to $2,000 during the shortage.
- **[MONEY]** Secondary, unconfirmed at the vendor: the 5090's 1,792GB/s and $1,999 MSRP, PRO 6000 street pricing, the Mac Studio configuration changes, the 75% Metal working-set figure.
- **[DATE/VERSION]** Nano 4B 2.37 GB 6 GB Yes Lite 9B 5.04 GB 12 GB Yes Core 27B / Code 27B 15.13 GB 24 GB Yes Vision 35B-a3b 19.0 GB 24 GB Yes Plus 397B-a17b 209 GB 64 GB No Everything through 35B fits a 5090.
- **[DATE/VERSION]** The 397B tier doesn't, at any quantization worth running; on a 64GB Mac it works only because a paged mixture-of-experts loader streams experts from SSD, holding peak resident memory near 11GB at 2.1 tokens per second on an M1 Ultra.
- **[NUMBER]** Apple silicon has shipped up to 512GB at 819GB/s, while NVIDIA publishes 1,792GB/s over 96GB for the RTX PRO 6000 — so a 120B model runs on the big Mac and won't load on a 32GB RTX 5090 at all, while on models that fit both, the discrete GPU processes prompts around 20x faster.
- **[NUMBER]** Apple's M3 Ultra configures to 512GB at over 800GB/s (819GB/s per the Mac Studio specs), and Apple claims models over 600 billion parameters run on device.
- **[NUMBER]** DGX Spark ships 128GB of coherent memory at 273GB/s for inference up to 200B.
- **[NUMBER]** An RTX 5090 has 32GB; the RTX PRO 6000 has 96GB with ECC.
- **[NUMBER]** Here's what my app's tiers need: Model Download Min RAM Fits 32GB VRAM?
- **[NUMBER]** Slow, but it runs. llama.cpp's DGX Spark file shows the same shape on a mainstream model: 59 GiB of gpt-oss-120b at roughly 2,444 tokens/sec prefill, 59 tokens/sec generation.
- **[NUMBER]** Apple silicon: M4 Max 714 tokens/sec prefill and 70 tokens/sec generation; M2 Ultra 1,238 and 94.
- **[NUMBER]** Apple is closing the compute half deliberately: M5 puts a Neural Accelerator in every GPU core and claims over 4x M4's peak AI compute, with M5 Pro and M5 Max at 307GB/s and 614GB/s.
- **[NUMBER]** The PRO 6000's 96GB is ECC-protected; Apple's isn't.
- **[NUMBER]** Pick dedicated VRAM if your models fit in 32–96GB, time-to-first-token is what you feel most, you're serving multiple users, or you plan to fine-tune.
