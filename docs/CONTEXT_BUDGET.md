# Portable context and token-budget protocol

Source: [NovaDrive iOS token-budget specification](https://github.com/asapacsin/iOS_Automotive_Voice_Agent/blob/main/specs/token-budget.md), November 19, 2026. Port the **protocol**, not the iOS-specific feature paths, Swift gates or status schema.

## Objective and observed baseline

Optimize **validated outcomes per dollar and hour**, not minimum prompt length. The iOS source reports that a repeated full read of a ~160 KB feature spec costs roughly 40k–50k tokens. Its first history pass archived 120 completed items and moved 101 status rows, leaving hot STATUS.md at ~62 KB and work.json at ~91 KB. Those are source-project estimates and file sizes, **not measured token-billing or throughput improvements** in this shared repo.

## Section-based retrieval (implemented)

    python3 scripts/spec_section.py /path/to/project/specs/features/trip-plan.md
    python3 scripts/spec_section.py /path/to/project/specs/features/trip-plan.md 51
    python3 scripts/spec_section.py /path/to/project/specs/features/trip-plan.md 5.2
    python3 scripts/spec_section.py docs/AI_BUILDER_BIBLE.md "Model policy"

The first command lists headings, line ranges and sizes; subsequent commands return only the named section. Headings within fenced code are ignored and the index is rebuilt each run. A section above 40 KB requires an explicit larger --max-bytes or a narrower Read offset/limit. **This tool does not physically split or rewrite the original spec**; use it before considering a costly and brittle file-sharding migration.

Load task -> named spec section -> required contracts -> relevant acceptance rows -> targeted code references. Request a dependency outside that set only with a reason, and retain safety/integration information required for correctness.

## Read budget (implemented)

The Claude Code PreToolUse Read hook is registered in this repo's .claude/settings.json. It denies whole-file Read of text files larger than 40 KiB without offset or limit. Small files, scoped Read, missing/unreadable paths, known binary types and other tools pass. Relative paths use the tool event cwd.

- Set AI_NATIVE_READ_GUARD_KB=80 for an 80 KiB limit; 0 disables it.
- When copying to another repo, merge hook entries rather than overwriting existing settings.
- This **fail-open optimization hint** is distinct from the **fail-closed security-sensitive write/command guard** (scripts/pre_tool_guard.py). Other read tools can bypass it. Never use it to authorize access or to drop acceptance evidence.

## Agent routing and review (operating policy)

Use the main Executor for implementation and ordinary fixes, a low-cost read-only search agent for narrow location/symbol questions where supported, and a truly **independent** Reviewer for final acceptance. The search agent is not an independent verifier. The existing review_scope manifest already gives the Reviewer a complete changed-file inventory, source fingerprint, diff and allowed context; let it expand into callers/tests with a recorded reason. Model tier and agent syntax are client-specific. Avoid redundant subagent calls and repeated entire-document reviews; compare actual cost/quality on the task.

At a natural batch boundary, save canonical task and evidence state and use the client's supported context-reset command when needed. Do not trigger extra Stop-hook cycles while awaiting human-only work. Parallel agents are worthwhile only for independently scoped tasks with clear outputs.

## Hot/cold history policy (adapter needed; not implemented in shared core)

The iOS repository's scripts/history.py is **specific to its specs/work.json and STATUS.md**. Do not directly run it on this repository's runtime registries or evidence.

For a target project adapter:
1. Check live registry/status sizes on prompt submission, **not Stop**, to avoid unwanted continuation loops.
2. Show a compact table of terminal candidates, open dependents and still-unverified device/human work.
3. Require a reasoned KEEP / SUMMARIZE / ARCHIVE decision per item. Never archive unfinished, failed or externally/human-blocked work.
4. Preserve a minimal dependency-resolving stub (id, terminal status, evidence pointer), and save full originals in searchable archives. Mixed status rows move only when every referenced task is archived.
5. Fail on duplicate ids, missing archive records or invalid cross-references. Preserve immutable acceptance/device evidence, run frontier checks and required gates, then commit the archive with decisions.

Archive policy is documented here but **not auto-enabled** until a project-specific schema adapter and tests exist.

## Verify and measure

    python3 -m unittest discover -s tests -v
    python3 scripts/spec_section.py docs/AI_BUILDER_BIBLE.md

Compare before/after on matched task batches: measured input/output tokens and provider cost, number of subagent calls, elapsed time, accepted tasks, reopened defects, and reviewer missing-context findings. State sample counts and preferably p50/p95. Do not claim a percentage savings merely from reduced file sizes. Spec/index or guard execution is not evidence that external model usage became cheaper.
