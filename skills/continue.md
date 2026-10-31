# /continue — no premature stop

1. Re-read the trusted work registry, latest supervisor checkpoint and current source evidence; never infer remaining work from conversation memory. Run:
    python3 scripts/frontier.py check --registry <registry>
    python3 scripts/frontier.py next --registry <registry>
2. If control_decision is CONTINUE_FRONTIER, select an eligible authorized item whose dependencies and required capabilities are satisfied. Run /goal's supervised cycle for that approved contract; repeat only while progress and budget allow.
3. If one task is BLOCKED_EXTERNAL by GPU/device/credential/remote publication, continue unrelated CPU/offline items. Never relax evidence level merely to finish.
4. If the frontier is empty, distinguish STOP_COMPLETE from WAIT_EXTERNAL, HUMAN_HANDOFF, DISCOVERY_REQUIRED or INVALID_STATE. Missing backlog evidence is not automatically COMPLETE. The project release gate is separate from the per-task gate.
5. End when a bound is reached, the same unfinished state repeats, a human-only decision is genuinely needed or no eligible work exists. Preserve checkpoint, specific blocker and next authorized action; never use an infinite Stop-hook loop.
6. Optional Claude hook: see docs/HOOK_CYCLE.md; enable AI_NATIVE_CONTINUE_ENABLED=1 and AI_NATIVE_WORK_REGISTRY only for a validated registry. This hook suggests another task; only a host-owned scripts/supervisor.py actually executes and checkpoints tasks. Codex Cloud does not load this hook automatically.
