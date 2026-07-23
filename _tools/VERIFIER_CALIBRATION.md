# Round-1 verifier calibration — READ BEFORE ACTIONING ITS "FABRICATION" LIST

Hand-checked 7 concrete "fabrication" blockers from the round-1 verify pass against primary
sources on 2026-07-23. **Six of seven were actually TRUE (~85% false-positive rate).** The verifier's fabrication list is
heavily contaminated with false positives, almost all on facts dated AFTER early 2026 (i.e. after
the model's own knowledge horizon). When its WebFetch to a primary source 403s (openai.com,
google blogs do this), it concludes "unverifiable → fabrication" — wrongly.

| Flagged claim | Truth | Source | Verdict on verifier |
|---|---|---|---|
| NotebookLM / native Gemini app for Mac, April 2026 | TRUE — launched 15 Apr 2026 | 9to5google, workspaceupdates.googleblog.com | FALSE POSITIVE |
| M365 Copilot runs GPT-5.6 (as of July 2026) | TRUE — preferred model 9 Jul 2026 | openai.com, techcommunity.microsoft.com, TechCrunch | FALSE POSITIVE |
| DeepSeek has no official desktop app; desktop apps are unofficial wrappers | TRUE — official = web/Android/iOS only | Wikipedia, vendor | FALSE POSITIVE |
| Otter.ai Mac/Windows desktop app, announced Oct 2025 | TRUE — announced 7 Oct 2025 | otter.ai/blog, DevX, LinkedIn | FALSE POSITIVE |
| GitHub Copilot auto-downgrades to Free when plan ends | TRUE | docs.github.com | FALSE POSITIVE |
| Enchanted "last functional commits 2025-03-18" | FABRICATED — real latest commit 2026-07-07 ("Link to Jaz successor project") | api.github.com/repos/gluonfield/enchanted | CORRECT — **fixed by hand** |

## Rule for the round-2 repair pass
1. NEVER delete a claim just because a primary-source fetch failed. Corroborate with WebSearch first.
2. A specific, plausible, post-2026 fact is MORE likely true than fabricated — treat "I can't confirm"
   as "leave it and flag low-confidence", NOT "delete".
3. These are CONFIRMED TRUE — do not touch: the Gemini Mac app (Apr 2026), GPT-5.6 in M365 Copilot,
   DeepSeek desktop apps being unofficial wrappers.
4. Only DELETE/rewrite a claim that WebSearch actively CONTRADICTS (like the Enchanted commit date).

## GROUND-TRUTH CORRECTIONS (my batch spec was wrong — verified against shipping code 2026-07-23)
- **Outlier HAS web search + deep research** (Pro, opt-in): `main.js` "web research is part of pro", "deep research is part of pro"; backend `outlier/research/providers/{brave,duckduckgo,searxng}.py` + `fetch_url` + `web_search` in both compat layers. My batch OUTLIER_FACTS said "NO live web search" — WRONG. Fixed 9 pages that flatly denied it (kept the accurate "Pro-only, opt-in, query leaves the machine" framing on perplexity/grammarly).
- **Outlier HAS TTS narration** (`/tts/speak`, T10.ttsCfg in main.js) — reads answers aloud. So "no voice mode" is only defensible as "no conversational voice mode"; the notebooklm page's precise "voice exists but limited to narration" is more accurate.
- Third occurrence of [[feedback-verify-fact-sheets-against-shipping-code]] this session — ground ANY capability claim (has/hasn't X) against main.js + backend, never memory.

## FINAL /vs/ ADJUDICATION
10 residual confirm-agent flags across 8 pages: **9 were true post-cutoff facts** (GPT-5.6, Otter Oct-2025, GitHub 65-lexemes + auto-downgrade, NotebookLM Gemini-Mac-app + voice/TTS, DeepSeek wrappers, Notion Credits May-4-2026, Meta One) — all verified TRUE via WebSearch, left in place. **1 genuine fabrication**: Copilot "Brazil/South Korea/Vietnam auto-exclusion" (Brazil & Vietnam are supported) — REMOVED.
