# Codex continuation: portable project setup

This is the **one supported supervisor**, not a second Ralph Loop:
`scripts/bootstrap_queue.py` converts an approved work-unit list to the registry
consumed by existing `scripts/supervisor.py`. A Codex response ending is **not**
completion; completion needs a current independently reviewed `TASK_VERIFIED`
from `scripts/ai_native.py`. No `AGENTS.md` prompt can keep a terminated
`codex exec` process alive without a host process to invoke the next one.

## What this changes

- Reuses the existing dependency-aware supervisor rather than copying the
  manga project's simpler `project_queue.py` and creating competing state.
- Copies the manga **queue format**: ordered, explicit contract paths.
- Creates an untracked, gitignored `.ai-native/work.json` and never overwrites
  an existing registry. Each task starts `NOT_RUN`.
- `ordered: true` (default) adds a dependency on the previous task;
  `ordered: false` permits independent tasks and explicit `depends_on` IDs.
  Dependencies and contract validation are checked before creating state.
- Supports resumable **verified** work across invocations through the existing
  supervisor. It does not give models authority to approve plans, secrets,
  publication or human-only actions.

## 1. Validate an approved queue

In the **target** repository, create a JSON file (e.g.
`production/ralph/work-units/project-queue.json`):

```json
{
  "schema_version": 1,
  "ordered": true,
  "contracts": [
    "production/ralph/work-units/first-approved-task.json",
    "production/ralph/work-units/second-approved-task.json"
  ]
}
```

Use the **AI-native** contract schema, not the Goose Ralph manifest schema.
Each contract needs a unique `task_id`, `goal`, `acceptance`, an evidence gate,
and execution budgets. Paths are relative to the target repository. The queue
must be explicitly authorized. Use `ordered: false` to permit independent
work (and optionally `{"path": "...", "depends_on": ["other-task-id"]}` entries).
Always keep approval and project-specific QA policies in the target repo.

From the AI-native engineering repository:

```powershell
$engine = (Get-Location).Path
$target = 'D:\桌面\edria-manga'
python "$engine\scripts\bootstrap_queue.py" --repo "$target" --queue production/ralph/work-units/project-queue.json --dry-run
```

Expected: `VALID QUEUE`, with the ordered task IDs. No model calls are made.

## 2. Create the durable registry once

Confirm `$target\.gitignore` includes `.ai-native/`, then run:

```powershell
python "$engine\scripts\bootstrap_queue.py" --repo "$target" --queue production/ralph/work-units/project-queue.json
python "$engine\scripts\frontier.py" next --registry "$target\.ai-native\work.json"
```

The importer refuses to overwrite `.ai-native/work.json` on later runs.
The registry is durable across normal supervisor invocations, **not
automatically backed up by Git**. Preserve it in your normal machine backups.
If a queue changes, review and migrate the existing registry deliberately;
never delete it just to clear a blocker.

## 3. Configure real Codex subprocesses

Install/authenticate the Codex CLI in the machine/account executing the
supervisor. Do not assume the default `gpt-6-luna` and `gpt-6-astra`
strings are accepted API model IDs; verify installed model names and access.

```powershell
codex --version
codex login status
$env:AI_NATIVE_EXECUTOR_CMD = "python $engine\scripts\codex_bridge.py executor"
$env:AI_NATIVE_REVIEWER_CMD = "python $engine\scripts\codex_bridge.py reviewer"
$env:AI_NATIVE_EXECUTOR_MODEL = 'YOUR_VERIFIED_EXECUTOR_MODEL'
$env:AI_NATIVE_REVIEWER_MODEL = 'YOUR_DIFFERENT_VERIFIED_REVIEWER_MODEL'
```

The reviewer must be a genuinely independent, read-only invocation.
Check `docs/INTEGRATION.md` for credential restrictions and model CLI flags.

## 4. Run verified work, not an unbounded loop

```powershell
python "$engine\scripts\supervisor.py" --repo "$target" --registry "$target\.ai-native\work.json" --max-tasks 1 --max-seconds 1800
```

Start with one harmless test contract. After confirming the generated
`$target\.ai-native\runs\<task-id>\latest.json` and registry, raise
`--max-tasks` as appropriate. The controller invokes executor, required
gates and independent reviewer. The supervisor advances to the next eligible
task only on exact `TASK_VERIFIED`.

For delivery-sensitive code use `--require-remote` **only** after the
reviewed commit can actually be pushed to the authorized remote branch;
otherwise it correctly blocks.

## 5. Relaunch after the CLI session stops

Put the above environment setup and supervisor invocation into a local
PowerShell script **outside versioned credentials**. Use Windows Task Scheduler:
Create Task → Triggers → New → choose recurrence; Actions → New →
Start a program `powershell.exe`, arguments
`-NoProfile -File "PATH_TO_YOUR_RUN_SCRIPT.ps1"`. Set **Start in** to your
checkout and **Do not start a new instance** when running. The machine must be
on and authenticated.

### Important stop behavior

- When a whole supervisor invocation reaches its bounded time/task budget,
  rerunning it picks up the remaining eligible tasks. No infinite background
  execution is promised.
- An individual task that exits **unverified** (timeout, missing gates,
  invalid review, interrupted process) is intentionally marked
  `BLOCKED_EXTERNAL`. The supervisor **does not retry it forever**.
  Inspect its evidence, address the failure and deliberately reauthorize
  a retry before changing the task back to `NOT_RUN`. Never reset `PASS`
  or manually assign `PASS` without evidence.
- Restarts are separate Codex CLI sessions that share repository state and
  contracts; they do not automatically resume the same chat transcript.
- This layer does not supply image generation, device/GPU capabilities,
  published manga approval, or automatic canonical task discovery.

## Verification

```powershell
python -m unittest discover -s tests -p "test_bootstrap_queue.py" -v
python -m unittest discover -s tests -v
```

Isolated tests cover dependency ordering, missing/duplicate contracts,
path traversal, dry-run behavior, existing registry protection and ignored
runtime state. These tests do not spend model tokens or demonstrate a live
Codex run.
