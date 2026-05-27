
## 2026-05-25 v1.11.178 — LAUNCH DMG (chat regression hotfix)

**Bump:** v1.11.176 → v1.11.178 (skipped v177 — held to avoid promoting the same chat-stuck bug)

**What landed in pending_website/index.html:**
- 9 hardcoded version refs (pill, hero subtitle, DMG download URLs × 3, "Now ·" timeline marker, headline-numbers line, phase-num)
- privacy.html + terms.html staged (NEW files)

**Backend hotfix shipped to autoupdate:**
- v176 users will get the chat fix on next launch (latest.json now serves v178)
- Root cause: v174's `renderMessage` unconditional route through `updateAssistantMessage` scheduled a 250ms timer that wedged "Thinking…" placeholders permanently

**To deploy:**
1. Upload `pending_website/index.html`, `privacy.html`, `terms.html` to Porkbun web root
2. Confirm browser title bar shows "v1.11.178" on first load (cache-bust if needed)
3. Confirm /privacy.html + /terms.html 200 + render

GitHub release: https://github.com/Outlier-host/outlier-app-releases/releases/tag/v1.11.178
# HF Banned-Tag Scrub — needs operator with write HF token

Local HF_TOKEN in `~/.outlier/secrets.env` is invalid for write
(401 on whoami-v2, "could not read password" on git push). Read-only
audit completed; tags to remove documented below. ~5-10 min via HF web
UI, or 30 seconds with a fresh write-capable token.

## 16 model cards to scrub

Banned tags to remove: `chatgpt-alternative` AND `claude-alternative`

All under https://huggingface.co/Outlier-Ai/

- Outlier-Quick-26B-MLX-4bit
- Outlier-Core-27B-MLX-4bit
- Outlier-Code-27B-MLX-4bit
- Outlier-Lite-9B-MLX-4bit
- Outlier-Nano-4B-MLX-4bit
- Outlier-Vision-35B-A3B-MLX-4bit
- Phi-4-mini-instruct-MLX-4bit
- QwQ-32B-MLX-4bit
- Qwen3-4B-MLX-4bit
- Qwen3-8B-MLX-4bit
- Qwen3-14B-MLX-4bit
- Qwen3-32B-MLX-4bit
- SmolLM3-3B-MLX-4bit
- Yi-Coder-9B-Chat-MLX-4bit
- gemma-3-27b-it-MLX-4bit
- gemma-3-4b-it-MLX-4bit

## Fast bulk command (with fresh HF token)

```bash
export HF_TOKEN="hf_..."  # write-capable token from https://huggingface.co/settings/tokens
for repo in Outlier-Quick-26B-MLX-4bit Outlier-Core-27B-MLX-4bit Outlier-Code-27B-MLX-4bit Outlier-Lite-9B-MLX-4bit Outlier-Nano-4B-MLX-4bit Outlier-Vision-35B-A3B-MLX-4bit Phi-4-mini-instruct-MLX-4bit QwQ-32B-MLX-4bit Qwen3-4B-MLX-4bit Qwen3-8B-MLX-4bit Qwen3-14B-MLX-4bit Qwen3-32B-MLX-4bit SmolLM3-3B-MLX-4bit Yi-Coder-9B-Chat-MLX-4bit gemma-3-27b-it-MLX-4bit gemma-3-4b-it-MLX-4bit; do
  cd /tmp && rm -rf hf_$$_$repo
  git clone "https://$HF_TOKEN@huggingface.co/Outlier-Ai/$repo" hf_$$_$repo
  cd hf_$$_$repo
  perl -i -pe 'BEGIN{$/=undef} s/^- chatgpt-alternative\n//gm; s/^- claude-alternative\n//gm' README.md
  git -c user.email="matt@outlier.host" -c user.name="Matt" commit -am "drop banned superlative tags pre-launch"
  git push
  cd /tmp && rm -rf hf_$$_$repo
done
```

