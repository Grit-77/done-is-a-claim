# Handoff

Template for a different session or machine. A handoff is a map to evidence, not
evidence that the new checkout is ready.

```text
Project: <repository identity and intended branch>
Goal: <current user outcome>
Revision: <commit and working-tree state>
Worktree: <intended checkout; machine-local mapping if needed>
Checkpoint: <record identity and revision; read-back time>
Decisions: <only choices the next session must preserve>
Completed: <artifact or behavior, with receipt>
Remaining: <concrete unfinished work>
Active workers: <owner, scope, branch; or none>
Current ownership: <receiver observation; live workers or unresolved overlap>
Checks: <command, inputs, result, evidence location>
Not checked: <gaps and reasons>
Next action: <one actionable step>
Resume boundary: <authorized action and prerequisites still unresolved>
```

On receipt, resolve the repository on the current machine, inspect Git state, and
confirm the cited files exist. A clean checkout at the same commit does not imply
the same environment. Reopen evidence and distinguish historical checks from
observations of the received checkout; repeat checks whose relevant inputs changed.
After checkpointing or stopping, read the final record back: a stop can replace
the next action. On receipt, check current ownership before overlapping writes.
If two sessions left conflicting changes, reconcile them
explicitly; choosing the newest note does not merge the code.

Use the fields relevant to the unfinished boundary. A trivial uninterrupted edit
does not require a handoff, ownership transfer or a new tracking system.
