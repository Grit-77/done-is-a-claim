---
name: collecting-worker-results
description: "Inspect a stopped worker's returned work and evidence before accepting it, retrying it or handing it to an integration owner. Use when a worker finishes, records disagree, or a green result has no visible change. Collection does not authorize merging."
---

# Collecting worker results

A worker stopping, delivering a change and satisfying a task are different
events. Reconcile the report, returned files and verification before deciding
what was delivered. These are operational checks, not incident statistics.

## Separate the records

| Observation | Supports | Does not establish |
|---|---|---|
| Process exit or runner status | The recorded process outcome | A delivered change or acceptance |
| Worker report | The worker's account of work and blockers | Independent verification |
| Commits, patches and working-tree diff | A change footprint against a named base | Correctness or integration |
| Acceptance record | The result on its recorded input tree | A pass on a different returned tree |
| Destination state | What reached the target revision or location | That it matches the tested work |

## Procedure

1. Confirm the run identity and that the worker stopped; a stale status or
   another process with the same name is insufficient. Collect only the
   assigned result. Resolve competing ownership before changing shared state.
2. Read the report and blockers, then inspect the returned base, tip, commits,
   tracked diff and untracked files. A clean tree with no new commits may mean
   no change, an already-delivered change or a patch elsewhere; investigate.
3. Compare the footprint with the task scope. A report-only return may satisfy
   a reporting task, but is not an implementation. Identify unrelated or stacked
   changes without assuming commit dates reliably establish ownership.
4. Read the tested revision, input hashes, command, environment and actual
   result before its success flag. If the check measured an unchanged baseline,
   it demonstrates baseline behavior, not a requested implementation.
   An unchanged return can still satisfy an explicitly observational task.
5. Rerun the agreed acceptance on the returned input tree yourself, plus the
   relevant regression checks. Preserve the command's exit status and log.
   A changed or incompletely identified tree needs new evidence. If checks
   cannot run, report that limit; do not translate it into a pass.
6. Reconcile discrepancies: a failed packaging step can coexist with tested
   work, and a successful process can deliver none. Investigate environment
   and baseline failures rather than assigning cause from a label alone.
7. Before retrying a partial or ambiguous operation, inspect existing output,
   current state and any successor task. Record the cause and changed brief;
   an earlier nonzero exit does not prove nothing was created.

## Handover

Return task identity, base, delivered branch or patch, tested tree and hashes,
commands/results, evidence locations, blockers and the proposed next step.
State whether the work is only returned, verified or already integrated.
Hand verified work to its integration owner; do not automatically commit,
merge, cherry-pick or close another owner's task during collection.
