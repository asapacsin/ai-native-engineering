---
name: fix
description: Fix an observed software defect through a bounded change to the existing behavior owner, preserving invariants and adding a regression test. Use after defect reproduction.
---

# Fix a reproduced defect

Adapted from Nova Drive /fix; target-project source-of-truth and acceptance rules take precedence.

1. Start with the reproduction artifact or state why reproduction is blocked.
2. Identify the existing implementation owner and relevant architectural invariants. Read only the necessary files and interface boundaries.
3. Propose the smallest change satisfying the task contract. Prefer editing the owner to creating a parallel mechanism; remove obsolete replacement paths.
4. Add or update a focused regression test that fails against the original behavior and passes with the fix when feasible.
5. Run targeted tests while iterating, then execute the contract's required deterministic gates. Save fresh results and exact source revision.
6. Report changed files, reproduction link, passing and failing checks, unverified behaviors and next action. Do not self-certify review, device E2E or merge eligibility.

Escalate invariant conflicts, ownership ambiguity or repeated failures instead of broadening scope. A green unit test is not device, network or visual proof.