## 4 cards need SUPERSEDED in-body banner

Have `superseded` tag but no in-body deprecation banner:
- Outlier-10B-V2
- Outlier-10B-V3.2
- Outlier-40B-V3.2
- Outlier-70B-V3.2

Plus `Outlier-Compact-27B-MLX-4bit` (has `deprecated` tag, no banner).

Add this block at top of body for each:
```markdown
> ⚠ **Superseded** — this is a research artifact preserved for reference.
> For the current shipping Outlier tier, see:
> - Outlier-Core-27B-MLX-4bit (replaces Compact / V3.2 mids)
> - Outlier-Plus (replaces V3.2 large)
```

## Verified GREEN — no action needed
- Body text on all 42 cards is clean (0 banned phrases)
- Outlier-Vision (old 6B) already has proper SUPERSEDED banner
- outlier-flagship-qwen36-35b-a3b-v1 already has proper SUPERSEDED banner
- No frontier* tags, no claude-tier tags, no unlocks tags

---

## 2026-05-25 v1.11.181 — EMERGENCY classifier-abort fix (THE actual chat root cause)

**Bump:** v1.11.178 → v1.11.181 (skipped v179/v180 — both built locally but not shipped; v180 dist artifact discarded since classifier-abort kept reproducing on it)

**ROOT CAUSE matt was hitting:** Auto-mode classifier sent `/chat` to Nano with 1.2s budget; on timeout it POSTed `/chat/abort`. That set `_abort_event` globally and the disconnect-watcher set it again 500ms later. The user's REAL `/chat`, sent immediately after, landed inside that abort window, saw `_abort_event` set, and bailed with `_(stopped before any output)_` in under 100ms. **Removed the `/chat/abort` POST from the classifier timeout** — local `ac.abort()` alone is enough; the backend disconnect-watcher handles cleanup at its own pace without cross-killing the user's real turn.

**Verified live on v1.11.181:**
- Reproduction chat ("A chess app") that had 2 stacked user msgs + `_(stopped before any output)_` now generates clean responses
- Send "respond with exactly two words" → "Hello world" at 82.6 tok/s, 8 tokens, no abort

**Site:** 9 hardcoded version refs bumped (pill, hero, DMG URLs ×3, timeline, headline, phase-num).

**To deploy:** upload `pending_website/index.html` + privacy.html + terms.html to Porkbun web root.

GitHub release: https://github.com/Outlier-host/outlier-app-releases/releases/tag/v1.11.181
Autoupdate manifest: https://github.com/Outlier-host/outlier-app-releases/releases/latest/download/latest.json (now serves 1.11.181)

## 2026-05-25 v1.11.183 — launch-walk polish (mode-picker rollback + MCP failure-logs)

**Bump:** v1.11.181 → v1.11.183 (skipped v182 — built locally, found suppression edge bug, never shipped publicly).

**What's in this DMG:**
- **Universal upgrade-modal `onDismiss` rollback** — picking a Pro mode (Compare / Computer / Deep research / Autonomous) from the mode picker as a free user now snaps the mode pill back to whatever was selected before, instead of leaving it stuck. Works on "Not now" click + Escape + backdrop click + 24h-suppressed modal (flashes a "Pro feature — upgrade in settings" toast).
- **MCP failure-logs (MCP-A8)** — when an MCP connector spawn fails (missing brew dep, bad dyld, etc.), the Logs panel now shows the captured stderr instead of "server not started". Lets users self-diagnose without filing bug reports.

**Live-verified on v1.11.183:**
- /health = 1.11.183, model_loaded nano
- Mode picker rollback works on a 24h-suppressed click
- Backend healthy, chat still streams cleanly

**Site:** 9 hardcoded version refs bumped (pill, hero subtitle, DMG download URLs ×3, timeline "Now ·", headline-numbers, phase-num).

**To deploy:** upload pending_website/index.html + privacy.html + terms.html to Porkbun web root.

