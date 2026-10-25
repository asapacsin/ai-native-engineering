# Portable AI-native skills: Claude Code / Codex

This repository keeps a single procedural source in skills/<name>.md. The two thin discoverable manifests link to that source: .claude/skills/<name>/SKILL.md for Claude Code, and .agents/skills/<name>/SKILL.md for Codex. The local CLI client loads the manifests only when running in a checkout that contains this repository. These are guidance skills, not privileged enforcement or remote work schedulers.

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

## Quality and scope

Tests/test_skills.py checks discoverability and the documented contract; skills/evals.json lists fresh-session behavioral cases. Neither proves that a model obeyed the skill, a real CLI was invoked, a remote branch protection rule was installed, or the target project passed E2E tests. Evaluate the cases with independent sessions before claiming skill reliability, ideally against a no-skill baseline. This shared pack intentionally avoids Android-only scripts, Aurel-only GPU assertions, and manga-specific policy.

Primary references: https://code.claude.com/docs/en/skills and https://learn.chatgpt.com/docs/build-skills ; see docs/AI_BUILDER_BIBLE.md for the underlying engineering method.
