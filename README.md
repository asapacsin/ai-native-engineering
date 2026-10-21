# AI-native Engineering (Executor-first + End-State Reviewer)

Reusable, testable workflow distilled from the Android automotive voice-agent and Aurel game. **Not just prompts:** the Python controller runs real commands, records evidence tied to source fingerprint, hands a packet to an external read-only reviewer, and enforces `PASS | REWORK | BLOCKED | NOT_VERIFIED` with bounded retries.

## Verify this repository

```bash
python3 -m unittest discover -s tests -v
python3 scripts/ai_native.py validate --contract examples/contract.json
```

## Drive a project

1. Copy and edit `examples/contract.json` (or start with `adapters/aurel.json` / `adapters/android.json`).
2. Configure `AI_NATIVE_EXECUTOR_CMD` (optional) and `AI_NATIVE_REVIEWER_CMD` (required for PASS) to **real authenticated external agent CLIs**; see `scripts/codex_bridge.py` for a working Codex CLI adapter with explicit Luna Medium / Astra High model flags. Prompts alone do not invoke an LLM.
3. Run `python3 scripts/ai_native.py cycle --repo /path/to/project --contract /path/to/contract.json`.
4. Examine `.ai-native/runs/<task-id>/latest.json`, gate logs, review packet and decision. On REWORK, target the changed files and re-verify; do not accept an unsupported green build as E2E proof.

Default: **low-cost Executor → deterministic end-state checks → stronger independent Reviewer → targeted Executor retry**. Escalate to Architect only when important uncertainty warrants it. `max_attempts` and `max_total_seconds` prevent runaway spending.

See [AI Builder Bible](docs/AI_BUILDER_BIBLE.md) and [exact integration instructions](docs/INTEGRATION.md).

## File map

| Path | Role |
| --- | --- |
| `scripts/ai_native.py` | executable bounded orchestration, gate evidence, commit + dirty-source fingerprint |
| `scripts/codex_bridge.py` | optional actual Codex executor (Luna) / independent reviewer (Astra) subprocess adapters |
| `.claude/hooks/ai-native-stop.py` | opt-in end-state Stop hook, guards recursive loops |
| `examples/contract.json` | sample spec/acceptance/budget/CLI gate contract |
| `adapters/aurel.json`, `adapters/android.json` | source-specific gate examples; not a claim those apps were tested here |
| `tests/` | controller behavioral tests including false PASS and stale review rejection |
| `.github/workflows/ci.yml` | CI for the portable controller |
| `scripts/publish.ps1` | create **private** `asapacsin/ai-native-engineering` and push from Windows with `gh` CLI |

## Publishing to GitHub (Windows)

Download and extract the ZIP, open PowerShell in the extracted `ai-native-engineering` folder. Install Git and GitHub CLI (`winget install --id Git.Git -e` and `winget install --id GitHub.cli -e`) if missing. Then:

```powershell
gh auth login
.\scripts\publish.ps1
```

The script creates a private `asapacsin/ai-native-engineering`, initializes Git only if needed, commits the files, and pushes. It **will not overwrite an existing remote repository**. `gh auth login` should use the GitHub account that controls `asapacsin`. See the source references in the Bible. No repository is claimed to be online until the GitHub creation/push is confirmed.
