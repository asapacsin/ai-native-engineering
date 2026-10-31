---
name: verify
description: Verify claimed outcomes against fresh evidence from the exact source revision. Use for suspect cached tests, ambiguous PASS claims, variant mixing, or device/GPU/E2E claims unsupported by actual runs.
---

# Evidence-fresh verification

**Origin:** Nova Drive `skills/verify.md`, `ACCEPTANCE_TESTS.md` failure cases; generalized without embedding a project's live capability state.

1. Read the **approved** contract and current repository `AGENTS.md`. Identify the current branch, commit, diff and modified/untracked files. Resolve the relevant owner, requirement IDs and minimum evidence level.
2. Choose the correct **freshness anchor**: a test run ID, source fingerprint, named variant and artifact timestamp. Never treat stale XML in a previous build directory as the outcome of the current run.
3. Run the contract's mandatory verification gates. Prefer captured machine-readable artifacts (JUnit XML, JSON test reports, recorded commands, logs) over a tool's prose summary. A Gradle `BUILD SUCCESSFUL` message alone can reflect up-to-date cached tasks; verify actual test execution and source binding.
4. Never add counts from different build variants to produce a single result. Name the exact variant and scope. Never run two verifications concurrently against one mutable worktree; tests can race and manufacture false failures.
5. **Preserve claim boundaries:** unit/CLI/reference tests do not prove device, audio/navigation, external network, native/neural renderer, GPU memory, frame rate or visual acceptance. Demand real-run artifact evidence when the acceptance contract needs it.
6. Collect a compact packet: task ID, source fingerprint, required checks with exit codes, artifacts, relevant test counts, proof levels, missing dependencies, and unverified behavior.
7. Request independent read-only review under the existing controller. Never change acceptance requirements, bypass gates, self-approve a merge, or declare a terminal task PASS from your narrative.

**Known failure classes from the source project:** Gradle may report success without fresh JUnit XML; old build directories may retain results; simultaneously building the same worktree caused transient `NoClassDefFoundError` failures; mixing debug and release counts inflated reports. Adapt the principle to the target toolchain rather than copying Android commands.

**Stop conditions:** If a required test runner, device, credential, model weight, or hardware is unavailable, return precise `BLOCKED` or `NOT_VERIFIED` scope. Do not lower the stated required evidence level.
