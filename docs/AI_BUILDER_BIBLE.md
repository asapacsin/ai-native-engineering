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

## Multi-agent approach: safe parallelism, not more agents

**Optimize for independently verified *integrated* deliverables per dollar/hour, not concurrent agent count.** Keep the economical Executor → deterministic end-state gates → genuinely independent read-only Reviewer → bounded targeted repair loop **per task**. Use a lightweight coordinator for DAG scheduling, process launch, fingerprints and compact evidence—not a large model rereading every worker's full transcript or the entire project on each step.

- **One task / tightly coupled edits:** one Executor, sequential. Do not force multi-agent execution.
- **Independent research or test/log exploration:** parallel **read-only subagents**, returning short evidence summaries.
- **Independent approved implementation tasks:** **two concurrent worktree-isolated Claude/Codex/API workers by default**, moving to three only if accepted throughput and review capacity justify it. The host must launch workers before waiting for the first to finish. One shared worktree, shared external resource or overlapping file ownership means serialize.
- **Complex peer coordination:** optionally use interactive **Claude Code Agent Teams**; they are experimental, cost more tokens and must be explicitly enabled in the client. They do not spawn teammates from non-interactive `claude -p`/Agent SDK runs. A repo instruction or agent-team setting is not a general parallel scheduler.
- **Scheduler gate:** create independently approved contracts with owner, acceptance, source/base SHA, allowed paths, exact gates, dependencies, resources and aggregate/per-task budgets. Dispatch only the ready, **nonconflicting** dependency frontier; a missing GPU/device blocks only dependent tasks.
- **Verification/integration gate:** evidence belongs to an exact worktree revision and independent requirement scope. Reviewer verdicts remain `PASS | REWORK | BLOCKED | NOT_VERIFIED`. Integrate approved branches **serially**, then rerun integration-level gates/review on the combined revision. Two individually passing workers are not proof of an integrated PASS.
- **Backpressure and audit:** cap worker count and retry/time/token spend. Track overlapping run intervals, peak actual concurrency, coordinator/reviewer costs, accepted integrated tasks/hour, cost/accepted task and regressions. Never declare project COMPLETE while required evidence or human/device actions are pending.

**Implementation truth (2026-10-27):** the repo's `frontier.py` supplies dependency decisions and `supervisor.py` is currently **single-process and sequential**. Parallel launch, conflict-aware scheduling, concurrency-safe registry writes, separate worktrees and integrated re-review still require a host implementation and tests. `/goal` and Stop hooks are not substitutes. Do not claim parallel execution until worker intervals really overlap.

See the [multi-agent orchestration runbook](MULTI_AGENT_ORCHESTRATION.md) for the scheduler contract, launch steps for `claude --worktree`, optional Agent Teams settings, evidence/integration gates, and diagnostics; follow provider-specific restrictions there.

## Method validity gate — understand the approach before scaling implementation

AI can **hallucinate facts** (APIs, dependencies, capabilities, results) and can also choose a **plausible but wrong method** (algorithm, architecture, library, workflow, or optimization target). Passing unit tests or receiving a confident review does **not** establish that the chosen method solves the real problem well.

For non-trivial, unfamiliar, costly, high-risk, or architecture-changing work, apply a lightweight **method-selection checkpoint before bulk implementation**:

1. **Define the real outcome and constraints.** State the user-visible success condition, acceptance scope, quality, time/cost/latency budget, and non-negotiable limitations. Challenge an assumed implementation strategy when a simpler method can achieve the outcome.
2. **Inspect and verify.** Read the actual codebase and authoritative API/upstream documentation; independently check important technical claims rather than trusting model-generated explanations. Identify relevant established solutions before inventing a new one.
3. **Compare methods.** Consider 1–3 realistic approaches (including reuse of an existing tool or smaller workflow), their trade-offs and failure modes. Record a brief design basis: chosen method, why, assumptions, rejected alternatives, and what would falsify the choice.
4. **Understand enough to evaluate.** The accountable human and/or qualified domain reviewer should be able to explain the method's key mechanism, assumptions, limitations, and why it fits the problem. When domain expertise is missing, obtain authoritative references, a subject-matter review, or a bounded experiment; do not equate AI confidence with understanding.
5. **Test the risky assumption early.** Use a small representative prototype, benchmark, sample, or vertical slice *before* scaling to many files/assets or committing to an architecture. Include negative and edge cases and measure outcome-level properties, not just compilation or interface conformance.
6. **Review the method as well as the output.** Independent review must question whether the approach is appropriate, necessary, efficient, and supported by evidence—not only whether code matches the proposed plan. If repeated revisions do not improve the real outcome, stop the loop and revisit the method rather than extending retries.

**Proportionality:** Routine, well-understood local fixes do not need a formal comparison or an expensive Architect call; a short rationale is enough. Escalate before irreversible, expensive or poorly understood commitments. Record **NOT_VERIFIED** where method validity remains untested. This checkpoint complements, and never replaces, the end-state deterministic gates.

