# Completion receipt

Template only. Replace the fields with observed evidence; do not invent terminal output.
Keep private logs local and share only the evidence the recipient is allowed to see.

```text
Outcome: <complete | partial | blocked>
Scope: <what changed and what the user can now do>
Revision: <commit; branch; clean or dirty>
Inputs: <uncommitted diff or artifact hashes when HEAD alone is insufficient>

Acceptance: <exact command and working directory>
Observed: <actual relevant output, including collection/result counts>
Exit: <the tested command's own status>
Evidence: <log or artifact location; observation time>

Broader checks: <commands and outcomes>
Not checked: <omissions and reasons; say none only if true>
Limits: <what these checks do not establish>
Delivery, if relevant:
  Inspected source: <artifact and revision or byte identity>
  Destination: <actual delivered artifact and observed revision>
  Attempt / acknowledgement: <operation and matching receipt; or unverified>
  Publication: <destination observation; or not checked with reason>
  Read-back: <comparison with source; evidence and time; or unverified>
  Consumer check: <decode, parse or rendered result; evidence; or not checked>
Next step: <remaining work or none>
```

A passing targeted test supports that test's claim. It does not silently establish
that the full suite, rendered interface, deployment or another machine works.
Re-run checks affected by a later edit; keep earlier observations attached to their
original inputs. There is no need to repeat unrelated checks just to refresh a date.

An acknowledgement establishes only what the matching operation's receipt says;
it does not establish human reading. Source inspection, destination byte equality
and a successful consumer check support different claims. If the destination
cannot be inspected, keep delivery unverified. Omit delivery fields for a local
draft or edit with no delivery claim; this template grants no publishing rights.
