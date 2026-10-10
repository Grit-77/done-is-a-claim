---
name: acceptance-design
description: "Define executable acceptance for a bounded task before work or dispatch. Use when writing a worker brief, selecting success checks, or repairing an acceptance contract that cannot test the intended outcome."
---

# Acceptance design

Acceptance connects the user's outcome to an observable check. Design it before
implementation, and give the worker the exact contract the reviewer will use.
These are operational instructions, not measured failure-rate claims.

## Define the experiment

1. Name the outcome, affected boundary and scope. Check the command, loader,
   artifact or user flow actually affected; a helper test alone may miss the
   boundary defect. Identify what the check deliberately leaves untested.
2. Name the target host or platform, runner, dependencies, permissions and
   inputs. Confirm required source files exist in the delivered base and
   travel with the brief. Distinguish existing input paths from files to create.
3. Record the exact command, expected observable result and evidence location.
   Test that it launches on the target environment before dispatch. Prefer a
   repository script when shell quoting or setup would make the command fragile.
   Do not depend on an undocumented interpreter or hidden login state.
4. Scope every planned write, including tests and generated artifacts. Make
   predecessors available in the delivered base, or route the task to a
   checkout that contains them. A named branch is not necessarily accessible.

## Separate change from preservation

- For a defect or new behavior, demonstrate that the check rejects the old
  behavior for the intended reason when feasible. A missing tool or test path
  is not that demonstration. If a baseline run is unavailable, state the gap.
- For preservation, establish the existing behavior and require it to remain
  valid. Do not demand a failing baseline for behavior meant to stay unchanged.
- Vary meaningful inputs and inspect outputs where the contract depends on
  them. A mocked success, repeated implementation constant or file's existence
  may prove less than the required outcome. Include relevant regression scope.
- If a worker cannot run a required live-service or platform check, assign it
  to a suitable verifier and retain it as required. Local success cannot stand
  in for the missing boundary check.

## Freeze and correct the contract

Put the exact commands, inputs, preservation requirements and stop conditions
in the brief. Worker and reviewer use the same contract on identified trees.
If the check is wrong or unrunnable, report the mismatch before continuing
dependent work. The task owner records the old and replacement contracts, the
reason and how the replacement still tests the intended outcome. Revalidate
the replacement before resuming; do not silently lower a threshold, remove a
failing case or relabel a failure as success. A changed user requirement is a
scope change to record, not evidence that the old contract passed.

Acceptance is designed when it can distinguish the required outcome from a
plausible failure, runs where assigned, and preserves the agreed boundaries.
