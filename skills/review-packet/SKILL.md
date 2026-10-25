---
name: review-packet
description: Prepare evidence for independent code review of a bounded agent change, checking actual source, scope, fresh tests and exact revision before merge.
---

# Build and inspect a review packet

Adapted from Nova Drive /review-packet; use project-specific review tools where they exist.

1. Identify approved task contract, base/tip commits, current git diff, tracked/untracked status and modified-file scope.
2. Gather evidence from actual gate artifacts at the reviewed revision, not the Executor's completion summary.
3. Compare acceptance requirements with observed proof levels. Flag stale tests, out-of-scope changes, source-of-truth drift, secrets and unsafe dependencies.
4. Have a separate read-only reviewer inspect the code and artifacts; the implementation agent cannot attest to its own correctness.
5. Record PASS, REWORK, BLOCKED or NOT_VERIFIED with specific findings and next action. Required failing or absent evidence is never bypassed by a model verdict.
6. Only a separate governance/CI decision may authorize merge. Re-check exact source fingerprint and required hosted checks before claiming release.

Do not run concurrent verification against the same mutable worktree. Reject evidence produced for another task or source revision.
