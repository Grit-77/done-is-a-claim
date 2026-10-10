# Diagnosis record

Template only. Record observations that separate explanations, not a chronology
of guesses. Keep full logs local and point to the relevant evidence.

```text
Outcome: <expected behavior and observed failure>
Inputs: <revision, dirty inputs, environment, relevant order or seed>
Reproduction: <exact command/action and working directory>
Observed: <actual output or artifact locator; producer exit status>
Evidence: <log/artifact location and observation time>

Hypotheses: <plausible causes with predicted and contradicting observations>
Experiment: <changed condition; explanations its outcomes distinguish>
Result: <actual observation and exit status; evidence locator>
Interpretation: <supported/rejected hypotheses and remaining uncertainty>
Control, if relevant: <identified baseline, matched conditions and signatures>
Limits: <unmatched conditions, unavailable checks, intermittent behavior>

Fix: <supported mechanism, affected call sites and owned files>
Verification: <reproduction, regression and broader checks; actual results>
Final inputs: <revision and dirty input identity after fixes and review>
Next action: <another separating experiment, authorized fix or concrete blocker>
```

A successful retry alone does not establish a cause or fix. Preserve the original
failure evidence and report what the comparison actually supports.
