# Portable skills: evidence-first deployment (2026-10-25)

## Decision

The initial five procedures were **not** evidence of improved effectiveness. After inspecting [Nova Drive's skill policy](https://github.com/asapacsin/Android_Automotive_Voice_Agent/blob/main/harness/SKILL_POLICY.md), we **removed** generic `reproduce`, `fix`, and `review-packet`: they reiterated existing AGENTS/controller requirements and had no demonstrated marginal value. Prefer deterministic scripts for repeatable actions, hard gates for invariants, and skills only for repeatable tasks requiring judgment.

Two existing, failure-informed procedures remain:

| Skill | Concrete problem solved | Real incident/source |
| --- | --- | --- |
| `verify` | Avoid stale test evidence, build-variant mixing, concurrent test artifacts, and falsely promoting unit tests to live hardware success | [Nova Drive verify](https://github.com/asapacsin/Android_Automotive_Voice_Agent/blob/main/skills/verify.md), [review packet](https://github.com/asapacsin/Android_Automotive_Voice_Agent/blob/main/skills/review-packet.md) |
| `token-efficient-task` | Avoid loading entire huge test matrices/issue files and shipping full logs to every agent turn | [Nova Drive token-efficient task](https://github.com/asapacsin/Android_Automotive_Voice_Agent/blob/main/.claude/skills/token-efficient-task/SKILL.md) |

The contents live in `.agents/skills/<name>/SKILL.md`, the native Codex repository discovery location. Their instructions are context guidance, not a substituted gate/reviewer.

## Deployment choices (do not mix up discovery and execution)

**A. External Codex controller, explicit selection (existing harness)**

Add `"skill": "verify"` to an approved task contract (see `examples/skill-contract.json`). Run:

    python3 scripts/ai_native.py validate --contract examples/skill-contract.json

On the authenticated host, point `AI_NATIVE_EXECUTOR_CMD` and `AI_NATIVE_REVIEWER_CMD` to the absolute `scripts/codex_bridge.py` paths and invoke `scripts/ai_native.py cycle --repo <target-project> --contract <approved-contract>`. The named skill is validated, hashed with the contract and **injected into the Executor prompt only**. Existing contracts work without any `skill` key. The reviewer and deterministic gates remain independent.

**B. Native Codex discovery inside another repository, opt-in (no contract needed)**

Codex discovers `<target-repo>/.agents/skills/<name>/SKILL.md` automatically. To install from this shared repo without overwriting existing project skills:

    python3 scripts/install_skills.py --target /path/to/target-project --skill verify --dry-run
    python3 scripts/install_skills.py --target /path/to/target-project --skill verify

Run Codex **from the target repository**. The user can explicitly invoke `$verify`; implicit triggering depends on the skill description and must be evaluated. Prefer a target's existing specialized skill (for example Nova Drive already has a specialized Claude verification procedure) rather than installing a generic duplicate. This installer copies static skill files, not enforcement scripts, credentials, or the controller. Existing different files fail closed; identical content is idempotent.

**C. Claude Code / other agents**

Native discovery paths and supported hooks differ. Do **not** assume `.agents/skills` is automatically found by every client or that an injected Codex prompt becomes a native Claude skill. Keep client-specific adapters thin and test real behavior.

## How to know whether a skill earns a place

1. Collect real repeated failures/traces. Follow the [source skill policy](https://github.com/asapacsin/Android_Automotive_Voice_Agent/blob/main/harness/SKILL_POLICY.md): repeated meaningful workflow >=3 observations; modify after >=2 repeated deviations; stale/wrong command warrants immediate repair.
2. Define **positive and negative trigger cases** before rollout. See `evals/skill_cases.json`. Measure unintended activation, not only success when explicitly given a skill.
3. Run matched baseline (no skill) and skill versions on the **same task contract** except `skill`, with the same model, fresh comparable worktrees, identical tools and separately verifiable acceptance. Run at least 5 comparable pairs per skill before drawing conclusions; vary task difficulty and domain.
4. Use `scripts/skill_eval.py` to compare **controller evidence** from one pair. A successful controller verdict is not a guarantee of real device/E2E performance. Record token usage, total cost, wall time, retries and intervention separately from actual provider traces.
5. Only retain a skill when independent correctness is at least unchanged **and** its measured improvement justifies added cost/context. If no meaningful lift, remove it rather than increasing instructions.

## External evidence

- [OpenAI: Testing Agent Skills Systematically with Evals](https://developers.openai.com/blog/eval-skills)
- [NVIDIA: SkillEvaluator](https://developer.nvidia.com/blog/evaluating-ai-agent-skill-performance-with-nvidia-skillevaluator/) — includes live with/without comparisons and overlap detection
- [UCSB: How Well Do Agentic Skills Work in the Wild](https://arxiv.org/abs/2604.04323) — gains decay in realistic retrieval settings
- [Codex: Build Skills](https://learn.chatgpt.com/docs/build-skills) — native `.agents/skills` discovery and explicit/implicit triggering

**Verification honesty:** CI in this repository checks static catalogs, deterministic comparison and tests. A paid live Codex/Claude A/B or Android/Aurel hardware/GPU run is NOT_VERIFIED until actual runner evidence is recorded. No skill uplift percentage is claimed.