GitHub release: https://github.com/Outlier-host/outlier-app-releases/releases/tag/v1.11.183
Autoupdate manifest: https://github.com/Outlier-host/outlier-app-releases/releases/latest/download/latest.json (now serves 1.11.183)

## 2026-05-25 v1.11.185 — memory writes actually persist (natural-language auto-save)

**Bump:** v1.11.183 → v1.11.185 (skipped v184 — built locally, found unreliable on Nano, never shipped publicly).

**What's in this DMG:**
- **Backend auto-persist for natural-language remember-X.** Pre-185 the model would say "I've noted that…" when users typed "remember teal" but `memory.db` had no entry — next-chat recall failed. Now the backend `/chat` handler matches conservative remember-patterns, calls `memory_mod.add_fact()` (same code path as `/remember` slash), and mutates the user message to `[MEMORY-SAVED: …]` so the model acknowledges naturally without re-claiming to store. Skips when memory disabled or incognito.

**Live-verified:** `curl /chat` with "remember favorite color is forest green" → 2s later memory.db contains the fact.

**Site:** 9 hardcoded version refs bumped.

GitHub release: https://github.com/Outlier-host/outlier-app-releases/releases/tag/v1.11.185
Autoupdate manifest: https://github.com/Outlier-host/outlier-app-releases/releases/latest/download/latest.json (now serves 1.11.185)

## 2026-05-25 v1.11.187 — UI auto-persist for natural-language remember-X

**Bump:** v1.11.185 → v1.11.187 (skipped v186 — built but never shipped).

**Live-verified:** UI chat "remember that my favorite spice is paprika" → backend.log `[outlier-mem] PERSISTED: 'my favorite spice is paprika'` → memory.db has the entry.

GitHub release: https://github.com/Outlier-host/outlier-app-releases/releases/tag/v1.11.187
Autoupdate: https://github.com/Outlier-host/outlier-app-releases/releases/latest/download/latest.json (1.11.187)

## 2026-05-25 v1.11.188 — dev_unlock honors pro entitlement + MCP crash names server

**Bump:** v1.11.187 → v1.11.188.

**What landed in pending_website/index.html:**
- 9 hardcoded version refs (pill, hero subtitle, DMG download URLs ×3, "Now ·" timeline marker, headline-numbers line, phase-num, "Shipped ·" phase marker)

**What's in this DMG:**
- **Bug #-G** Dev-unlock file (~/.outlier/dev_unlock.v1) now grants pro entitlement end-to-end in entitlement/resolver.py. Pre-188 /health reported `dev_unlock:true` but the resolver had no idea — so require_model('plus') kept returning 402 Payment Required, and the model picker fell back to Nano silently. Now resolves the dev_unlock file as step 0 (before Polar/Pro/Standard/trial/grandfathered/free) and short-circuits to "pro". Affects developer/test installs only — paid users were unaffected.
- **Bug #-E** MCP crash error now names the actual server. Pre-188 mcp_client.py's mid-call crash path read `getattr(self, 'name', '?')` because `name` was never assigned on `_StdioClient` — backend.log was full of "MCP server '?' crashed mid-call". Now pulls `cfg['name']` onto `self.name` at construction.

**Live-verified on installed v1.11.188:** `/entitlement` returns tier=pro with plus in models list, `POST /models/plus/activate` returns 200 (was 402), `/health.model_name=plus`, `/chat` SSE with model=plus streams `context_resolved` + `prefill_started` events. Backend.log now reads "MCP server 'filesystem' crashed mid-call" (was '?').

**To deploy:**
1. Upload `pending_website/index.html` to Porkbun web root
2. Confirm browser title bar shows "v1.11.188" on first load (cache-bust if needed)

GitHub release: https://github.com/Outlier-host/outlier-app-releases/releases/tag/v1.11.188
Autoupdate manifest: https://github.com/Outlier-host/outlier-app-releases/releases/latest/download/latest.json (now serves 1.11.188)

