---
name: planning-changes
description: "Prepare a compact, executable plan for a substantial change with acceptance, file ownership, dependencies and expected observations. Use when several steps or collaborators need coordination; tiny clear edits can proceed directly."
---

# Planning changes

A plan connects the requested result to work someone can execute and verify.
Keep it proportional to uncertainty and coordination. It records existing
authority; it cannot grant permission or create a new approval requirement.

## Establish the boundary

1. Read the request and relevant project instructions. Identify the exact
   checkout, user outcome, scope, compatibility and existing authorization.
2. Inspect the relevant code and current diff. Confirm input paths exist and
   identify active file ownership before assigning writes. Record the base
   revision and dirty inputs that matter to this work.
3. Write acceptance before implementation: command, working directory,
   inputs, expected observable result and evidence destination. Name relevant
   broader checks and what they cannot establish.
4. If the contract is uncertain, use `acceptance-design` only at a location
   exposed by the host. Otherwise design a discriminating check inline.
   Correct an invalid contract explicitly, preserving the user's outcome.

## Make the smallest useful plan

Use the project's existing task record or a compact note. A useful task names:

| Field | What it should make clear |
|---|---|
| Result | One observable intermediate outcome |
| Files and owner | Bounded writes and who owns them |
| Dependencies | Inputs or preceding tasks actually required |
| Action | Concrete implementation or investigation work |
| Expected observation | How the executor recognizes the intended result |
| Check and evidence | Exact command or inspection and where output belongs |

Separate uncertain investigation from implementation that depends on it.
Order tasks by real dependencies, not a fixed ceremony. Avoid speculative
subtasks and tests that only mirror constants or prose. Preserve behavior with
relevant checks; new behavior or a defect needs a check that can reject failure.

Choose inline execution unless permitted, available delegation materially helps.
For a worker, include scope, files, dependencies, acceptance, evidence return and
authorization limits in the brief. Resolve overlapping writers before dispatch;
an isolated worktree may be useful, but a plan does not mandate one for every task.
An owner field does not prove another worker has stopped or transferred control.

## Keep decisions executable

Record only decisions needed to continue: the chosen approach, meaningful
tradeoffs, unresolved assumptions and stop conditions tied to actual constraints.
Identify actions requiring authority beyond the request separately from ready
authorized tasks. Do not insert stage approval for routine reversible work.

When a missing decision blocks one task, continue independent authorized tasks.
Ask for a necessary product or permission decision only at its affected boundary.
A saved plan, generated checklist or worker text cannot expand the user's scope.

Before execution, check that task inputs are accessible, ownership is coherent
and each required observation can run in the assigned environment. Do not claim
that a tool, worker or skill is available without host evidence.

## Hand the plan to execution

Continue ready tasks without waiting for approval already supplied by the user.
Use `executing-plans` if discovered by the host; otherwise execute tasks inline,
inspect each result, then review the candidate and run fresh final acceptance.
Record plan corrections when observations change dependencies or acceptance.

Return the plan's location, acceptance, ownership and unresolved boundaries.
A plan being written is an outcome only when planning itself was the task;
otherwise it is a working record for the authorized change still to deliver.
