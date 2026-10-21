# Enforcement guide (portable core, milestone P0/P1)

This repository is PUBLIC. Do not commit private manuscript text, game source, customer data, API keys, local absolute paths with secrets, or private Android/Aurel/Edria artifacts here. Use the core as reusable software; put private project manifests in the projects themselves.

The current implementation provides **local procedural enforcement**, not a hosted autonomous service or preinstalled branch protection. GitHub connector publication does not launch Codex or grant the executor independent reviewer permissions.

## Safe task workflow (explicit commands)

1. Make an isolated branch/worktree in the target repo by ordinary Git tooling, after checking for uncommitted changes:

   ```sh
   git status --short
   git worktree add -b exec/example ../project-example HEAD
   git rev-parse HEAD
   ```

2. Create `my-contract.json` outside the executor's write scope, with all normal `examples/contract.json` fields PLUS:

   ```json
   {
     "base_commit": "40-character SHA before feature work",
     "approved_paths": ["src/**", "tests/**"],
     "forbidden_paths": ["src/secret.py"]
   }
   ```

   This is a fragment, not a standalone contract. `base_commit` must be the actual recorded Git SHA. `approved_paths` is a list of project-relative patterns: `*` matches within a folder; `**` recurses. `AGENTS.md`, CI workflow files and governance state are always protected.

3. Separate from the executor, approve the exact contract hash (self-asserted local approver identity):

   ```sh
   python3 scripts/governance.py approve --repo ../project-example --contract my-contract.json --actor owner --role owner
   ```

4. Run the actual implementation and **separate independent reviewer** through the configured external CLI. For example, if your Codex CLI supports the supplied role bridge, set `AI_NATIVE_EXECUTOR_CMD` and `AI_NATIVE_REVIEWER_CMD` as in `docs/INTEGRATION.md`. The project contract's commands run in the selected worktree:

   ```sh
   python3 scripts/ai_native.py cycle --repo ../project-example --contract my-contract.json
   ```

   `NOT_VERIFIED` is intentional if no reviewer was invoked. If tests fail, reviewer PASS is not sufficient.

5. **After** the executor commits its branch and a fresh review/check, run the exact-tip merge eligibility gate before merging:

   ```sh
   python3 scripts/governance.py scope --repo ../project-example --contract my-contract.json
   python3 scripts/governance.py eligible --repo ../project-example --contract my-contract.json --requirements ../project-example/verification/requirements.json
   ```

   Requirements are **owned separately from the executor contract**. An appropriate requirements file looks like `examples/requirements.json`, listing every mandatory requirement with `min_level` and `gate_ids`. Missing passing gates or too-low evidence levels cause NOT_ELIGIBLE. For terminal/E2E claims, declare `terminal_required`; the current portable core requires terminal fields but **does not validate external artifact truth**. Keep actual end-to-end/device/GPU proof in the source project's specialized validators; do not treat this CLI alone as sufficient evidence.

6. Merge **only** after `ELIGIBLE`, CI and appropriate review approve the exact branch tip. This script does not execute merges. Put it into a protected GitHub Actions required check / branch rule for real integration enforcement; absent branch protection, GitHub still permits bypassing it.

## Autonomous frontier and human queue

Fill `verification/work.json` in each target repo, using `examples/work.json` as a starting point. Each item declares `id`, `owner`, `status`, `action`, `depends_on`, and explicit blocker/evidence fields where applicable. Commands:

```sh
python3 scripts/frontier.py check --registry examples/work.json
python3 scripts/frontier.py next --registry examples/work.json
python3 scripts/frontier.py human-packet --registry examples/work.json
python3 scripts/frontier.py clean-pass --registry examples/work.json --independent
python3 scripts/frontier.py human-gate --registry examples/work.json
```

A blocked GPU task blocks only its dependants. Other authorized tasks remain eligible. Physical/human tests are queued rather than causing one interruption per missing artifact. `human-gate` requires two explicit clean discovery passes on the *same* registry version. These calls DO NOT automatically launch a model or execute `action`: a host-runner must consume the frontier and repeat after each completed task. An `--independent` flag is an operator attestation, not cryptographic identity.

## P0 safety constraints and limitations

- Approval, contract hash, and reviewed tree fingerprint must agree.
- No protected/forbidden/out-of-scope changes can be merge-eligible.
- No stale review is merge-eligible, even after a trivial source edit.
- Role/environment strings are local claims, not tamper-proof authentication.
- Production integration requires isolated executor permissions, a separately authenticated reviewer, a *required* CI check, and branch protection.
- Binary/device/visual/e2e evidence needs domain-specific adapters; the shared core does not falsely mark it executed.
- No automatic unattended terminal-decider or cost accounting has been integrated yet. See [coverage inventory](PRACTICE_COVERAGE.md).
