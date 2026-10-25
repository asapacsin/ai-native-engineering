# /fix — one owner, minimal correction

1. Read the contract, reproduction and architecture owner. Inspect git diff/status and approved_paths before editing. Respect forbidden_paths and protected governance files.
2. Change the single existing owner; avoid parallel implementations, broad rewrites, new state ledgers, arbitrary test weakening or generated-workaround code.
3. Run the failing test until it passes and run neighboring regression checks. If a test doesn't cover acceptance, add honest proof rather than upgrading its label.
4. Compare the diff to contract boundaries. Document residual risk and exact changed files; follow /verify and /review-packet.
5. After two failed targeted fixes, architecture uncertainty or invariant conflict, stop bounded retries and escalate with the observed evidence. Never silently rerun without a budget.
