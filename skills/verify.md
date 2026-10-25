# /verify — evidence beats narrative

1. Read the task contract, separately owned requirements and the actual source/commit fingerprint. Required tests and proof levels come from the requirements, not the executor's description.
2. Run exact specified commands and save outputs with exit status, execution environment, timestamp and reviewed source state. For a configured task run:
    python3 scripts/ai_native.py cycle --repo <target> --contract <contract>
   This invokes the configured external agents if present. To verify current state only, do not set an executor command; independent Reviewer remains required for PASS.
3. Record each level separately: unit, integration, end-to-end, device, live service, GPU or human. A build, mocked run or source inspection must not substitute for a higher required level.
4. Inspect .ai-native/runs/<task-id>/latest.json and validate fingerprint/contract hash. Gate failure, absent independent review, changed source or missing required level => NOT_VERIFIED, REWORK or BLOCKED; never self-declare PASS.
5. For merge eligibility with separately owned requirements run:
    python3 scripts/governance.py eligible --repo <target> --contract <contract> --requirements <requirements.json>
   This is a local check, not proof of GitHub branch protection or remote delivery. See docs/ENFORCEMENT.md and docs/INTEGRATION.md.
