---
name: token-efficient-task
description: Perform a bounded engineering task using selective context retrieval, explicit contracts, compact evidence and efficient handoffs. Use when repository context is large.
---

# Token-efficient task execution

Adapted from Nova Drive token-efficient-task. This skill minimizes irrelevant context, not required checks.

1. Read branch and status, approved task contract, and the smallest relevant architecture/owner references. Search first; expand context only for needed sections.
2. Avoid bulk-loading huge test matrices, issue files and unrelated source. Point the executor at exact paths, symbols, test IDs and existing invariants.
3. Keep one Executor by default; parallelize only genuinely independent work with nonoverlapping ownership. Respect budgets and contract boundaries.
4. During implementation run focused tests, saving full logs externally and returning concise failure excerpts. Final acceptance still runs every required gate.
5. At a handoff, store exact revision, changed files, proof level, unresolved blockers and the next bounded action in the project's durable state.
6. Compare token/cost/runtime and verified success against a no-skill baseline on similar tasks. Drop the skill if it adds overhead without improving outcomes.

Never trade away coverage, reviewer independence or necessary device/GPU proof for reduced token usage.
