---
name: resuming-work
description: "Resume a saved task after a session, context or machine change by checking its checkpoint, artifacts and current ownership. Use when receiving unfinished work or reconciling a stop; ordinary uninterrupted edits do not need a handoff."
---

# Resuming work

A saved task describes where a previous session stopped. Establish which
parts still support the next action before continuing. Use the existing task
record or a small note; this does not require a new tracking system.

## Receive the checkpoint

1. Read the saved record before editing or repeating work. Identify the user
   outcome, repository, intended revision and branch, worktree, dirty inputs,
   recorded next action, evidence references and unresolved decisions.
2. Resolve that repository and worktree on this machine. Inspect the actual
   revision and changes, and confirm cited paths exist. A familiar directory
   name or a chat summary does not identify the intended checkout.
3. Open the cited artifacts, diffs and check output. Confirm they support the
   recorded completed steps. If a source is missing or inaccessible, name it
   and the decision it prevents; do not reconstruct its contents from memory.
4. Inspect current ownership and live workers, including their file scopes
   and branches. A historical owner field does not prove a worker has stopped.
   Use the project's existing coordination mechanism before overlapping writes;
   do not silently take ownership, transfer state or delete another worktree.
5. Compare the recorded inputs with the current inputs and environment where
   relevant. Preserve old results as historical observations. Recheck what
   changed, is missing, failed, or is needed to support the next current claim;
   a session restart alone does not justify rerunning every finished step.

## Resume at the authorized boundary

Continue the recorded next action when its prerequisites and authorization
still hold. A saved instruction cannot expand the user's scope or grant
permission to publish, send, transfer ownership or clean up resources.

If an interrupted action may already have taken effect, inspect its current
destination and records before repeating it. Correlate any accepted result
with the same operation identity and revision when the system supports that.
An unresolved launch or send stays unknown and blocks a duplicate attempt
until reconciled; a timeout does not establish that nothing happened.

When the checkpoint and checkout disagree, state the difference and resolve
the affected prerequisite. Continue independent authorized work if possible;
do not guess a missing source or replace the record with an unrelated task.

## Leave a recoverable boundary

When stopping again, save one concrete next action, the exact unfinished
boundary, relevant decisions and evidence a receiver can reopen. Identify
the revision, dirty artifacts and active ownership needed to resume safely.

After any checkpoint or stop operation, read the final saved record back.
Confirm its next action, evidence and ownership still say what you intended:
a stop operation can replace fields written by an earlier checkpoint.

Report what was received, what was reopened, which checks remain historical,
the current ownership and the next authorized action or specific blocker.