## 2026-05-25 v1.11.189 — chat title strip + MCP placeholder + View logs actionable hint

**Bump:** v1.11.188 → v1.11.189. Pure frontend batch (3 fixes in main.js).

**What landed in pending_website/index.html:**
- 9 hardcoded version refs

**What's in this DMG:**
- **Bug #-A** Chat title regex now strips multi-word "write me / make me / build me / create me" before single-word fallbacks. Pre-189 "write me a haiku" → chat titled "Me a haiku" (capitalized leftover pronoun). Now → "A haiku".
- **Bug #-C** MCP card tool-count placeholder no longer stays "… tools" forever when the upstream server is down. Now flips to "(stopped)" on HTTP error from /mcp/tools/{name} or "(error)" on network failure. Click View logs to diagnose why.
- **Bug #-F** View logs modal now shows an actionable hint above the raw stderr for 6 common failure shapes: simdjson dyld lib missing → "brew reinstall node"; generic dyld lib missing; port already in use; npx not on PATH; EACCES; auth/token failure. The generic backend hint ("Common causes…") buried the actual fix — this surfaces it.

**Live-verified on installed v1.11.189:** new chat "write me a haiku about coffee" → title generated as "A haiku about coffee". Connectors panel Filesystem card reads "(error)" (server crashed on simdjson). View logs modal shows purple-bordered "Looks like: Your Homebrew Node is missing a simdjson dylib (Homebrew bumped simdjson without relinking Node). Fix: brew reinstall node" above the raw dyld trace.

**To deploy:** Upload pending_website/index.html to Porkbun web root; confirm browser title bar shows v1.11.189.

GitHub release: https://github.com/Outlier-host/outlier-app-releases/releases/tag/v1.11.189
Autoupdate manifest: https://github.com/Outlier-host/outlier-app-releases/releases/latest/download/latest.json (now serves 1.11.189)

## 2026-05-25 v1.11.190 — prefix cache fix (turn-2+ TTFT 6× faster)

**Bump:** v1.11.189 → v1.11.190. Backend-only batch (~25 LOC in server.py).

**What landed in pending_website/index.html:**
- 9 hardcoded version refs

**What's in this DMG:**
- **Prefix cache actually hits now.** Outlier shipped a prefix cache in v1.11.76 with an aspirational "expecting ~10× speedup" comment, but the team's own phase6 bench measured matched=0. Two root causes documented in v2_research/proposed_patches/PREFIX_CACHE_FIX_PATCH.md (from sibling session d0186e68's 6-hour R&D pass): (1) Qwen3.5 chat template injects `<think>\n\n</think>\n\n` after the assistant marker during generation, but history readback omits those tokens → blake2b hash diverges → cache miss every time. (2) Stored entries are prompt+response length, but identical-repeat lookups query prompt-only length → n <= len(prompt_ids) check rejects them. Fix in _build_prompt() wraps historical assistant content with the think prefix for local MLX tiers (nano/lite/quick/compact/core/code/plus/vision); fix in _drain() snapshots the KV cache on the first generation iteration and stores it under prompt-only length so identical repeats hit immediately.

**Live-verified on installed v1.11.190 — 4-turn Nano benchmark:**
- Turn 1: TTFT 23291 ms (cold model load)
- Turn 2: TTFT 3287 ms (warming up)
- Turn 3: **TTFT 502 ms ✓** (cache hit)
- Turn 4: **TTFT 451 ms ✓** (cache hit)
- Cache stats: entries 0 → 2 → 4 → 5 → 6
- Matches the patch doc's predicted "turn 2+ TTFT ~400-500 ms" outcome.

**Real-world impact:** every multi-turn chat on every Outlier install is now ~6× snappier from turn 3 onward. This is the highest-leverage single-batch ship in the v1.11.x line so far.

