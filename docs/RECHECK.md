# Recheck a saved receipt

A receipt records an earlier execution. Before relying on it again, compare its
recorded evidence with the files and log you have now.

The optional [checker](../tools/check_receipt.py) is read-only and uses Python
3.10+ with the standard library. It does not execute the command inside a receipt,
rewrite evidence, or decide whether the user's task is complete.

## Capture, then compare

Capture a command with at least one selected input:

```bash
python tools/receipt.py --input examples/false_green.py -- python examples/false_green.py
```

Copy the exact `receipt.json` path printed by the capture tool. Replace
`path/to/receipt.json` below with that path; `--project` explicitly selects the
current project to compare:

```bash
python tools/check_receipt.py path/to/receipt.json --project .
python tools/check_receipt.py path/to/receipt.json --project . --json
```

The synthetic demo's command succeeds when it exposes the intended false-green
trap. A matching receipt does not turn the inner failing verifier into a pass.

## What is compared

- **Log bytes:** the sibling `command.log` against `log_sha256` recorded by the
  capture tool after closing the log.
- **Selected current files:** their bytes against the receipt's `inputs_after`
  SHA-256 values, resolved under the explicitly chosen project.
- **Git HEAD:** the current commit against the recorded post-run HEAD when one
  was recorded. Absent recorded Git is explicitly outside this comparison scope.
- **Historical outcome:** reported separately. Consistent bytes do not upgrade
  a failed command, a check that changed its inputs, or an incomplete observation.

Historical absolute paths are context only. The checker does not use the saved
`command.cwd`, `resolved_path` or Git root to choose what to open. Relative input
names support Windows separators, but absolute names, traversal, aliases and
paths escaping the selected project are refused. Logs must be the regular sibling
`command.log`, not an arbitrary path embedded in JSON.

## Outcomes and exits

| State | Exit | Meaning |
|---|---:|---|
| `matches` | 0 | The available declared comparisons match and the recorded command succeeded without recorded input changes or lost observations. |
| `different` | 1 | Current file, log or recorded-HEAD evidence differs, including missing bytes. |
| `invalid` | 2 | The receipt or supplied paths fail the supported-format checks. |
| `recorded_failure` | 3 | Comparisons may match, but the historical execution is not a successful stable-input result. |
| `incomplete` | 4 | A required comparison cannot be established. |

When several conditions apply, the report retains component details and gives
priority to invalid, different, incomplete, then recorded failure. Always read the
recorded command outcome as well as the comparison state.

Receipts from v1.1.0 without `log_sha256` remain readable, but their log binding is
incomplete. Receipts with no selected inputs also remain incomplete for freshness
checking. Do not add a new hash to an old receipt and pretend it was observed
during the original run; capture fresh evidence when the task requires it.

## A match is a scoped observation

The JSON and log are ordinary editable files. Someone can change both to agree.
This tool detects inconsistency against the saved record; it does not establish
authorship, authenticity, signed provenance or that the recorded command really
ran. It is not an in-toto or SLSA verifier.

Selected hashes exclude undeclared inputs and dependencies. Endpoint hashes can
miss a change that was later restored, and the read/compare operation is not an
atomic filesystem snapshot. Git HEAD equality does not establish equality of
unselected dirty files or the environment. Re-run checks affected by a meaningful
change instead of treating this comparison as a permanent approval.
