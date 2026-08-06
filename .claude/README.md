# `.claude/` — session tooling

Added 2026-08-06 from the Claude Code usage report, by the monitoring chat.
Everything here encodes a ritual the owner already runs by hand; none of it
changes what the project believes.

| Path | What |
|---|---|
| `settings.json` | PreToolUse hook: refuses a commit with a staged file over 5 MB |
| `hooks/block_large_staged_files.ps1` | the hook's actual logic — a file, not an inline string |
| `skills/close-session/SKILL.md` | `/close-session` — land deliverables, sync docs, commit, push |
| `skills/analyze-capture/SKILL.md` | `/analyze-capture` — safely ingest a log or stat export |

---

## 🛑 THE HOOK IS UNVERIFIED. Verify it before trusting it.

**It was written by a chat with no Windows shell, so it has never executed.** That is
exactly the state this project treats as dangerous: a guard that is documented but not
demonstrated gets *reported as satisfied*. `3d` found three of those. **Until the test
below has been run, assume the hook does nothing.**

Test it — from the repo root, in PowerShell:

```powershell
# 1. it must pass cleanly with nothing staged
powershell -NoProfile -File .claude\hooks\block_large_staged_files.ps1 ; $LASTEXITCODE

# 2. it must BLOCK (exit 2) on a large staged file
fsutil file createnew big.tmp 6291456
git add big.tmp
powershell -NoProfile -File .claude\hooks\block_large_staged_files.ps1 ; $LASTEXITCODE
git reset big.tmp ; Remove-Item big.tmp
```

Expected: **0** then **2**. If the second run prints 0, the hook is inert — fix it or
delete it, but do not leave it in place looking like protection.

### Two defects in the version the usage report suggested, fixed here

1. **It fired on every `Bash` call.** The report's matcher is `"Bash"` with the git
   command inline, so a `git diff --cached` ran before *every single* shell command —
   including in directories that are not a git repo, where it errors. The script here
   exits immediately when nothing is staged, which makes the common case nearly free,
   but the matcher is still tool-wide; that is a Claude Code limitation, not a bug.
2. **The inline quoting could not survive `cmd.exe`.** The report nests `\"…\"` inside
   `-Command "…"`, which is not how Windows escapes quotes. Moving the logic into a
   `.ps1` and invoking it with `-File` removes the quoting problem entirely.

Both are recorded because inheriting a suggestion unchecked is the failure this repo
spends most of its discipline avoiding.