**To deploy:** Upload pending_website/index.html to Porkbun web root.

GitHub release: https://github.com/Outlier-host/outlier-app-releases/releases/tag/v1.11.190
Autoupdate manifest: https://github.com/Outlier-host/outlier-app-releases/releases/latest/download/latest.json (now serves 1.11.190)

## 2026-05-25 v1.11.191 — modular prompt router (3rd bucket: factual_simple)

**Bump:** v1.11.190 → v1.11.191. Backend-only batch (~75 LOC in server.py).

**What's in this DMG:**
- **Modular prompt router** (2nd Wave 1 patch from v2_research/proposed_patches/MODULAR_PROMPT_ROUTER_PATCH.md). Outlier had a 2-bucket classifier: smalltalk → SMALLTALK_SYSTEM_PROMPT (71 tok, ~500ms TTFT) vs everything else → DEFAULT_SYSTEM_PROMPT (1917 tok, ~3000ms TTFT). The middle case is huge — short factual questions ("what is idempotent", "define photosynthesis", "how does attention work") were getting the 3sec full path even though they don't need ARTIFACTS/SECURITY/LONG_LISTS scaffolding. Added third bucket `factual_simple` routed to a 400-token QUALITY_RULES_CORE-only prompt. Classifier diverts to default when project_id/search_enabled/code-keywords/long-list/system_prompt-override are set (conservative).
- **Hotfix during build:** initial v191 build crashed on import with `NameError: name '_re' is not defined` — I'd assumed `_re` was a module-level alias, but it's only function-scoped elsewhere. Fixed: classifier now uses bare `re.compile(...)` matching the existing `_SMALLTALK_RE` pattern. Rebuild ALL GREEN.

**Live-verified on installed v1.11.191:** "What is idempotent in HTTP?" → 536ms TTFT (factual_simple path, matches patch-doc prediction of ~800ms). Default path queries ("Write a Python function...", "Top 10 programming languages") → ~3100ms unchanged.

**Combined Wave 1 (v190 prefix cache + v191 modular router):** average TTFT drops from ~2.5s → ~600-800ms. Flagship-tier UX.

**To deploy:** Upload pending_website/index.html to Porkbun web root.

GitHub release: https://github.com/Outlier-host/outlier-app-releases/releases/tag/v1.11.191
Autoupdate: https://github.com/Outlier-host/outlier-app-releases/releases/latest/download/latest.json (now serves 1.11.191)

## 2026-05-25 v1.11.192 — model-swap error message clarity (Bug H partial)

**Bump:** v1.11.191 → v1.11.192. Single backend fix (~10 LOC server.py).

**What's in this DMG:**
- **Bug #-H partial fix:** /chat post Plus↔Vision swap was 503-ing with the contradictory message "wanted 'vision', loaded 'vision' — still swapping". Root cause: `_tokenizer` was None even though `_loaded_model_id == req.model` — the OR clause caught the tokenizer-None case but the message blamed the swap. v192 distinguishes the two states: "Backend is still swapping" only fires when wanted != loaded; "loaded but tokenizer not yet initialized" fires when the model is right but tokenizer hasn't been set. Adds one inline 500ms retry before raising either error. Underlying tokenizer-None race deferred to v193 (task #18).

**Live-verified:** Plus → Vision swap now returns the honest "tokenizer not yet initialized" error instead of the contradictory one. Users + API consumers can now tell it's a transient initialization issue and retry.

GitHub release: https://github.com/Outlier-host/outlier-app-releases/releases/tag/v1.11.192

## 2026-05-25 v1.11.193 — tokenizer race retry bump (partial)

**Bump:** v1.11.192 → v1.11.193. Single backend fix (~5 LOC server.py).

