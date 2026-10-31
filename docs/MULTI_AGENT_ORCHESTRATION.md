# Multi-agent orchestration — parallel execution and review

Operational companion to [AI Builder Bible](AI_BUILDER_BIBLE.md).

**Goal:** increase **verified, integrated deliverables per dollar and elapsed hour**. Parallelism is a scheduling choice, *not* the default definition of "multi-agent." Preserve the executor-first, deterministic-gates, independent-reviewer architecture **for every task**. A lightweight host coordinator should handle dispatch and evidence bookkeeping, not repeatedly ingest the complete repository, task matrix or every worker transcript. Never assume that a prompt, `/goal` skill, repo file, or Claude setting actually launches concurrent processes.

### Choose the smallest useful topology

| Work shape | Preferred execution | Why |
| --- | --- | --- |
| One small change; one shared file; tightly coupled steps | **One economical Executor**, sequential steps | No fan-out or merge overhead |
| Independent codebase research, tests/log triage, design critiques | **Parallel read-only subagents**, return compact findings | Isolation and short coordinator context |
| Two or more approved implementation tasks with disjoint writes | **Parallel isolated worktree sessions/CLI workers**, bounded concurrency | Real simultaneous progress without file collisions |
| Interdependent investigators needing peer-to-peer discussion, shared task ownership or competing hypotheses | **Claude Code Agent Teams** *when explicitly enabled and supported* | Team communication; extra coordination and token cost |
| Shared-state refactor, architecture decision, dependent phase, integration, or merging | **Serialize at the dependency/integration boundary** | Preserve invariants and reproducible evidence |

