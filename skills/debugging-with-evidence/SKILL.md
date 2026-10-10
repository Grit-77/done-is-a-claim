---
name: debugging-with-evidence
description: "Diagnose unexpected behavior with a reproduction, competing explanations and experiments that separate them before fixing. Use for bugs, failed checks or repeated unsuccessful fixes; attribute branch failures only with suitable comparison evidence."
---

# Debugging with evidence

An observed failure establishes that something happened under particular
conditions. Find the mechanism that explains it before changing another thing.
Keep the investigation tied to the user's outcome and authorized file scope.

## Capture the failure

1. Record expected and observed behavior, exact command or user action,
   revision, dirty inputs, environment, relevant order or seed and evidence path.
2. Read the complete error and inspect the affected artifact and relevant diff.
   Missing paths, absent tools, empty test collection and permission errors
   may explain an unrunnable check; they do not establish successful behavior.
3. Reproduce with the smallest scope that still preserves the failure. Retain
   the original run: narrowing can remove order, shared state or boundary effects.
4. Register cleanup before an experiment that creates temporary resources.
   Use read-only inspection to answer state questions; do not reset or destroy
   the working tree to learn what was changed.

## Test explanations

Write a small set of plausible hypotheses based on the observation. For each,
name the predicted result and the observation that would contradict it. Choose
an experiment whose outcomes separate at least two explanations. Repeating the
same failed run without changing a discriminating condition adds little evidence.

Change one relevant condition where feasible and capture the actual outcome.
For an intermittent failure, retain repetitions and their conditions; one passing
retry is not proof of a fix. Instrument only what is needed and remove temporary
instrumentation when it no longer contributes to the delivered behavior.

When evaluating a detector or classifier, establish that a known-good case can
produce a negative result. A check that flags everything may be measuring itself.
Inspect differences in inputs, configuration and failure signatures before
assigning cause from test names, counts, labels or timing alone.

If branch versus baseline attribution matters, use `whose-red` at the location
the host actually exposes. If unavailable, compare identified trees with matched
commands, environment and failure signatures, using a clean control when feasible.
Report extra branch failures and unmatched conditions separately. A shared failure
on one baseline supports a limited historical finding, not innocence of the change.

## Fix the supported mechanism

When evidence supports a cause, make the smallest change that addresses its
class within the authorized scope. Inspect related call sites and affected inputs;
one repaired example may leave the same defect elsewhere. Where warranted, add
a regression check that would reject the old behavior for the observed reason.
Avoid tests that only repeat implementation values without an independent basis.

If a planned fix fails, compare its prediction with the new observation and
revise the hypothesis. Do not stack unrelated guesses. If experiments stop
distinguishing explanations, summarize what is known, seek a better observation
or name the concrete unavailable prerequisite. Continue independent work if useful.

## Verify the explanation and result

Rerun the reproduction and relevant regression scope, then the agreed acceptance
and broader checks on the candidate. Inspect the actual output and capture each
command's own exit code. Review the diff for scope and temporary artifacts.
Use discovered `reviewing-changes` when useful; self-review remains explicit.
After review fixes, run affected checks and review changed or unresolved findings.

Before reporting success, confirm evidence describes the final inputs and
rerun final acceptance yourself. State the supported cause, rejected alternatives,
changed files, observed checks and evidence paths. Keep unavailable comparisons,
remaining intermittent behavior and untested boundaries explicit.
