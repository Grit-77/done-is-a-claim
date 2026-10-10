# Review record

Template only. Inspect the candidate and preserve evidence through fixes and
rereview. Do not label self-review as independent review.

```text
Outcome / acceptance: <user contract and exact checks>
Candidate: <checkout, base, revision and dirty inputs>
Scope / mode: <files and boundaries inspected; independent or self-review>
Evidence read: <actual diff, artifacts and check output locations>

Finding <id>: <impact, file locator and violated outcome>
  Evidence: <reproduction or observation and locator; uncertainty if any>
  Correction: <concrete direction within scope>
  Resolution: <fix and evidence, unresolved or owner decision>
  Affected checks: <commands, own exit statuses and actual results>
  Rereview: <changed parts and remaining findings; observation and locator>

Final inputs: <revision and dirty inputs actually checked>
Final acceptance: <exact command, own exit status, actual output, evidence path>
Broader checks / CI: <all required outcomes on identified inputs>
Not checked / limits: <gaps and their effect on the verdict>
Verdict: <what evidence supports; remaining findings or blockers>
```

A clean review is scoped evidence, not proof of every property. Run final
acceptance on the resulting inputs after review fixes; earlier checks remain
observations about their earlier inputs.
