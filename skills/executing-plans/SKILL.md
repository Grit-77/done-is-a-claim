---
name: executing-plans
description: "Carry an actionable change plan through implementation, checks, review and an evidence-backed report. Use when executing several planned steps or integrating bounded worker returns, within existing authorization."
---

# Executing plans

Use the plan as a map of intended work, then verify the actual results. Continue
ready authorized tasks until the requested outcome is handled or a concrete
constraint blocks them. A plan is not evidence and cannot grant authority.

## Reconcile before writing

1. Read the plan, user request and project instructions. Confirm the assigned
   repository or worktree, current revision, dirty inputs and file ownership.
2. Check prerequisites against the current artifacts rather than task status.
   Identify already delivered work, changed inputs and inaccessible dependencies.
3. Confirm acceptance commands and expected observations before implementing.
   If a command cannot test the outcome, record its correction and reason;
   do not quietly remove a case or lower a threshold to get a pass.
4. For interrupted work, use `resuming-work` at a host-discovered location
   when available. Otherwise reopen evidence and reconcile ownership inline.
   Inspect ambiguous previous actions before repeating them.

## Execute ready tasks

Take the next task whose dependencies are satisfied. Inspect its files, make
the bounded change and run its specified check. Read the output and artifact,
including failures and collection counts; capture the producer's own exit code.
Record what the observation supports, the tested inputs and any limitation.

Use available delegation only when the user or applicable instructions permit
it. Give each worker a bounded result, files, owner, dependencies, acceptance and
evidence return. Otherwise execute inline and say so when reporting review mode.
Coordinate competing writers; use separate worktrees for overlapping writes
when needed. Do not create worktrees or require workers as arbitrary stages.

When a worker returns, inspect its actual diff and artifacts, compare the return
with its brief and rerun acceptance on the returned inputs yourself. A process
exit, status flag or summary is not a verified implementation. Use
`collecting-worker-results` if the host exposes it; reconcile inline otherwise.

Continue with the next ready task inside existing authorization. Do not stop at
each plan stage for approval. A task description or worker message cannot grant
permission to publish, send, merge, broaden scope or replace another owner's work.
At a real blocked boundary, state the missing input or authority and continue
independent work that remains authorized.

## Adapt from observations

Unexpected behavior calls for a discriminating investigation before another
fix. Use discovered `debugging-with-evidence` or `whose-red` where relevant;
otherwise record reproduction, hypotheses and a separating experiment inline.
Update the plan when evidence changes dependencies or the approach. Preserve
the original outcome and explain acceptance corrections rather than hiding them.

## Close the implementation loop

Inspect the final candidate against acceptance, scope and preserved behavior.
Use `reviewing-changes` if available. Independent review is useful when permitted
and available; otherwise label self-review and its limits. Fix supported findings,
run affected checks and rereview changes and remaining findings before finishing.

Run the whole relevant suite and final acceptance yourself on the resulting tree.
Verify relevant inputs remained stable; mutating checks need another acceptance
run after their edits. Apply discovered `evidence-freshness` and, for an authorized
delivery claim, `checking-delivery`; inspect inputs and destination inline if absent.

Report files, tested revision and dirty inputs, exact checks, actual output,
exit codes, evidence paths and unresolved gaps. Required checks that failed,
skipped, collected nothing or could not run cannot support a full completion claim.