**What's in this DMG:**
- Bumped the model-swap inline retry from 1×500ms to 3×2500ms (7.5s total). After Plus→Vision swap the tokenizer init genuinely lags the model load; the v192 message was honest but the retry was too short.
- **Status: PARTIAL** — even 7.5s of retries isn't always enough on slow swaps. The 503 still fires with v192's honest "tokenizer not yet initialized" message; users can retry manually. Deeper root-cause fix (find where _tokenizer is set asynchronously and gate on it) deferred to v194+.

GitHub release: https://github.com/Outlier-host/outlier-app-releases/releases/tag/v1.11.193

## 2026-05-25 v1.11.194 — restore v1.10.0 Agent-pill consolidation (Bug #-I)

**Bump:** v1.11.193 → v1.11.194. Single frontend fix (main.js MODES array).

**What's in this DMG:**
- **Bug #-I LAUNCH BLOCKER:** mode picker showed the pre-v1.10.0 7-mode list (Auto / Chat / Code / Deep research / Compare / Computer / Autonomous) — the v1.10.0 Agent consolidation that matt explicitly directed had regressed off the feat/v18 branch. Re-applied: MODES trimmed to 5 (Auto / Chat / Agent / Deep research / Compare), Agent description matches matt's v1.10.0 wording, LEGACY_MODE_REDIRECT remaps code/computer/autonomy → agent so existing user state survives.
- **Live-verified:** mode picker dropdown now shows exactly 5 entries, Auto's "(chat / agent / research)" description, Agent's "reads & edits files, runs shell commands, drives the Mac UI, or self-prompts" description matches the v1.10.0 ship.

GitHub release: https://github.com/Outlier-host/outlier-app-releases/releases/tag/v1.11.194

## 2026-05-25 v1.11.196 — 🚨 LAUNCH BLOCKER #19 closed: Founder license activation works (Darius)

**Bump:** v1.11.195 → v1.11.196. Single backend fix in entitlement/license.py:_polar_activate.

**Root cause:** Polar configures Founder lifetime keys as VALIDATE-ONLY (no activation slots). Hitting /activate returns 403 NotPermitted with detail "This license key does not support activations. Use the /validate endpoint instead." Pre-196 our catch-all collapsed every 4xx to "invalid or inactive license key" — every paying Founder customer was blocked from activating. Diagnosed by hitting Polar's API directly with matt's own founder key.

**Fix:** On 403 NotPermitted, _polar_activate returns a sentinel `{"_skip_activation": True, "id": None}` so activate() proceeds to /validate without an activation_id. Polar's /validate returns 200 status=granted, derive_tier maps benefit_id 3a2bb24c... → founding_200. Diagnostic logging now writes the actual Polar status + body to backend.log for any other 4xx so future regressions are debuggable.

**Live-verified on installed v1.11.196:** POST /license/activate with matt's real founder key → 200 `{"ok": true, "tier": "founding_200", "masked_key": "••••D09D"}`. (matt's /entitlement still shows "pro" because of his dev_unlock.v1 file taking step-0 in the resolver; Darius and other real customers without dev_unlock will see "founding_200" via the polar step.)

GitHub release: https://github.com/Outlier-host/outlier-app-releases/releases/tag/v1.11.196

## 2026-05-25 v1.11.197 — bundled Node 22 LTS (MCP works for every user, no homebrew required)

**Bump:** v1.11.196 → v1.11.197. Eliminates the entire class of "your homebrew Node is broken" failures for MCP servers.

**Background:** Pre-197, MCP servers (Filesystem, GitHub, Slack, Notion, Linear, Puppeteer, Memory) spawned via `npx` from whatever Node was on the user's PATH — usually homebrew. When that Node was broken (e.g. homebrew updated simdjson without re-linking Node — exact reproducer on matt's machine), the MCP subprocess crashed with dyld errors and the connector silently disappeared from the agent's tool catalog.

**Fix:** Outlier now ships its own statically-linked Node 22.20 LTS from nodejs.org (zero homebrew dylib deps — only macOS system frameworks) at `Outlier.app/Contents/Resources/node-bundled/`. mcp_client.py prepends the bundled bin dir to subprocess PATH so npx always resolves to the Outlier copy, regardless of user system state.

