# /handoff — durable truth over transcript

1. Inspect git status, revision, approved scope and the latest task report or supervisor checkpoint. Do not overwrite pre-existing user edits.
2. Record task_id, goal, branch/commit and dirty state, changed files, exact gate command + outcome + proof level, independent reviewer status, unfinished checks, blockers, and one next executable step.
3. Store mutable run/registry/handoff state in the trusted .ai-native/ location or an external workspace, not as invented PASS fields in tracked source. Keep secrets and customer content out of logs and reports.
4. Commit/push only when authorized; a clean local commit is not remote delivery. If the target requires remote proof, verify the authorized remote tip via the delivery gate and report unresolved mismatch.
5. Recompute scripts/frontier.py next before ending. Report COMPLETE only after /goal's required end-state and independent release checks; otherwise report an honest paused or blocked status.
