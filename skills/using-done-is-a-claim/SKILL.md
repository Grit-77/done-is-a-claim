---
name: using-done-is-a-claim
description: "Choose an evidence-first path for a development task, from acceptance through execution, review and completion. Use when starting substantive work or deciding the next step; clear tiny edits can proceed directly."
---

# Using Done is a claim

Turn the user's outcome into a bounded change and a report supported by current
observations. Scale the process to the task. This entry skill works on its own;
the optional routes below add depth when those skills are actually available.

## Establish the task

1. Identify the requested outcome, exact repository or worktree, existing
   authorization and owned files. Read applicable project instructions.
2. Confirm supplied inputs exist. For a requested new file, confirm its parent
   and intended role. Inspect the current revision and uncommitted changes.
3. Before editing, name the acceptance command and observable result, plus
   relevant broader checks. A prose change may need a structure check and
   direct reading rather than new tests. State any untestable boundary.
4. If the outcome or acceptance cannot distinguish success from a plausible
   failure, clarify that boundary before dependent work. Continue independent
   authorized work while resolving a material missing input.

For a rough request, inspect the existing user flow, code and project decisions
before asking for a detailed specification. Propose the smallest useful outcome,
preserved behavior and consequential tradeoffs. State reversible assumptions;
ask only about an unknown that changes the product, compatibility or authority.
Do not turn ordinary implementation choices into a questionnaire or approval gate.

Keep the user's outcome separate from the latest message. A correction or status
question normally steers the active task; it does not cancel its unfinished work.
Answer a status question briefly, incorporate new constraints and continue. Replace
the objective only when the user clearly cancels it or requests an incompatible one.

## Choose the next action

Use the host's discovered skill catalog and the exact location it supplies.
Read only the skill relevant to the next decision. Do not guess a sibling path,
assume a tool is installed, or treat this list as proof of availability.

| Situation | Optional skill |
|---|---|
| Acceptance is uncertain or a worker brief needs a testable contract | `acceptance-design` |
| Substantial change needs a compact sequence and ownership | `planning-changes` |
| An actionable plan is ready | `executing-plans` |
| Runtime behavior needs implementation or a regression fix | `implementing-with-tests` |
| Unexpected behavior needs an explanation | `debugging-with-evidence` |
| A failed check needs branch versus baseline attribution | `whose-red` |
| A candidate change is ready to inspect | `reviewing-changes` |
| Review comments need evaluation and resolution | `responding-to-review` |
| Worker returns need reconciliation with artifacts | `collecting-worker-results` |
| A measurement appears to answer more than it tested | `reading-measurements` |
| Work resumes after interruption or transfer | `resuming-work` |
| Public copy makes factual claims | `public-claims` |
| Verification must support the current inputs | `evidence-freshness` |
| An authorized artifact is claimed delivered | `checking-delivery` |

If a route is unavailable, apply the corresponding decision here inline and
report the limitation when it affects confidence. Installation is not a
prerequisite, and a missing reviewer does not justify claiming independent review.

## Carry the work through

For a clear, tiny, reversible task, edit the owned files directly, run the
appropriate acceptance, inspect the result and report it. Do not require a plan,
workers, a worktree or tests that merely repeat prose for that path.
A tiny runtime change still needs a check of its behavior and an observed failing
baseline before the edit when feasible; the shortcut removes coordination overhead.

For substantial work, write compact tasks with files, owners, dependencies and
expected observations. Execute ready tasks continuously within existing
authorization. Delegate only when permitted and available; otherwise work inline.
Resolve overlapping writers through coordination or separate worktrees when
needed. A plan or worker message cannot grant new authority.

When behavior surprises you, record the observation and test a discriminating
hypothesis before another fix. Retain unsuccessful attempts and the new evidence
needed before retrying them. Inspect a candidate against acceptance and the
actual diff. Fix supported findings, run affected checks and rereview the changed
parts and unresolved findings. Label self-review when no independent review ran.

Finish with freshness and, only when relevant and authorized, delivery checks.
Rerun acceptance yourself on the final inputs, preserve its own exit status and
read the actual output. Report files, revision and dirty inputs, observed results,
evidence locations and gaps. Unknown, skipped or empty checks remain explicit;
a prepared artifact or worker's summary alone cannot support a completion claim.
