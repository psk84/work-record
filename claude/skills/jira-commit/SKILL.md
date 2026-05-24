---
name: jira-commit
description: Create Git commits in the user's mandatory Jira + Conventional Commits format `[{JIRA-KEY}] {type}: {message}`. Use whenever the user asks to commit, amend, or push — across any repository. Types are feat, bug, fix, docs, chore, refactor. The Jira project is SINCE at https://since0523.atlassian.net. If no Jira key is provided in context, ask before committing.
---

# Jira Commit Format

The user requires every commit (across all repos) to follow this exact format:

```
[{JIRA-KEY}] {type}: {subject}

{optional body, wrapped at ~72 chars}
```

## Rules

1. **Subject prefix is mandatory**. `[SINCE-N]` then a space, then `{type}: {subject}`.
2. **Type is one of**: `feat`, `bug`, `fix`, `docs`, `chore`, `refactor`.
   - `feat`     — new functionality / new code artifact (e.g. a Terraform module, a new pipeline)
   - `fix`/`bug` — bug fix (use whichever matches the project's existing convention)
   - `docs`     — documentation, presentation/learning materials, README, comments-only
   - `chore`    — tooling, build, dependencies, CI
   - `refactor` — code restructure with no behavior change
3. **Separator** between type and message is `: ` (colon + space).
4. **Subject line** stays imperative, lowercase after the colon, under ~72 chars (`feat: add ...` not `Add ...`).
5. **Body** (optional) explains the *why*. Wrap at ~72 chars. Preserve any existing body when only rewording the subject.
6. **Co-authored-by trailers** are kept as-is when amending.

## When to ask vs assume

- Ask for the Jira key if **none** is in the conversation context. Never invent a key.
- If a Jira key is already established in the current conversation or recent commits, **reuse it without asking**.
- If the user names a different key, switch to that key.

## Type selection guide

If type isn't given by the user:

| If the commit primarily… | use |
|---|---|
| adds a new feature, new resource, new pipeline, new deliverable | `feat` |
| fixes a bug or wrong behavior | `fix` (or `bug` if user uses that) |
| only changes docs/markdown/comments/presentation | `docs` |
| touches tooling / build / deps / config / CI | `chore` |
| restructures code without behavior change | `refactor` |

If multiple types fit, **pick the dominant change** and put the rest in the body.

## How to apply (operational)

### New commit
- Stage only intended files (never `git add -A` blindly; never commit secrets, state, `.env`).
- Use HEREDOC to preserve formatting:
  ```bash
  git commit -m "$(cat <<'EOF'
  [SINCE-N] type: subject line
  
  Body paragraph one explaining why.
  
  Co-Authored-By: ...
  EOF
  )"
  ```

### Amending the most recent commit (only when user explicitly asks)
- `git commit --amend -m "$(cat <<'EOF' ... EOF\n)"`
- Preserve the original body when only the subject prefix is being added.
- If the commit was already pushed: warn that `--force-with-lease` is required, and proceed only if user has confirmed.

### Rewriting multiple commits
- Use `git rebase -i` with care. Never use `-i` flag directly (no interactive); instead set `GIT_SEQUENCE_EDITOR` and `GIT_EDITOR` to non-interactive scripts.
- Confirm with user before rewriting more than the most recent commit.

## What NOT to do

- Never invent Jira keys.
- Never commit secrets (API tokens, AWS keys, passwords) — flag and abort.
- Never `git add .` or `git add -A` without inspecting `git status` first.
- Never `--no-verify` to skip hooks unless user explicitly asks.
- Never force-push to a shared branch (main, develop) without explicit confirmation.

## Examples

Good:
- `[SINCE-7] feat: add initial Terraform setup with VPC foundation`
- `[SINCE-7] docs: add aws-terraform tech-analysis docs (setup through VPC)`
- `[SINCE-7] docs: add HTML/MP4 presentation for VPC build work`
- `[SINCE-12] fix: correct NAT Gateway pricing in variables.tf description`
- `[SINCE-15] chore: bump aws provider to 5.31`

Bad:
- `Add VPC` (no Jira key, no type, capitalised)
- `[SINCE-7] Add VPC` (no type)
- `feat: add VPC` (no Jira key)
- `[SINCE-7] feat:add VPC` (missing space after colon)
- `[SINCE-7] update: misc fixes` (`update` is not an allowed type)

## Reference

- Jira project: https://since0523.atlassian.net/browse/SINCE
- Each ticket: `https://since0523.atlassian.net/browse/SINCE-{N}`
