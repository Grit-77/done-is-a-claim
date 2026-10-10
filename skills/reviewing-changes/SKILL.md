---
name: reviewing-changes
description: "Review an actual candidate against the user's acceptance and scope, then carry findings through fixes, affected checks and rereview. Use before claiming a substantive change complete or accepting a worker's implementation."
---

# Reviewing changes

Review the delivered candidate, not the author's confidence or task status.
Support findings with the user's contract, the actual diff and observable
behavior. A review is useful only to the extent its inspected scope is clear.

## Establish the review inputs

1. Read the user outcome, acceptance commands, preserved behavior and scoped
   file ownership. Confirm the assigned checkout and applicable instructions.
2. Identify base and candidate revision, plus uncommitted and untracked inputs.
   Inspect the diff and affected artifacts directly. Verify referenced paths.
3. Read existing check output, command, exit status and input identity. Treat
   author and worker reports as leads; do not turn a result label into evidence.
4. State the review mode. Use an independent reviewer when permitted and
   available with a bounded brief and evidence. Otherwise perform self-review
   explicitly, naming the loss of independence without pretending another agent ran.

## Look for consequential defects

Evaluate the candidate against the original outcome, compatibility, edge cases
and relevant callers. Confirm checks can distinguish the intended behavior from
a plausible failure. A constant assertion, file existence or successful response
alone may not test the boundary the user cares about.

Inspect all affected call sites for a defect class, not only the example fixed.
Check that generated artifacts, consumers or rendered output work where those
are part of acceptance. Name anything inaccessible instead of assuming it works.
Keep aesthetic preferences separate from contract defects and avoid scope growth.

For every supported finding, record severity or practical impact, file locator,
reproduction or evidence, violated outcome and a concrete correction direction.
State uncertainty when evidence is incomplete. Do not invent findings to fill a
quota; a scoped review with no findings is still bounded by what was inspected.

Rerun agreed acceptance yourself on the candidate and the whole relevant suite.
Capture the commands' own exit codes and actual summaries, including collection
counts. Read every required CI result on the identified revision where applicable.
Failed, skipped, unavailable and empty checks remain gaps, even if one check passes.

If a failure needs attribution, use host-discovered `whose-red` when available;
otherwise compare matched runs and report the limits. A baseline failure does not
exonerate extra candidate failures or changed behavior. Use
`debugging-with-evidence` if discovered when a separating experiment is needed.

## Resolve findings without losing the evidence

For a review-only assignment, return findings to the owner without editing.
When fixes are authorized and within your ownership, correct supported defects.
Delegate only within existing permission and available capabilities; coordinate
overlapping writers rather than assuming ownership or requiring arbitrary worktrees.

After each meaningful fix, run affected acceptance and regression checks.
Rereview the changed parts and every unresolved finding; mark a finding resolved
only with evidence for its correction. Continue this loop while authorized fixes
remain. If a blocker prevents a fix or check, state it and its effect on acceptance.
An initial review does not certify edits made afterward.

## Return a current verdict

Bind the final verdict to the resulting revision and dirty inputs. Rerun final
acceptance yourself and confirm the relevant inputs did not change during the run.
Use `evidence-freshness` only at a host-discovered location if available; otherwise
compare the inputs inline. Delivery claims need destination observations within
existing authorization, using discovered `checking-delivery` or inline inspection.

Return review mode and scope, findings and resolutions, files, observed checks,
evidence paths and remaining limits. Say what those observations establish;
an independent review, current green CI or usable delivery each needs its own evidence.
