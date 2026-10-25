# /create-skill — evidence-backed skill development

1. Collect 2+ real repetitions, corrections or failed runs and describe the missing capability, expected outcome, concrete trigger phrases and failure modes. Do not add a skill for a one-off fact.
2. If all steps are deterministic, implement a tested script or control-plane invariant instead. If judgment is needed, keep a skill with an imperative default path, narrow exceptions and gotchas.
3. Author a canonical skills/<name>.md procedure and mirrored .claude/skills/<name>/SKILL.md and .agents/skills/<name>/SKILL.md discovery manifests. The descriptions must identify when to invoke and when not. Reuse existing names instead of adding synonyms.
4. Add 2-3 realistic skill evaluation prompts including one blocked or negative case under skills/evals.json. Run fresh agent sessions with and without the proposed skill and compare task correctness, required evidence, wall time and total model cost. A manifest/test passing does not prove a behavioral improvement.
5. Keep changes only when the evaluated behavior improves. After two weak revisions, remove or merge the skill. Do not unilaterally modify hooks, branch protections, approvals, cost policy or the user's security boundaries just to make skill execution easier.