Do not turn on Agent Teams globally as a substitute for making tasks independent. Ordinary Claude subagents can already run independent research concurrently. A second Claude Code session in a separate Git worktree is often simpler for parallel code changes. Agent Teams are experimental, use more tokens than subagents and require an interactive Claude Code session; they **do not spawn teammates in non-interactive `claude -p`/Agent SDK runs**, even if the feature flag is enabled. For product behavior see the [official Agent Teams guide](https://code.claude.com/docs/en/agent-teams), [subagent guide](https://code.claude.com/docs/en/sub-agents) and [worktree workflow](https://code.claude.com/docs/en/common-workflows#run-parallel-sessions-with-worktrees).

### Dispatch contract: *parallel where independent, serial where dependent*

1. **Approve before dispatch.** For each task, store `task_id`, exact `base_commit`, `goal`, acceptance/required evidence, `depends_on`, `approved_paths`, `forbidden_paths`, required capabilities, exclusive resources, gate commands and retry/time/cost caps in trusted, non-Executor-owned contracts/registry. Use a dependency DAG; reject cycles, unknown dependencies, scope overlap and missing resource assumptions. Do not infer authorization from a brainstormed backlog.
2. **Compute the ready frontier.** A task is runnable only if its dependencies have acceptable, current proof and its resources are available. Choose a set with **no overlapping write paths or exclusive resources** (e.g., same device, GPU, test database, port, workspace, branch or migration). Read-only investigations may share sources. Do not spawn concurrent writers in the same worktree or against the same mutable remote system.
3. **Launch the whole safe batch before awaiting completion.** Default to **two** independent implementation workers; raise to three only after measuring stable throughput and review capacity. Do not launch another worker merely to fill slots. Give each a separate worktree/branch, bounded task contract and cheap capable Executor. The host must actually launch simultaneous processes/sessions; a numbered list of delegation prompts executed one by one is **not** parallelism.
4. **Verify each isolated result.** Collect wall-clock start/end, actual model/worker, source fingerprint, gate outputs, touched paths and cost. Run declared deterministic gates and invoke an **independent read-only Reviewer** on that task's *actual* revision and separately owned requirements. The Reviewer emits `PASS`, `REWORK`, `BLOCKED` or `NOT_VERIFIED`; never take a worker's self-report as proof. Limit targeted retries to the approved budget.
5. **Integrate conservatively.** Reconcile completed branches **one at a time** with approved scope, exact-tip and required CI checks. If integration changes a reviewed fingerprint or introduces interactions, rerun affected checks and review on the integrated revision. A PASS on two isolated branches **does not prove** their combination passes. Downstream dependent work begins only after its required upstream evidence is valid.
6. **Recompute/stop honestly.** After *every* completion or blocker, refresh the ready frontier and dispatch any remaining independent authorized tasks within budget. Leave missing GPU/device/human/credential work explicitly blocked, without halting unrelated jobs. No stop hook or lead agent may declare project COMPLETE while required work remains unverified. Checkpoint and hand off cleanly on budget exhaustion.

Example: contracts `API` and `UI` can run together in two worktrees if their writes/resources do not conflict; `E2E` declares `depends_on: ["API", "UI"]` and waits for both **integrated** results. The scheduler may continue independent `DOCS` while `E2E` is blocked on a device. Source owners, required E2E scope and shared test environments—not just file paths—determine safety.

### How to enable genuine parallel work in Claude Code

**Simple implementation default (no experimental team feature):** Open two separate terminal sessions in a Git repo that already has a commit, with the *same approved base* and distinct task/branch names:

~~~sh
# Terminal A: approved API contract, separate worktree
claude --worktree feature-api
# Terminal B: approved UI contract, separate worktree
claude --worktree feature-ui
~~~

In each session supply **only its own** scoped contract, and supervise both. `--worktree` isolates checkout/branch state; it does **not** isolate ports, hardware, databases, network credentials or other external resources. For repeated read-only investigation, instead explicitly request: "Start two independent subagents now to investigate X and Y in parallel. Do not await X before starting Y. Return only findings and evidence." Verify in the session/activity trace that their running intervals overlap.

**When teammate coordination is necessary:** Enable experimental Agent Teams in the *actual Claude Code client's* user `~/.claude/settings.json` or an appropriately scoped local project settings file:

~~~json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
~~~

Then, in an **interactive** Claude Code session, ask: "Create an agent team with two independent workers; assign separate file ownership and task contracts, start them concurrently, keep the lead focused on coordination, and hold integration until all required independent reviews pass." The in-process team panel works inside a terminal; split-pane display requires tmux or iTerm2 and is not supported in VS Code's integrated terminal or Windows Terminal. VS Code's Claude interface supports some subagent capabilities but a UI panel alone does **not** prove that an Agent Team was created. Check teammate sessions, running timestamps and actual task progress. If teams are unnecessary, disable the flag again: enabling it can cause otherwise named subagents to become teammates.

**Cross-model/CI automation:** The host runner (Claude/Codex CLI, CI, or a trusted service) must implement the process fan-out and worktree lifecycle itself. **This repository currently has a dependency-aware frontier and a sequential, single-process `scripts/supervisor.py`; it does not yet implement parallel dispatch, concurrency-safe registry writes, per-worker worktree management or automatic integrated re-review.** `scripts/frontier.py next`, a supervisor invocation, `.claude` instructions or a Stop hook must **not** be described as a working parallel scheduler. Add tests and a host-level runner before claiming autonomous multi-agent implementation.

### Cost, observation and failure policy

- **Minimize main-agent replay:** coordinator carries compact task IDs, decision/evidence hashes, ready/blocked states and links to stored artifacts; workers read only their bounded files. Do not paste large `TEST_MATRIX`, full diff/log histories or all worker transcripts into every coordination turn. The reviewer receives the relevant task, independent acceptance scope, diff, fingerprints, failing outputs and trace references only.
- **Cost guard:** a worker consumes real tokens even if its results are discarded. Meter per-worker tokens/dollars, coordinator tokens, review cost, retries and integration cost. Cap both per-worker and aggregate spend; start with two workers, not automatic maximum parallelism. Escalate to Architect only on invariant conflict, important uncertainty or repeated failed bounded repairs.
- **Proof of concurrency:** record `worker_id`, `worktree`, `task_id`, `started_at`, `finished_at` and final state. Report *peak simultaneous running workers*, overlap time, accepted-integrated tasks/hour, total cost/accepted task, rework and integration regressions. If peak concurrency is 1, fix **dispatch**, permissions, capability limits or dependencies instead of merely strengthening the prompt.
- **Backpressure:** suspend new launches when Reviewer/CI/integration queues are saturated; serialize when tasks conflict; cancel or defer speculative tasks that do not improve expected accepted output. Protect model rate limits, context use and budget. Keep independent Reviewer authority and protected CI/merge gates outside Executor write permissions.
- **Stop states:** individual task PASS is not project COMPLETE; queued, running, blocked and human-required items remain visible. A teammate ending, lead saying "done", `/goal` returning, or Stop/SubagentStop firing is not sufficient proof of terminal acceptance.

---

