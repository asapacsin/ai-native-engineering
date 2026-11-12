# Continue to the requested deliverable

An agent can save useful work while still failing the user's task by ending
after each artifact or reviewer handoff. A checkpoint is progress; the unit of
completion remains the deliverable the user authorized. These are operating
rules for the executing host and agent, not a new runtime mechanism.

## Define the completion scope

Record the parent deliverable and its acceptance criteria before splitting it
into work items. Include the required artifacts, assembly/integration, review
dispositions and delivery evidence. Register the authorized work and its
dependencies with the existing frontier; a single task's PASS does not establish
that this registry covers the entire request. Do not shrink the scope to the
last artifact produced, invent new requirements, or bypass existing approvals.

For example, a request to finish a 20-page illustrated chapter includes its
required pages, lettering, assembled reader, review corrections and agreed
exports. Fifteen saved images or a review request cannot establish completion.
Domain-specific visual acceptance belongs in the project's adapter/contract.

## Keep checkpoint, review and completion separate

| Event | Required next action |
| --- | --- |
| Artifact saved or Git commit pushed | Preserve provenance and continue the next authorized step. A push is backup/delivery evidence, not reviewer approval. |
| Review requested | Send the actual artifact, governing spec and acceptance context to the designated independent reviewer; await its result. Dispatch alone is not review evidence. |
| Review returns actionable REWORK | Apply the findings and resubmit within the declared attempt/time/cost bounds. |
| Task verified | Recompute the frontier; continue eligible work while within bounds. |
| All required work accepted and delivered | Report completion with evidence for the parent deliverable. Keep merge/publication authorization separate. |
| Dependency unavailable, user interruption, host limitation or bound reached | Preserve progress and report the specific incomplete disposition; never label it COMPLETE. |

Ordinary review latency is not an external dependency failure. In a tool-enabled
chat, wait for the review tool/agent while providing progress updates; do not
end the turn simply because a reviewer was dispatched. A reviewer error,
unavailable configured reviewer or exhausted review timeout is a different,
observable condition and must be reported accurately. Follow existing
control-plane decisions and bounds; these rules do not authorize unlimited
retries, invented reviewer verdicts or overriding a stop decision.

## Make runtime activation explicit

Use the mode the host actually supports:

- **Interactive tool-enabled agent:** continue tool calls and review/correction
  cycles during the active task. Use commentary for checkpoints. A final chat
  response ends that execution turn; do not imply it continues in the background.
- **Externally supervised execution:** configure and invoke the existing
  supervisor with real Executor/Reviewer commands, a trusted registry,
  capability snapshot and declared bounds. Record its actual observed run and
  decision. See [environment continuation](ENVIRONMENT_CONTINUATION.md).
- **Compatible Claude Code host:** the optional [Stop hook](HOOK_CYCLE.md) can
  supply bounded continuation instructions only when explicitly enabled and
  configured. Its allow-stop cases remain unchanged.

Copying this guide, adding AGENTS.md rules, installing scripts or creating a
sample registry does not activate any of these mechanisms. A Claude hook must
not be claimed to supervise a standalone Codex conversation. Report setup,
activation and observed operation separately.

## Audit before ending an execution task

State whether the full requested acceptance has evidence. If work remains,
identify its next action and continue when it is authorized and executable.
If stopping early, identify the actual failed action or exhausted bound, the
remaining work and preserved checkpoint, and the condition needed to resume.
An internal checkpoint or routine REWORK verdict alone is not that condition.
