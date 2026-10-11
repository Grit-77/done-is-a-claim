# Use it during ordinary development

Start with `using-done-is-a-claim` through your host's skill picker, or invoke a
specific installed skill below. The workflow follows the task's size: a text fix
can stay a direct edit; a behavior change needs a check that reaches that behavior.
These are example requests, not measured agent outcomes.

## Add a feature without guessing the product

> Make exporting this report easier. Use the existing screen and project
> conventions. Find what the user needs to export, preserve current filters and
> explain any consequential assumption before implementing the smallest useful
> change. Continue within my existing authorization.

The entry and planning skills inspect current behavior and known decisions
before asking questions. They distinguish actual requirements from reversible
assumptions and decisions that would change the product. A missing consequential
answer blocks only its dependent work, not all investigation. They do not require
a new design document or approval stage for every task.

## Change behavior with a check that can catch the mistake

> Use implementing-with-tests to fix this bug. Establish a test of the user's
> failing behavior, show why it fails on the current implementation, make the
> smallest correction and rerun relevant checks. Preserve unrelated behavior.

The [skill](../skills/implementing-with-tests/SKILL.md) connects acceptance to the
implementation loop. A missing dependency, broken test import or empty collection
is not the intended failing baseline. Existing passing preservation tests stay
green; documentation-only edits need suitable inspection, not an artificial test
failure. If the environment cannot run a check, the agent must keep that gap visible.

The useful result is the changed behavior, actual before/after observations and
relevant regression result. A written test that never ran cannot establish this.

## Resolve review comments without blindly accepting them

> Use responding-to-review for these comments against the current revision.
> Check each claim against our requirements and code. Fix supported defects,
> explain stale or incorrect suggestions with evidence, and identify decisions
> that genuinely need my input. Prepare responses here; do not post them.

The [skill](../skills/responding-to-review/SKILL.md) separates supported findings,
stale observations, disputed suggestions and missing decisions. It can fix an
independent valid bug while a larger product question remains open. A reviewer
or bot repeating a comment does not make it correct. Resolving code and posting
a reply are separate actions governed by the user's existing authorization.

For example, a reviewer may find an actual dropped zero-value row while also
suggesting alphabetical sorting that conflicts with the required first-seen
order. Keep the valid fix and verify the ordering contract; do not trade one
regression for another to mark both comments addressed.

[Try this review in a separate practice project](../examples/review-feedback/README.md).
It includes actual code, a contract, review comments and three narrow passing tests.
The fixture has a deliberate defect; inspect the agent's changes and evidence.

## Keep the task when the conversation changes

For long work, the existing execution/resume skills preserve the objective,
newer steering, decisions, relevant evidence and unfinished next action in the
project's usual record. “What's the status?” should produce an answer and then
continued work, not silently replace the task. An explicit cancellation or an
incompatible new request does change the objective.

An unsuccessful attempt needs its observed result and a condition for retry.
Reopening a context window is not new evidence that the same failed approach
will now work. Keep the note compact; routine uninterrupted edits need no ledger.

## Install and verify what you have

The native plugin includes all 15 skills. Existing project copies can use the
`workflow` profile for the full route or `review` for reviewing and receiving
feedback. The `evidence` profile remains focused on interpreting observations.
[Installation and conservative updates](INSTALL.md) · [Native plugin updates](PLUGINS.md)

Skill discovery, actual loading and a correct task result are separate observations.
The instructions do not enforce tool behavior or imply that every ordinary prompt
automatically loaded them. [Native session checks](NATIVE-TESTS.md) and
[synthetic decision cases](../evals/README.md) help inspect those boundaries.
