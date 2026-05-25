
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