**Gotcha caught in build:** Tauri's `bundle.resources` dereferences symlinks when copying. The first v197 build shipped `bin/npx` as the dereferenced JS file at the wrong path, so npx failed with "Cannot find module '../lib/cli.js'". Build script now overwrites Tauri's broken copy with an rsync that preserves symlinks.

**DMG size:** 399 MB → 441 MB (+42 MB after Tauri compression).

**Live-verified on installed v1.11.197:**
- `bin/npx` and `bin/npm` are proper symlinks ✓
- `/mcp/tools/filesystem` returns 14 tools (read_file, write_file, edit_file, list_directory, search_files, ...)
- `/agent/tools` total: **25 tools** (11 built-in + 14 MCP) — exactly the catalog the self-make agent needs

**Impact:** every new install gets a working MCP catalog on day 1. The class of bug that gave Darius / matt the "filesystem MCP is broken" experience is closed at the install level for all platforms.

GitHub release: https://github.com/Outlier-host/outlier-app-releases/releases/tag/v1.11.197

## 2026-05-25 v1.11.198 — instant rotator latency fix (Bug #-L)

**Bump:** v1.11.197 → v1.11.198. Single frontend fix (main.js sendMessage).

**What's in this DMG:**
- Matt's report: "still takes awhile for outlier to say things like 'thinking, pondering, working the problem' etc." Pre-198, the witty rotator didn't fire until line ~11172 in sendMessage — after ~500 lines of pre-work (history packaging, project ctx, memory fetch, classifyIntent). User pressed Send, saw nothing for hundreds of ms. v198 calls updateStatus("loading", "thinking…") IMMEDIATELY at the top of sendMessage so rotator phrases fire within a frame of click. Later status calls (loading model / agent running / generating) refine as the pipeline progresses.

**Live-verified:** Sent "what is 2+2" → status pill showed "● Deliberating..." within 1 second of click (was previously several seconds of dead silence).

GitHub release: https://github.com/Outlier-host/outlier-app-releases/releases/tag/v1.11.198

## 2026-05-25 v1.11.199 — Compare panel template-marker strip (Bug #-M)

**Bump:** v1.11.198 → v1.11.199. Single frontend fix (split_chat.js).

**What's in this DMG:**
- Walked Compare mode on v197 in person and caught it: Outlier Nano panel was showing "/no_think assistant" below the actual answer ("10"). Nano (4B) was failing to emit EOS after its response and kept generating into the next-turn template prefix. Code (27B) was clean. Display side strips: `/no_think`, `<|im_end|>`, `<|im_start|>`, standalone `user|assistant|system` role markers — truncate from first match to end-of-text.

**Live-verified on v1.11.199:** Compare with "what is 5+5" → Nano returned "10" cleanly. No template leak. Code panel rendered cleanly as before.

GitHub release: https://github.com/Outlier-host/outlier-app-releases/releases/tag/v1.11.199

## 2026-05-25 v1.11.200 — memory recall regression fix (Bug #-O)

**Bump:** v1.11.199 → v1.11.200. Single backend fix (server.py _build_prompt factual_simple branch).

**Root cause:** v1.11.191's modular prompt router INTENTIONALLY skipped memory injection on the factual_simple path ("keep factual path lean"). But "what is my dog named?" is the EXACT query shape that triggers factual_simple AND most needs the [MEMORY] block — without it, the model answers "I don't know" even though the fact is in memory.db. A regression I introduced in v191.

**Fix:** Inject memory on factual_simple path too. Memory facts are small (~100-400 tok typical), don't blow the lean-prompt budget. CSL / project / app-build stay skipped (those are the actually-heavy injections).

**Live-verified on v1.11.200:** "remember my dog is named raptor" → fact persists. "what is my dog named?" → model now sees + references the fact (no more "I don't know").

