---
name: token-efficient-task
description: Execute large-repository tasks using narrow retrieval, short executor packets and compact fresh test evidence. Use when large specs, test matrices or repetitive logs are dominating agent context or cost.
---

# Evidence-preserving context efficiency

**Origin:** Nova Drive `.claude/skills/token-efficient-task/SKILL.md`, produced after large test matrices and issue documents inflated contexts.

1. Inspect git status, the approved task contract and the target repository's file index. Find the relevant owner/capability/acceptance IDs before reading broad documents.
2. Retrieve only the needed heading, search hits and bounded neighboring lines. Never preload huge test matrices, all issue histories, or entire test logs to answer a single task. If an indexed helper exists, use it instead of dumping a large file.
3. Send the Executor a compact packet: source revision, goal, owning paths, exact input pointers, invariants, allowed paths, verification commands, missing capabilities, and retry/stop budget. **References are navigation aids**, not a substitute for reading source at the integration boundary.
4. Start with one Executor. Parallelize only genuinely independent tasks with non-overlapping file and worktree ownership; avoid planners/reviewers that merely repeat the same context.
5. During implementation, run narrow tests; capture complete logs outside prompt context and surface failing test IDs and bounded excerpts. Do not let compressed output hide a nonzero exit code or weaken final verification.
6. At the final state run every **required** contract gate and independent review, even if costly. A limited test is not the release gate.
7. Write a durable, short handoff with exact source revision, changed files, proof level, unresolved blockers and next action. Do not use long conversation history as the state database.
8. Compare elapsed time/tokens/cost and controller-verified outcomes on matched tasks **with and without** this skill. Retire it when it consistently adds overhead without improving reliable output.

**Known source failure:** whole-file loading of thousands of test-matrix rows and issue items caused massive repeated context rereads. The cure is bounded retrieval and durable pointers, never fewer required tests.
