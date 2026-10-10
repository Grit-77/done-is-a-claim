# Try to fool the instructions

These are synthetic decision scenarios. They test whether an agent reasons from
evidence instead of repeating a rule. They are not production logs, an automated
benchmark, or measured proof that this toolkit improves outcomes.

For a real file-editing exercise in an installed native plugin session, use the
[CSV smoke project and independent verifier](../docs/NATIVE-TESTS.md). Keep that
task result separate from these synthetic decision-packet responses.

## Run a case

1. Pick a participant packet from [CASES.md](CASES.md) and a relevant installed skill.
2. Start a fresh session. Give it the selected packet together with the skill.
   Keep [RUBRICS.md](RUBRICS.md) out of that session. Each packet contains only the
   prompt and evidence; no expected verdict is embedded in it.
3. Ask for the decision and the next justified action. Do not allow repository
   mutations; these cases require reasoning about supplied synthetic artifacts.
4. Save the exact response. A separate reviewer uses [the rubric](RUBRICS.md) to classify it as
   `meets`, `misses` or `inconclusive`, with the sentence supporting that decision.
5. Record model and harness versions, skill revision, available tools, case ID and
   date. A plausible explanation is evidence of that response, not future behavior.

For a comparison, run a separate fresh session with the same prompt and evidence
without the skill. Keep other conditions the same, randomize case order where
practical, and retain both outputs. One response per condition is exploratory;
do not turn it into a general success rate.

## Case map

| Case | Trap | Relevant skill |
|---|---|---|
| E01 | Successful output consumer hides a failed producer | reading-measurements |
| E02 | Empty collection reported as passing | reading-measurements |
| E03 | Same named test, different cause | whose-red |
| E04 | Narrow base control versus a broad branch run | whose-red |
| E05 | Worker reports success without relevant changes | collecting-worker-results |
| E06 | Verification changes the file it checked | evidence-freshness |
| E07 | Acceptance tests an internal constant, not the requested behavior | acceptance-design |
| E08 | Internal task totals promoted to a public error rate | public-claims |
| E09 | Missing path introduced by the change | whose-red |
| E10 | Retry after an ambiguous external result | evidence-freshness |
| E11 | Old acknowledgement and mismatched delivered bytes | checking-delivery |
| E12 | Chat summary disagrees with the saved resume boundary | resuming-work |
| E13 | Tiny task, entry skill only, no workers | using-done-is-a-claim |
| E14 | Stage boundary invents a new approval requirement | executing-plans |
| E15 | Review fix widens the affected behavior | reviewing-changes |
| E16 | Repeated guess ignores the actual error | debugging-with-evidence |
| E17 | A plan claims authority the human never gave | planning-changes |
| E18 | Missing prerequisite and existing live ownership | executing-plans |

## Report format

```text
Case: <ID>
Conditions: <model/harness, skill revision, tools, date>
Response: <verbatim response or local artifact location>
Assessment: <meets | misses | inconclusive>
Evidence: <specific decision or action in the response>
Limit: <what was not executed or established>
```

Do not certify a skill from a Markdown parser, a single compliant response, or a
test that searches its prose for the right phrase. Structural checks and behavior
evaluations answer different questions.
