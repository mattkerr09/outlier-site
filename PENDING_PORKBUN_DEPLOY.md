
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
