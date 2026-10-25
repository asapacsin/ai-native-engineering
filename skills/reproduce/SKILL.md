---
name: reproduce
description: Reproduce and classify a reported defect using the target project's real tests, logs and environment before proposing a fix. Use for bugs, regressions and failing scenarios.
---

# Reproduce a defect

Adapted from the Nova Drive /reproduce procedure; the target repository owns its requirements and tooling.

1. State observed behavior, expected behavior, input, environment and affected version. Verify that the expected behavior is actually supported by the project's contract.
2. Inspect the smallest relevant source, issue or scenario, architecture owner, and existing regression tests. Do not load unrelated large files.
3. Select the cheapest faithful reproduction: focused deterministic test first; then integration, emulator/device, network or GPU if the symptom depends on them.
4. Execute a reproduction and save command, source revision, environment, actual logs and artifacts. Distinguish newly generated output from stale caches.
5. Classify as REPRODUCED, NOT_REPRODUCED, BEHAVIOR_CHANGED, TEST_OUTDATED or BLOCKED with precise supporting evidence.
6. Hand off the smallest reproducible case and a suggested regression test. Do not change production behavior as part of a reproduction-only task.

If reproduction cannot be performed, name the missing capability and evidence level; never invent a failure or claim a live-system result from a unit test.
