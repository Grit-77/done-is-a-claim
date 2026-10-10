# Capture a command, not a promise

The optional [receipt tool](../tools/receipt.py) runs a command directly, saves its
full merged output, and records the command's own exit code. It also records Git
state when available and fingerprints the input files you explicitly select.
New receipts bind the closed log's bytes with an additive `log_sha256` field.

Requires Python 3.10+. It uses the standard library; Git metadata is optional.
There is no provider account, upload, background process or network integration.

## First receipt

From this repository's root:

```bash
python tools/receipt.py -- python tools/run_tests.py
```

The tool prints the location of a new run directory under `.local/receipts/`.
Open its `receipt.json` and `command.log`. Each run gets its own directory, so a
later run does not replace an earlier receipt.

This command captures execution and Git state, but selects no file fingerprints.
Its receipt says `no_inputs_selected`. Choose the actual inputs of your own task
when you need that narrower before/after comparison.

## Bind selected files

For example, to fingerprint the synthetic demo source while executing it:

```bash
python tools/receipt.py --input examples/false_green.py -- python examples/false_green.py
```

The demo's exit zero means it demonstrated the intended mismatch; it does not mean
its deliberately failing inner verifier passed. The receipt preserves this
distinction by recording execution instead of guessing at the task's verdict.

Repeat `--input` for each existing file you want compared. Files must be inside
the selected working directory. These are selected-file fingerprints, not a
snapshot of every dependency or of the entire repository.

Use `--cwd` to run inside another existing project and `--output-dir` to choose
where the new run directory is created. Relative input paths are resolved against
that working directory. The tool does not edit the selected input files; the
command you launch may do so.

## Read the outcome

| Receipt status | Meaning |
|---|---|
| `command_succeeded` | The launched command returned zero, no selected-input or recorded HEAD change was detected, and no previously available Git observation was lost. This is not a test-pass or task-complete verdict. |
| `command_failed` | The launched command returned nonzero. Read its actual exit code and output. |
| `inputs_changed` | The command returned zero, but a selected input or the recorded Git HEAD changed. A failing child keeps `command_failed`, with any detected changes recorded separately. |
| `evidence_incomplete` | The command returned zero, but Git state that was available before the run could not be observed afterward. Stability is unknown. |
| `not_run` | The command could not be launched or its prerequisites were rejected. |

`command.exit_code` belongs to the child. `wrapper_exit_code` belongs to the
receipt tool. A successful child with changed inputs produces wrapper exit **3**.
A successful child with a lost Git observation produces wrapper exit **4**;
`evidence_incomplete` also remains visible when a failing child's exit is retained.
`head_changed: null` means the comparison was unavailable, not unchanged. Commands
outside a Git repository can still run normally; Git is optional.
A portable nonzero child status is retained; inspect the JSON for exact handling
of signals or platform-specific codes. A failure to write evidence is a failure
of the receipt tool, even if the child succeeded.

## Reuse a receipt carefully

Use [the receipt rechecker](RECHECK.md) before relying on saved evidence after a
handoff or edit. It compares the log, selected files and recorded HEAD against an
explicit current project, without rerunning the command. Old unbound logs and
receipts with no selected files remain incomplete for freshness checking.

## Inspect a known failure

This intentional failure runs on Windows, macOS and Linux:

```bash
python tools/receipt.py -- python -c "import sys; print('intentional failure'); sys.exit(7)"
```

Expect a nonzero wrapper result and a receipt containing the child's actual **7**.
That is the expected outcome of this exercise, not a failing installation.

## What a receipt does not establish

- Exit zero does not tell you whether tests were collected, required checks ran,
  or the user's acceptance condition was met. Read the log and the task brief.
- If you explicitly launch a shell pipeline, the tool sees that shell's result;
  it cannot reconstruct an inner producer's lost status. Pass the check directly.
- On Windows, direct `.bat`/`.cmd` commands are refused, including PATH-resolved
  batch files: Windows can interpret their arguments through a shell even when
  Python requests direct execution. Use a native executable. Explicitly invoked
  shells remain responsible for their own quoting and exit-code semantics.
- Matching endpoint hashes can miss a file changed and restored during the run.
  Dependencies, environment and undeclared inputs may also change.
- Receipts are ordinary editable local files, not signed attestations or an
  immutable execution environment. Git state and file snapshots are observations,
  not atomic locks.
- There is no timeout or descendant-process supervision. Use the project's
  process controls for long-running or untrusted commands.

Logs can contain whatever the command prints. Keep raw receipts local and review
them before sharing. This repository ignores `.local/`; another project may need
its own ignore rule. A shareable summary can use the
[completion receipt template](../templates/completion-receipt.md).
