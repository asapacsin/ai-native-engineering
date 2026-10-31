# Portable AI-native skills: Claude Code / Codex

This file combines two skill efforts: the evidence-first pair (`verify`, `token-efficient-task`, PR #9) and the cross-client procedure pack with `/goal` (PR #12). It also adds the `ai-research-directions` research skill.

## Layout

| Kind | Location | Who reads it |
| --- | --- | --- |
| Canonical procedure for the PR #12 pack (`goal`, `start`, `reproduce`, `fix`, `verify`, `review-packet`, `continue`, `handoff`, `create-skill`) | `skills/<name>.md` | the agent, via a manifest |
| Codex manifest | `.agents/skills/<name>/SKILL.md` | Codex native discovery; `scripts/skill_catalog.py` for contract-selected injection |
| Claude Code manifest | `.claude/skills/<name>/SKILL.md` | Claude Code native discovery |
| Self-contained skills (`token-efficient-task`, `ai-research-directions`) | full body in `.agents/skills/<name>/`, with a thin `.claude/skills/<name>/SKILL.md` pointer | both clients |

`verify` exists in both efforts. Its Codex `SKILL.md` keeps the full failure-informed body from PR #9 (so contract injection carries real guidance) and links to the PR #12 canonical procedure for the controller commands.

**Open tension, not resolved here:** PR #9 pruned the generic `reproduce`, `fix` and `review-packet` procedures because they had no demonstrated value over `AGENTS.md` and the controller, while PR #12 ships them. Both are included so that no practice is lost. Use the evaluation procedure below to decide which to keep, and remove any that show no measured lift.

## Research skill: `ai-research-directions`

Moves an initial research idea to an evidence-backed shortlist and pilot plan: venue-aware literature search, closest-work mapping, practice/documentation review, gate-first ranking (`scripts/rank_directions.py`) and an optional bounded Semantic Scholar query (`scripts/search_papers.py`). It covers practice rows 19 (research/design basis before major work) and part of 30 (research reproducibility). It never authorizes training, paid compute or restricted data, and it requires web access for live searches. Origin: `asapacsin/omnieeg-research` `.agents/skills/ai-research-directions/`. Its own tool tests run with `python3 .agents/skills/ai-research-directions/scripts/test_tools.py`.

## Use immediately

From the root of this checked-out repository start Claude Code or Codex (with normal workspace trust and tool permissions). In Claude Code invoke:

    /goal Finish the authorized feature, prove the acceptance tests and report anything unverified

In Codex select the goal skill with /skills or invoke:

    $goal Finish the authorized feature, prove the acceptance tests and report anything unverified

Claude /goal is a custom skill; Codex $goal is the corresponding skill invocation, not a guaranteed slash alias. If a newly added skill is not discovered, restart the client and confirm the working directory is within this checkout. If another installed skill has the same name, choose this repository's entry explicitly.

Other skills: start (resume), reproduce (baseline), fix (small correction), verify (fresh gates), review-packet (independent review), continue (authorized frontier), handoff (durable state), create-skill (evidence-led reuse).

## What makes /goal operational rather than a prompt loop

The skill directs the agent to use the repository's existing scripts; there is no new shadow task manager:
- A task contract, independent requirements and explicit gates define success: examples/contract.json, examples/requirements.json.
- A manually authorized work DAG is the source for next actions: examples/work.json is a schema, not a live registry. Each autonomous item needs contract_path to use supervisor.py.
- scripts/frontier.py next prevents one blocked resource from ending independent work.
- scripts/ai_native.py cycle runs deterministic verification and an independently configured external reviewer; missing reviewer is NOT_VERIFIED.
- scripts/supervisor.py is the durable bounded execution loop. It must be launched in an actual host environment with an authenticated executor/reviewer and writable trusted registry. It does not automatically push, merge or authorize contracts.
- .claude/hooks/keep-going.py can advise continuation only when explicitly enabled, and it does not execute the next task.

A quick read-only check from the harness root (does not invoke a model):

    python3 -m unittest discover -s tests -p 'test_skills.py' -v
    python3 scripts/frontier.py check --registry examples/work.json
    python3 scripts/ai_native.py validate --contract examples/contract.json

For a real target repo, first follow docs/INTEGRATION.md and docs/ENVIRONMENT_CONTINUATION.md to set up valid contracts, a gitignored work registry and actual CLI adapters. Choose a disposable branch, enforce scope/approval separately, and run the exact host-owned supervisor command in the goal skill. To adapt this pack to another repo, vendor BOTH client skill folders and the canonical skills/ files, then point scripts/ references to an installed/available AI-native harness; copying only a manifest cannot make the executor or supervisor available.

## Evidence-first selection (from PR #9)

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

## Quality and scope

Tests/test_skills.py checks discoverability and the documented contract; skills/evals.json lists fresh-session behavioral cases. Neither proves that a model obeyed the skill, a real CLI was invoked, a remote branch protection rule was installed, or the target project passed E2E tests. Evaluate the cases with independent sessions before claiming skill reliability, ideally against a no-skill baseline. This shared pack intentionally avoids Android-only scripts, Aurel-only GPU assertions, and manga-specific policy.

Primary references: https://code.claude.com/docs/en/skills and https://learn.chatgpt.com/docs/build-skills ; see docs/AI_BUILDER_BIBLE.md for the underlying engineering method.
