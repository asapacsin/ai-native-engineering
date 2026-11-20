# AI Builder Bible — shared reusable operating system

## Objective

Increase *validated useful outcomes per dollar and hour*, not tokens consumed or agents spawned. Human defines outcomes, architecture boundaries and risk appetite; software runs deterministic verification; independent AI reviewer is called only at the end-state and for substantive decisions.

## Default control loop

```text
Human-approved spec + cost/acceptance contract
                 |
                 v
       low-cost Executor (default)
                 |
                 v
     deterministic end-state trigger
          |             |
  unit/build/replay   fingerprint of HEAD + dirty/untracked state
          |             |
          +---- evidence packet ----+
                                    |
                        independent strong Reviewer
                                    |
                   +----------------+------------------+
                   |                |                  |
                PASS             REWORK        BLOCKED/NOT_VERIFIED
                   |                |                  |
              accept task    targeted task for   record precise
              + find next    Executor (bounded)   dependency/proof gap
```

The Reviewer MUST actually be invoked through an external client (for example a configured Codex CLI invocation) and given a read-only role/prompt. Merely setting `model_policy.independent_reviewer = Astra` does not call that model. See `docs/INTEGRATION.md`.

## Model policy

| Role | Default strategy | When invoked |
| --- | --- | --- |
| Executor | capable economical model such as GPT-6 Luna Medium | Most coding, tests, fixes, doc work |
| Planner | short, optional higher-reasoning context | Scope ambiguity, subtask allocation |
| Reviewer | *independent* strong model such as GPT-6 Astra High | End-state inspection, diff, acceptance, evidence, risks |
| Architect | expensive high-reasoning model | New architecture, violated invariant, ambiguous defect after 2 failed fixes |

A stronger reviewer does not automatically fix code. It emits a narrow correction contract for the Executor. Avoid passing entire repo/logs; provide task, fingerprint, changed files and gate failures. Inspect actual diff, not worker claims.

## Engineering invariants

- **One owner** per mutable state/behavior. Improve existing seams, don't create shadow state machines.
- **Executable proof** outranks persuasive summaries. Use builds, unit/integration tests, end-to-end traces and hardware observations scoped honestly.
- **Evidence provenance**: source commit, complete dirty state fingerprint, commands, observed outputs and reviewer verdict. Do not mark PASS because a previous session claimed success.
- **Deterministic code enforces policies**; prompts guide but cannot enforce. An optional Stop hook is only a convenience. CI/branch protection should enforce required gates and accepted reviews where configured.
- **Pre-tool guard**: for supported file-edit tools, apply task-specific `approved_paths` and `forbidden_paths` before the tool executes; fail closed when the active policy is missing or malformed, and protect agent instructions, CI workflows and evidence state. The optional Claude Code hook is documented in `docs/PRE_TOOL_GUARD.md`. This is defense-in-depth, not a sandbox: arbitrary shell writes and other agent tools can bypass file-tool checks, so pair it with isolated worktrees, client sandbox/permission controls, and required CI.
- **Bounded autonomy**: max retries, command timeouts, time/token/GPU cost caps; continue independent work after external blockers, never use infinite recursive Stop hooks.
- **No fabricated human/device results**: user testing, emulator, ADB, GPU and live-service checks require actual evidence. Classify unresolved as NOT_VERIFIED/BLOCKED, rather than advertising PASS.

## Imported patterns (not copied product code)

From [Android_Automotive_Voice_Agent](https://github.com/asapacsin/Android_Automotive_Voice_Agent): task contracts, role boundaries, read-only reviewer, review-before-integration, Stop/continue hook, TEST_MATRIX distinction of test layers. From `aurel-game`: `verification/gates.json`, `scripts/engineering.py` check/report/next, explicit dependency frontier, replay/native/neural evidence scope, GPU blocker discipline. The portable implementation consolidates these rather than depending on Android/Gradle/CMake.

## Evidence and limitations

A successful local unit-test result means only the harness unit tests ran. It does not mean the Aurel neural GPU workflow, Android speech/navigation E2E or any actual LLM provider review was run. Template gate commands must be executed in the respective repos; external Reviewer/Executor CLIs require authentication and working model selection. `PASS` is scoped to contract gates; if hardware is mandatory, add a real hardware gate before accepting.

## Context economy — specification compiler and demand-loaded evidence (2026-11-20)

The reusable lesson from [NovaDrive iOS](https://github.com/asapacsin/iOS_Automotive_Voice_Agent/blob/main/specs/token-budget.md) is **do not re-read the entire specification on every agent pass**. Compile the task into a scoped context packet: exact section identifiers, contract dependencies, acceptance rows, owned paths, gate commands, source fingerprint and budget. Retrieve only those sections, adding neighboring code or requirements when a concrete dependency demands it. Correctness and required safety context take precedence over minimizing tokens.

**Implemented shared tools:** `python3 scripts/spec_section.py <markdown-path> [section]` dynamically indexes and extracts one numbered or titled section; `scripts/read_guard.py` is an optional Claude Code PreToolUse Read budget (40 KiB by default, `AI_NATIVE_READ_GUARD_KB=0` disables). The Read budget is a **fail-open efficiency control**, independent of the **fail-closed file-edit scope guard**. The section helper does not physically shard or rewrite specification files. The operating guide and verification cases are in [CONTEXT_BUDGET.md](CONTEXT_BUDGET.md).

**Cost-aware routing:** prefer read-only lightweight search for file/symbol discovery, main-session implementation for routine coding/fixes, and a genuine independent reviewer only when acceptance evidence is ready. Always provide the complete diff inventory, relevant contracts, exact acceptance, changed callers/tests and deterministic gate evidence to the Reviewer; the existing source-bound scope manifest can log justified context expansion. A search subagent cannot replace the independent Reviewer. Do not imply the portable controller automatically selects a particular vendor/model or measures provider costs.

**Hot/cold memory:** keep active work and currently needed decisions in small canonical files; preserve historical completion evidence in a searchable archive. The agent should explicitly judge each terminal item **keep / summarize / archive**, with its reason and impact on open dependents. Archive adapters must retain dependency-resolving stubs, ensure uniqueness/recoverability and never discard human/device/acceptance proof. Avoid Stop-hook archival triggers that would unnecessarily restart completion loops; prefer a size-triggered prompt-submission reminder. **This is a portable policy, not yet a shared automatic archiver**; NovaDrive's implementation remains specific to its task/status schemas.

**Measured source example, not a shared benchmark:** the iOS pass on 2026-11-19 archived 120 completed tasks, moved 101 status rows and left hot STATUS.md at 62 KB and work.json at 91 KB. This shows smaller hot files, **not a validated percentage improvement** in billed tokens, task duration or accepted outcomes. Evaluate on equivalent tasks with actual token/cost logs, accepted PASS rate, regressions and missing-context findings. Never trade evidence quality for cosmetic token savings.

**Decision rule:** first use section-level extraction and diff-first review, then consider physical spec file splitting only if sections remain too large, have separate ownership or require independently versioned contracts. Fewer files are not the goal; lower repeated context cost with intact verification is.
