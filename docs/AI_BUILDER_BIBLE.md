# AI Builder Bible — shared reusable operating system

## Objective

Increase *validated useful outcomes per dollar and hour*, not tokens consumed or agents spawned. Human defines outcomes, architecture boundaries and risk appetite; software runs deterministic verification; independent AI reviewer is called only at the end-state and for substantive decisions.

## Evidence-driven spec development (EDSD)

Use this discovery cycle before approving the production specification when a design depends on uncertain technical feasibility, unfamiliar APIs, model behavior, integration constraints or performance. EDSD is a descriptive name for our workflow, not a claim of a new industry standard. It combines LLM-assisted exploration, technical spikes (small proofs of concept), evidence-based specification and the existing independent verification loop.

```text
Human objective + constraints
          |
Human / LLM discussion: candidates, assumptions, unknowns
          |
Review official docs, relevant implementations and community experience
          |
Define hypothesis + measurable success criteria + experiment budget
          |
Executor: isolated minimal PoC / reproducible experiment
          |
Measure actual results and inspect limitations
          |
          +-- unsupported / inconclusive --> revise hypothesis or record blocker
          |                                  and repeat within budget
          |
          +-- supported --> record evidence + decision + residual risks
                                  |
                       Human-approved spec / acceptance contract
                                  |
                       Existing default control loop
                       (Executor -> deterministic gates -> independent Reviewer)
                                  |
                       Accept or revise; preserve new knowledge
```

### Discovery and promotion rules

1. **Reason before building.** The human sets the outcome and constraints. Discuss candidate approaches with an LLM; distinguish facts, assumptions and unknowns. Check authoritative documentation and source code first; use community experience for candidate discovery and known failure modes, not as proof that the local implementation works.
2. **Test the highest-risk assumption first.** Define a falsifiable hypothesis, baseline where useful, input/environment, measurable success threshold and time/token/GPU budget before running the experiment. Build the smallest representative PoC that can answer the question; do not integrate an unvalidated architecture into the production codebase.
3. **Measure rather than trust.** Execute the PoC and preserve commands, versions, inputs, observed outputs, repeatability, limitations and negative results. A plausible LLM explanation, community recommendation or unexecuted test is not empirical evidence. Classify the hypothesis as supported, rejected or inconclusive under the tested conditions; these are experiment findings, not production PASS/FAIL verdicts.
4. **Promote knowledge, not necessarily code.** Add supported technical decisions to the relevant spec section with links to evidence, applicable conditions, measurable acceptance criteria and remaining integration risks. Keep unvalidated claims explicitly provisional. Human approval is required before the production specification becomes an execution contract; use independent review for substantive or high-risk decisions according to the existing model policy.
5. **Implement and independently verify.** The Executor implements against the approved spec; deterministic gates and the read-only independent Reviewer verify the actual production revision. A successful PoC proves only the scoped hypothesis, not production reliability, security, scalability or end-to-end correctness. Preserve the existing PASS/REWORK/BLOCKED/NOT_VERIFIED semantics and bounded retries.
6. **Close the learning loop.** If production evidence contradicts the spec, record the discrepancy, revisit the hypothesis and obtain approval for a revised contract rather than silently weakening acceptance criteria.

### Minimal experiment record

Keep the record beside the affected specification, or link to an existing evidence location. Use the lightest structure that preserves reproducibility.

- Question / hypothesis and why it matters
- Candidate solution, baseline and external references
- Predeclared success criteria, environment and budget
- PoC path or revision, exact commands and observed results
- Supported / rejected / inconclusive, limitations and next decision
- Spec section affected and production acceptance tests required

For example, `specs/<feature>/experiments/<spike-id>/` may contain the experiment record, minimal PoC and results, with links from `spec.md`. Avoid duplicating large logs or loading unrelated spec sections.

### When to use the cycle

For routine, well-understood changes with no material feasibility uncertainty, go directly to the normal human-approved spec and execution loop. For uncertain AI/model behavior, latency, new dependencies or architectural choices, run a focused spike first. Start sequentially with the existing Planner/Executor/Reviewer roles; this method introduces neither a mandatory extra agent nor parallel execution. Escalate or stop when the experiment budget is exhausted; record the unresolved question rather than manufacturing certainty.

The objective is faster judgment-to-evidence feedback and fewer costly production reworks, measured in validated outcomes per dollar and hour, not the number of experiments or pages of specifications.

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
