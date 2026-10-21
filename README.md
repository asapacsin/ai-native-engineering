# AI-native Engineering (Executor-first + End-State Reviewer)

> **Coverage status (2026-10-21): INCOMPLETE.** This is a portable controller starter, **not** the full engineering harness used across Android, Aurel, and Edria. The [practice-by-practice audit](docs/PRACTICE_COVERAGE.md) identifies missing approval/scope enforcement, autonomous work discovery, reviewer-before-merge, human validation batching, acceptance provenance, checkpoints and domain-specific adapters. Do not treat a passed controller test or a posted README as production verification.

Reusable, testable workflow distilled from the Android automotive voice-agent and Aurel game. **Not just prompts:** the Python controller runs real commands, records evidence tied to source fingerprint, hands a packet to an external read-only reviewer, and enforces `PASS | REWORK | BLOCKED | NOT_VERIFIED` with bounded retries.

## Verify this repository

```bash
python3 -m unittest discover -s tests -v
python3 scripts/ai_native.py validate --contract examples/contract.json
```

## Enforced governance and autonomous frontier

The local tooling now includes contract-hash approval, scoped paths, exact-tip merge eligibility and independent requirement-scope checks (`scripts/governance.py`), and a dependency-aware autonomous frontier with deferred human tasks and a two-clean-pass human gate (`scripts/frontier.py`). **Neither component is an installed GitHub branch rule or an automatically running multi-agent service.**

See **[operational enforcement commands](docs/ENFORCEMENT.md)** and the [practice coverage audit](docs/PRACTICE_COVERAGE.md) for the remaining gaps.

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

## This repository is published

This repository is hosted at [asapacsin/ai-native-engineering](https://github.com/asapacsin/ai-native-engineering). The original bootstrap-only publishing script is retained for historical/reference purposes and deliberately refuses to overwrite this existing repository. Review the [coverage audit](docs/PRACTICE_COVERAGE.md) before claiming all source-project practices are implemented.
