# /review-packet — independent end-state check

1. Collect the approved contract and hash, exact source fingerprint, git diff, changed paths, required gates, run logs and missing proof levels. Do not send unrelated source, private secrets or full logs.
2. Execute the configured independent read-only Reviewer through scripts/ai_native.py cycle (or host supervisor). Never call an executor's own answer an independent review. Review the actual source diff, not only a summary.
3. Compare reviewed_fingerprint and reviewed_contract_hash to the current packet; failed or missing gates cannot be overridden by reviewer prose. Decision must be PASS, REWORK, BLOCKED or NOT_VERIFIED.
4. Route REWORK back to /fix with bounded concrete findings. Route BLOCKED to the human/external queue and allow independent tasks to proceed. Never merge an unverified or stale revision.
5. Before integration, use scripts/governance.py scope and eligible with a separately owned requirements manifest; require configured CI/branch rules and exact-tip checks in the target repo. Local reviewer PASS is not permission to bypass repository policy.
