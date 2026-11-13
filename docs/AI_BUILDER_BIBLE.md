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

## Exclusive verdict authority: Reviewer only

**The Proposer is never the judge of its own proposal.** This is a mandatory separation of duties across proposals, implementation, tests, research claims, and release decisions:

1. **Proposer / Planner** defines a candidate plan, requirements, acceptance criteria, assumptions and evidence to gather. It may say *ready for review* or *proposed complete*, **not** `PASS`, `FAIL` or any final acceptance verdict. A proposal's confidence score is not a review.
2. **Executor** implements the approved scope, runs checks and reports commands, observations and unresolved issues. It cannot mark its own task `PASS` or `FAIL`, and must not write, forge or reuse reviewer results. A green build is evidence, not an approval.
3. **Independent Reviewer** alone issues the task-review verdict: `PASS`, `REWORK` (failed acceptance / fixable defects), `BLOCKED` (external dependency), or `NOT_VERIFIED` (missing or inconclusive evidence). If someone says `FAIL` for a task, map it to an actionable reviewer `REWORK`, `BLOCKED`, or `NOT_VERIFIED`; the portable protocol does not have a generic `FAIL` reviewer verdict.
4. **Trusted deterministic controller / CI** runs objective checks and can *veto* a Reviewer `PASS` when requirements, required gates, scope, freshness, or authorization fail. It does not substitute its own acceptance judgment for a Reviewer verdict. Missing, failed, forged, or stale Reviewer output means `NOT_VERIFIED` (or an explicitly named blocking control state), **never PASS**.
5. **Human/owner** approves goals, risk tolerance, exception handling and integration policy. Contract approval by a Planner/Architect/Owner is **not** a task-quality verdict; merge/release additionally requires required CI and independently authorized review.

A task contract, Proposer summary, Executor message, green test result or local status field must never be treated as a Reviewer-issued acceptance decision. Verdict evidence must be bound to the exact source fingerprint and contract hash and produced by a fresh external Reviewer process. The runner collects Reviewer output outside the Proposer/Executor worktree and only persists a validated copy. For true role isolation, enforce different identities/worktrees, read-only Reviewer access, protected CI/evidence and branch rules: self-reported role strings and SHA-256 consistency alone are **not authentication**.

## Model policy

| Role | Default strategy | When invoked |
| --- | --- | --- |
| Proposer / Planner | short, optional higher-reasoning context | Propose scope, requirements and acceptance tests; never issue a verdict |
| Executor | capable economical model such as GPT-6 Luna Medium | Most coding, tests, fixes, doc work |
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