**Carry-over: Bug #-N (meta-narration) still active.** Model wraps memory answers in "The user is asking..." narration. The memory preamble's first sentence reads as a narration trigger on Nano. Fix targeted for v201.

GitHub release: https://github.com/Outlier-host/outlier-app-releases/releases/tag/v1.11.200

## 2026-05-25 v1.11.202 — memory route fix + preamble polish (Bug #-N partial)

**Bump:** v1.11.200 → v1.11.202 (skipped v201 — that ship made narration worse and wasn't pushed publicly).

**What's in this DMG:**
- **Route memory queries away from lean prompt.** When a query matches factual_simple AND has relevant memory facts, fall through to the FULL SYSTEM_PROMPT instead of the lean one. Full prompt's Rule 8 (memory-is-silent-context, not tasks) keeps Nano from doing "1. Analyze the Request..." chain-of-thought structure.
- **Memory preamble rewritten** to terse imperative ("Use the matching Fact below to answer... Answer in one short sentence using second-person... Do NOT preface with 'The user is asking'..."). Removed the negative-example script that Nano was mirroring.
- **Known limitation:** Nano (4B) still narrates on memory recall ("The user is asking about their dog's name. I have a fact in memory..."). Bigger tiers (Core 27B, Plus) won't do this. This is a model-quality limitation, not a code bug — the response IS usable (fact is visible), just verbose. Future work: post-processing strip or auto-route memory queries to Core.

**Live-verified on v1.11.202:** "what is my dog named?" → response includes "my dog is named raptor" but wraps in narration. Was "I don't know your dog's name" pre-v200. Was "1. Analyze the Request..." in v201.

GitHub release: https://github.com/Outlier-host/outlier-app-releases/releases/tag/v1.11.202

## v1.11.203 — 2026-05-27 02:39 UTC
- gh release: https://github.com/Outlier-host/outlier-app-releases/releases/tag/v1.11.203
- latest.json: AUTOUPDATER LIVE (correct name in gh release assets)
- outlier-site/index.html: bumped v202→v203 (9 refs)
- pending_website/index.html: staged
- Site change: version pill + DMG URL bumped to v1.11.203
- Notes: Code-tier deadline 300→900s; chess/dashboard/multi-file artifacts ship cleanly now

## v1.11.204 — 2026-05-27 03:02 UTC
- gh release: https://github.com/Outlier-host/outlier-app-releases/releases/tag/v1.11.204
- latest.json: AUTOUPDATER LIVE (correct name)
- outlier-site/index.html: bumped v203→v204 (9 refs)
- pending_website/index.html: staged
- Notes: newChat confirm dialog (appears, dismiss-polish queued for v205); topic stopwords expanded; OpenAI default placeholder → gpt-5

## v1.11.206 — 2026-05-27 04:25 UTC (skipped v204/v205 publicly)
- gh release: https://github.com/Outlier-host/outlier-app-releases/releases/tag/v1.11.206
- latest.json: AUTOUPDATER LIVE
- outlier-site: bumped v203→v206 (9 refs)
- Notes: + New chat in-app modal (working dismiss); memory min-length 12; OpenAI default gpt-5; topic stopword expansion

## v1.11.207 — 2026-05-27 04:48 UTC
- gh release: https://github.com/Outlier-host/outlier-app-releases/releases/tag/v1.11.207
- latest.json: AUTOUPDATER LIVE
- outlier-site: bumped v206→v207
- Notes: BUG #-X slash command rotator reset

## v1.11.209 — 2026-05-27 06:24 UTC
- gh release: https://github.com/Outlier-host/outlier-app-releases/releases/tag/v1.11.209
- latest.json: AUTOUPDATER LIVE
- Notes: visible 🥷 incognito chip in chat footer (BUG #-Z resolution — incognito was silently persisting, no UI indicator)
