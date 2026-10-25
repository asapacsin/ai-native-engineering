---
name: verify
description: Verify a scoped implementation from freshly produced test and artifact evidence, distinguishing unit, integration and real runtime proof. Use before completion claims.
---

# Verify a change

Adapted from Nova Drive /verify. Verification instructions never replace the controller's required gates or the independent Reviewer.

1. Identify the task contract, exact commit plus dirty/untracked fingerprint, relevant changed files and required acceptance levels.
2. Run the specified deterministic gates with the proper target-project commands; keep command, exit code, run ID, logs and artifacts.
3. Check freshness: cached, stale or wrong-variant results do not prove the current source. Inspect original test reports rather than relying only on a green summary.
4. For device, integration, GPU, latency, audiovisual or external-service claims, require appropriate real-environment evidence; mark missing capabilities BLOCKED or NOT_VERIFIED.
5. Tie each claim to source revision, requirement and artifact. Identify failures separately; do not silently downgrade the promised evidence level.
6. Produce an evidence packet for an independent read-only Reviewer. Do not edit acceptance requirements, waive required gates or authorize your own merge.

Report exactly what was tested, what passed, what failed and what remains unverified. Only the external controller/reviewer can issue its final task verdict.
