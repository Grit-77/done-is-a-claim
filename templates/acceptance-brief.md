# Acceptance brief

Use before a bounded task. Keep the user's actual outcome visible; an easy test is
not a substitute for it. This is a template, not an executed task.

```text
Outcome: <observable user-facing result>
In scope: <files or responsibility>
Constraints: <compatibility, permissions, preserved behavior>
Acceptance: <command, working directory, expected observable behavior>
Broader checks: <relevant suite/build/manual check>
Known limitations: <what automation cannot establish>
Evidence to return: <diff/artifacts, revision, real outputs, omissions>
```

Check that the paths exist. For a new file, verify its intended parent and role.
If the acceptance command is wrong, report the mismatch and propose a correction
that still tests the original outcome. Record why it changed; never weaken it just
to turn a failure green.
