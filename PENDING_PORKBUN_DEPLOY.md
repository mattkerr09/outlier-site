
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
