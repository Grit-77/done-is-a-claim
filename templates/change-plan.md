# Change plan

Template only. Keep the plan as small as the task permits; a tiny clear edit may
proceed directly. Record existing authority rather than inventing approval stages.

```text
Outcome: <observable result requested by the user>
Checkout: <repository/worktree, branch, base revision, relevant dirty inputs>
Scope: <owned files or responsibilities; preserved behavior>
Authority: <what the user already authorized; real unresolved boundaries>
Acceptance: <exact command, working directory, inputs, expected observation>
Broader checks: <relevant suite/build/inspection; known limits>

Task <id>: <bounded result>
  Files / owner: <write scope and current owner>
  Depends on: <task ids or accessible inputs; none if independent>
  Action: <concrete work>
  Expected observation: <result distinguishing success from failure>
  Check / evidence: <command or inspection and evidence destination>

Decisions: <only choices and tradeoffs needed to execute>
Unresolved: <missing input or decision; effect on dependent tasks>
Next action: <ready authorized task>
Corrections: <changed plan/acceptance, reason and preserved outcome>
```

Execute ready work continuously within existing authorization. Worker briefs do
not grant new authority. Delegate only when permitted and available; use inline
execution otherwise. Resolve overlapping writes before dispatch.
