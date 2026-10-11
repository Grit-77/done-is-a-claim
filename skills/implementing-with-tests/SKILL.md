---
name: implementing-with-tests
description: "Implement runtime behavior changes and bug fixes with meaningful before-and-after checks, preserved behavior and relevant regression evidence. Use while editing code; prose-only changes do not need a failing test."
---

# Implementing with tests

Make the requested behavior observable, change only what it needs, and preserve
the surrounding contract. Follow the user's explicit workflow choices; if they
override test-first work, record the resulting evidence limits without blocking
authorized implementation or pretending a failing baseline was observed.

## Choose the behavior boundary

Read the request, current code, relevant callers and existing tests. Identify
the behavior to change, inputs and outputs that expose it, and behavior that must
remain valid. Respect the assigned files and existing production code.

Select a check that distinguishes the requested outcome from a plausible defect.
Prefer the real affected boundary when a helper test or mocked success would miss
it. Assertions should follow the contract, not repeat implementation constants.
Include meaningful edge inputs and relevant preservation checks proportionately.

An existing passing test may already cover a preservation requirement or an
already implemented outcome. Run and inspect it; add a check only for a real
coverage gap. Do not force a failure for behavior that should stay unchanged.
For a prose-only edit, inspect the text and scoped diff and use relevant document
checks. Do not invent a runtime test or artificial red to satisfy a ceremony.

## Observe a useful baseline

For new or corrected behavior, write or select the smallest meaningful check
before changing runtime code, then run it on the current implementation.
Read the actual failure and capture the command's own exit status and inputs.
Confirm it reaches the intended behavior and rejects it for the intended reason.

A missing import, fixture, tool, path or empty collection is a setup gap, not
evidence of the requested defect. Repair the setup within scope and rerun; do not
call an accidental red a baseline. If the check passes unexpectedly, inspect why:
the behavior may already exist, or the check may not distinguish the defect.
Do not weaken the requirement or deliberately break code to manufacture a red.

If execution or an authorized setup repair is unavailable, state which observation
is missing and why. Written tests and predicted failures cannot support a claim that red or green was observed.
Continue authorized work where useful, retaining required verification as a gap.

## Change, check and preserve

Make the smallest coherent implementation that satisfies the behavior. Do not
delete working production code or rewrite from scratch just to recreate test-first
history. Preserve unrelated edits and existing public behavior.

Run the behavior check and inspect the result, then run the whole relevant
regression suite, including affected callers and preservation cases. A single
green assertion cannot certify neighboring behavior; failed, skipped, unavailable
or empty required checks remain gaps. Investigate unexpected failures before
another speculative fix.

Refactor only when useful within scope. Rerun affected checks after the refactor;
an earlier green does not certify changed inputs. Repeat this loop for distinct
behaviors in proportion to their risk, rather than for every line or file.

## Return the evidence

Review the final diff against the request and preservation requirements. Report
changed files, tested revision and dirty inputs, commands, actual failure/pass
observations, exit statuses and evidence locations. Distinguish a demonstrated
before-and-after change from preservation-only checks or unexecuted tests.
Claim completion only to the extent current required checks support it.
