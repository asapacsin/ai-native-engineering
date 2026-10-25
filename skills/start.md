# /start — bounded context recovery

1. Run git status --short and git rev-parse HEAD in the target repo. Preserve changes from other actors.
2. Read AGENTS.md, task contract, requirements manifest and the relevant source/spec owner; inspect only the needed sections of long logs/specs.
3. If a registry exists, run python3 scripts/frontier.py check --registry <path> and python3 scripts/frontier.py next --registry <path>. Treat a missing registry as NOT_CONFIGURED, not as an empty successful project.
4. Inspect the active task's .ai-native/runs/<task-id>/latest.json and any supervisor checkpoint; do not rely on a past assistant summary. Check whether snapshot/contract/revision is current.
5. Report concise state: current branch/tip, active goal, eligible next task, required gate, blocker, and unverified evidence. Pass control to /goal or /continue. Do not read entire large backlogs or launch a costly agent merely to produce status.