## Engineering invariants

- **One owner** per mutable state/behavior. Improve existing seams, don't create shadow state machines.
- **Executable proof** outranks persuasive summaries. Use builds, unit/integration tests, end-to-end traces and hardware observations scoped honestly.
- **Evidence provenance**: source commit, complete dirty state fingerprint, commands, observed outputs and reviewer verdict. Do not mark PASS because a previous session claimed success.
- **Deterministic code enforces policies**; prompts guide but cannot enforce. An optional Stop hook is only a convenience. CI/branch protection should enforce required gates and accepted reviews where configured.
- **Pre-tool guard**: for supported file-edit tools, apply task-specific `approved_paths` and `forbidden_paths` before the tool executes; fail closed when the active policy is missing or malformed, and protect agent instructions, CI workflows and evidence state. The optional Claude Code hook is documented in `docs/PRE_TOOL_GUARD.md`. This is defense-in-depth, not a sandbox: arbitrary shell writes and other agent tools can bypass file-tool checks, so pair it with isolated worktrees, client sandbox/permission controls, and required CI.
- **Bounded autonomy**: max retries, command timeouts, time/token/GPU cost caps; continue independent work after external blockers, never use infinite recursive Stop hooks.
- **No fabricated human/device results**: user testing, emulator, ADB, GPU and live-service checks require actual evidence. Classify unresolved as NOT_VERIFIED/BLOCKED, rather than advertising PASS.

## Mandatory remote-delivery gate for code-changing tasks

A locally finished run is not a remotely delivered implementation. The Executor or host must:

1. Confirm the correct target repository, authorized remote (`git remote -v`), branch (`git branch --show-current`) and scoped changes (`git status --short`, `git diff --check`); do not sweep unrelated user changes into a commit.
2. Commit only approved task files with a meaningful message. Run required deterministic gates and independent review against that **exact committed tip**; if anything changes, obtain fresh evidence and review.
3. Push the reviewed commit to its authorized remote branch (`git push -u origin HEAD:<branch>`). Do not force-push, bypass protections or merge without approval.
4. Verify delivery, not just a successful push command: compare `git rev-parse HEAD` with the SHA returned by `git ls-remote --heads origin <branch>`. Record repository, branch, SHA and outstanding unrelated working-tree changes in the end-state handoff.
5. Close only after the remote SHA matches and acceptance evidence is current. If credentials, network access, permissions, CI/branch policy or review prevent delivery, report **BLOCKED** or **NOT_VERIFIED**, the precise blocker and any locally available commit SHA; do not claim a successfully delivered task. For read-only/no-change tasks, report that no commit was needed; explicit local-only instructions override pushing.

This is an agent operating rule, **not a guarantee implemented by the current controller, Stop hook or CI**. A host-level post-run check or required CI is needed to make it mechanically enforceable. Passing independent review is not permission to merge a protected branch.

## Imported patterns (not copied product code)

From [Android_Automotive_Voice_Agent](https://github.com/asapacsin/Android_Automotive_Voice_Agent): task contracts, role boundaries, read-only reviewer, review-before-integration, Stop/continue hook, TEST_MATRIX distinction of test layers. From `aurel-game`: `verification/gates.json`, `scripts/engineering.py` check/report/next, explicit dependency frontier, replay/native/neural evidence scope, GPU blocker discipline. The portable implementation consolidates these rather than depending on Android/Gradle/CMake.

## Evidence and limitations

A successful local unit-test result means only the harness unit tests ran. It does not mean the Aurel neural GPU workflow, Android speech/navigation E2E or any actual LLM provider review was run. Template gate commands must be executed in the respective repos; external Reviewer/Executor CLIs require authentication and working model selection. `PASS` is scoped to contract gates; if hardware is mandatory, add a real hardware gate before accepting.

## Human-facing skills (2026-10-25 update)

The Bible is now exposed through a small shared skill pack rather than pasting this document into every agent turn. See [docs/SKILLS.md](SKILLS.md) and canonical procedures under `skills/`. In Claude Code, `/goal <outcome>` is the interactive entry point; in Codex, use `$goal <outcome>`. `/goal` is a **decision procedure**, while the trusted host supervisor, independent requirements, gate evidence and GitHub rules are the **enforcement** mechanisms. A skill or a Stop hook by itself cannot prevent an arbitrary Codex Cloud task from ending. Final scope certification still requires a real independent reviewer, current evidence and any mandatory release/remote checks.

A complete outcome means acceptance scoped by separately owned requirements; all required evidence has been produced on the current source; independent review has passed; remaining authorized tasks have been reconciled; and target-appropriate delivery/terminal gates are satisfied. If one of these is missing, report the specific incomplete state instead of `COMPLETE`. New skill manifests have only static contract tests and unexecuted example evals until genuine fresh-session trials are run.
