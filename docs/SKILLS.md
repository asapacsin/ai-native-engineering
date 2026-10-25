# Portable task skills (opt-in)

This repository now packages five small, reusable Agent Skills under `skills/<name>/SKILL.md`, distilled from the [Nova Drive procedures](https://github.com/asapacsin/Android_Automotive_Voice_Agent/tree/main/.claude/skills). The shared versions deliberately remove Android-only commands and state paths. The target project's source-of-truth, approved contract, invariants and deterministic acceptance checks always take precedence.

## Available skills

| Contract name | When to select |
| --- | --- |
| `reproduce` | Establish a defect before proposing a fix |
| `fix` | Implement the smallest correct fix after reproduction |
| `verify` | Collect accurate scope-specific validation evidence |
| `review-packet` | Prepare independent review artifacts and find proof gaps |
| `token-efficient-task` | Reduce unnecessary context in large repositories |

A skill is procedural guidance, *not* an executable gate, a trusted reviewer, a credential boundary or a replacement for project adapters.

## Run through the Codex bridge

1. Choose the skill **explicitly** in the approved JSON task contract: `"skill": "fix"`. Do not rely on keyword heuristics. Existing contracts without `skill` work exactly as before.
2. Validate before spending model tokens:
   
       python3 scripts/ai_native.py validate --contract examples/skill-contract.json

   Unknown names, path traversal, broken frontmatter or oversized skills fail validation.
3. Point the external executor and reviewer commands at the Codex bridge, using the authenticated host environment:

       export AI_NATIVE_EXECUTOR_CMD="python3 /absolute/path/ai-native-engineering/scripts/codex_bridge.py executor"
       export AI_NATIVE_REVIEWER_CMD="python3 /absolute/path/ai-native-engineering/scripts/codex_bridge.py reviewer"
       python3 /absolute/path/ai-native-engineering/scripts/ai_native.py cycle --repo /path/to/target-project --contract /path/to/approved-contract.json

The controller validates the name and includes it in the hashed contract. The Codex **executor** bridge reads the trusted skill definition from the shared repository and includes it in the executor prompt even when working in a different target repository. The **reviewer does not receive executor skill instructions**. Tool permissions, reviewer independence and all required gates remain unchanged.

Other executor CLIs require an adapter that reads and applies the same contract field; this PR does **not** automatically install skills into Claude Code, Codex Cloud, Cursor, or project-local skill directories. Skills run via prompt injection into the explicitly configured Codex CLI bridge only. The target environment must still provide the project's tools and authentication.

## Evaluate rather than assume

Run at least two matched tasks per skill with identical scope, acceptance and model configuration: one with no `skill` field and one with the chosen skill, both from fresh comparable worktrees. Record source revision, correctness against independently checked acceptance, false-PASS, human interventions, retries, wall-clock time, token usage, and total cost when observable. Do not claim improved effectiveness from unit tests alone.

The bundled unit tests prove catalog validation and prompt selection, not quality gains, real paid-model integration, native skill discovery or Android/Aurel device/GPU acceptance. Keep deterministic logic in scripts, and only create further skills from repeated, evidenced procedures.
