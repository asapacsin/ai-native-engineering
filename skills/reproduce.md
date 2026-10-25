# /reproduce — proof before patch

1. Identify expected observable behavior, actual behavior, affected code owner and precise failing case. Read project-specific requirements and test layer labels.
2. Run the smallest existing deterministic reproduction first. Record exact command, environment and exit status; where appropriate add a failing regression test before changing implementation.
3. Differentiate a true failure from missing credentials, unavailable GPU/device, flaky network and unsupported test environment. Do not manufacture successful device, GPU or visual evidence.
4. Save the reproduction evidence and source revision in the task's run/checkpoint files; never treat a stale baseline as current proof.
5. Hand the smallest reproducible defect and its constraints to /fix. If the failure cannot be reproduced, record NOT_VERIFIED or BLOCKED with the needed next test instead of guessing.
