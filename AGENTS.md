# AI-native agent operating contract

1. **Executor-first**: default to a capable low-cost executor for routine scoped tasks. Do not spin up Architect, Planner, or Reviewer before they are needed. Pick actual model in the external agent client; this repo cannot override provider entitlement.
2. First inspect the existing owner, source, ADR/spec, state, git status, and current acceptance. Research upstream documentation/community solutions before inventing new infrastructure.
3. Author a small JSON task contract with `goal`, `acceptance`, `boundaries`, exact gate commands, time limits, and `task_id`.
4. Delegate implementation to the Executor in an isolated worktree/branch when useful. Never weaken tests or create parallel implementation owners to get green checks.
5. On executor end, run `scripts/ai_native.py cycle`: run deterministic gates, capture commit + dirty diff/untracked fingerprint, then call an **independent read-only** Reviewer through an explicitly configured external command.
6. Verdicts: `PASS` (acceptance evidence and independent review), `REWORK` (targeted fixes), `BLOCKED` (named missing dependency), `NOT_VERIFIED` (cannot support completion claim). Reviewer's words alone never override a failed required gate.
7. At most 3 attempts and a defined time/cost budget. Escalate ambiguous architecture, two failed attempts, invariant conflict, or genuinely expensive experiments to Architect; do not routinely send trivial work to expensive models.
8. Continue only authorized independent tasks. Stop on truly human-only actions, credentials or irreversible decisions; record and batch human requests rather than asking for every routine next step.
9. Results must bind to actual source revision/worktree fingerprint. Compile != runtime; JVM != device; offline model clip != live performance. Record evidence level and what was NOT verified.
10. No secrets in reports, logs, commits, agent prompts or model inputs. Never claim this skeleton has called a real LLM without an explicitly configured reviewer/executor CLI.

Canonical method: [`docs/AI_BUILDER_BIBLE.md`](docs/AI_BUILDER_BIBLE.md).
