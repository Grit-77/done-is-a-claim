---
name: evidence-freshness
description: "Bind a check or action to the input snapshot it actually used. Use before relying on cached verification, consuming a reviewed batch, acting while inputs may change, or retrying an operation with an ambiguous result."
---

# Evidence freshness

Evidence remains a statement about its measured snapshot. It supports a later
decision only to the extent that the decision uses that snapshot and relevant
conditions. These are operational safeguards, not a new incident record.

## Pin what the check consumes

1. Identify the input tree and relevant configuration, dependencies, datasets,
   generated inputs, flags and environment. Record the revision and dirty
   state; a commit alone does not describe uncommitted or untracked input.
2. Before the run, hash the selected inputs or a manifest of them. Say what
   the selection excludes; matching a few hashes cannot certify the whole
   repository or an external service. Freeze batch lists into a separate
   snapshot rather than checking a list that remains open for append.
3. Run the named check against that snapshot. Record command, outcome, time
   and evidence location. Retain the tested inputs or enough identifiers to
   reproduce them without treating a log summary as the input identity.
4. Compare the revision, dirty state and selected hashes after the run. Changed
   inputs make the result ambiguous for the new tree. A formatter or fixer
   that mutates its inputs does not certify its resulting tree; run acceptance
   again on the stable result. Distinguish produced outputs from changed inputs.
5. Equal before/after hashes can miss edits made and restored during a run.
   When a result gates a consequential action, use isolated immutable inputs
   or coordination that prevents concurrent writes; hashes alone are not a lock.

## Consume the reviewed snapshot

Use the same bytes and identifiers that were checked: the frozen candidate
list, tested artifact or exact revision. Verify them again immediately before
the action, including the current destination and ownership where relevant.
If anything relevant changed, stop that action and reconcile or recheck;
do not silently substitute a newer list, branch tip or rebuilt artifact.
Where a race can still occur after the comparison, use an atomic conditional
update or equivalent expected-revision mechanism. Otherwise report the limit
and coordinate the action rather than claiming the comparison eliminated it.

## Reconcile ambiguous retries

A timeout or nonzero exit may occur after an output or state change was
created. Inspect the destination, durable records and any existing successor
before retrying. Reuse an operation identity when the system supports it;
otherwise establish whether the first attempt took effect and avoid duplicates.

Report the snapshot checked, snapshot consumed, relevant differences and any
unresolved race. Historical evidence stays valid for its old snapshot;
a claim about current state needs evidence appropriate to that state.
