# Handoff

Template for a different session or machine. A handoff is a map to evidence, not
evidence that the new checkout is ready.

```text
Project: <repository identity and intended branch>
Goal: <current user outcome>
Revision: <commit and working-tree state>
Decisions: <only choices the next session must preserve>
Completed: <artifact or behavior, with receipt>
Remaining: <concrete unfinished work>
Active workers: <owner, scope, branch; or none>
Checks: <command, inputs, result, evidence location>
Not checked: <gaps and reasons>
Next action: <one actionable step>
```

On receipt, resolve the repository on the current machine, inspect Git state, and
confirm the cited files exist. A clean checkout at the same commit does not imply
the same environment. If two sessions left conflicting changes, reconcile them
explicitly; choosing the newest note does not merge the code.
