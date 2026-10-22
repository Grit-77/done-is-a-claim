# Bring a receipt to your next PR

**English** · [Türkçe](REPORTS.tr.md)

Run your project's real check, then turn its local receipt into a Markdown
summary. No plugin or provider account is required for these optional tools;
you need Python 3.10+ and a clone of this toolkit. Installing the skills alone
does not put the Python tools in your project.

## Use your existing project

Keep the toolkit clone and your project separate. From the toolkit's root,
replace `../my-project` with your existing project path. This example assumes
that project already has `app.py` and `test_app.py`; choose your actual source,
test files and check command instead:

```bash
python tools/receipt.py --cwd ../my-project --input app.py --input test_app.py -- python -m unittest test_app
```

The command runs **inside your project**. The tool prints the exact path to a
new `receipt.json`; the adjacent `command.log` contains the full command output.
Read that output and compare it with your task's acceptance conditions.
Repeat `--input` to select more existing files. Unselected files, dependencies
and the environment are outside the file comparison.

Use the printed receipt path in the next command. Replace `run-EXAMPLE` below
with the actual directory, keeping the same project root:

```bash
python tools/report_receipt.py ../my-project/.local/receipts/run-EXAMPLE/receipt.json --project ../my-project
```

The reporter prints Markdown to your terminal. Review it, then copy it into a
PR description or comment alongside your acceptance condition and any checks
you did not run. It does not publish anything or rerun the recorded command.
Raw receipts and logs should remain local; add `.local/` to your project's
ignore rules if it is not already ignored.

## Read the two results separately

The report has a **historical child exit** and a **recheck state**. A command
that returned `7` remains a recorded failure even if all its selected bytes
still match. A command that returned `0` can have stale evidence after an edit.

| Reporter exit | Recheck state | What it means |
| --- | --- | --- |
| 0 | `matches` | Selected observations match, with no recorded command failure or mutation. This does not establish that tests ran or the task is complete. |
| 1 | `different` | A selected file or log differs or is missing, or Git HEAD differs. |
| 2 | `invalid` | Metadata or a required local observation is invalid/unavailable. Use the local rechecker for details. |
| 3 | `recorded_failure` | Matching current observations retain a historical command failure, failure to run, or input/HEAD mutation. |
| 4 | `incomplete` | Evidence lacks required scope or observations, such as selected files or a bound log hash. |

These are **reporter** exits, not the captured child's exit code. Differences
take precedence over incomplete evidence, which takes precedence over a
recorded failure; the historical result remains visible in every valid report.
Keep a nonzero reporter result visible in automation even though it printed
Markdown successfully. [Full recheck semantics](RECHECK.md).

The table includes selected input counts, log hashes, optional Git HEADs and
validated timestamps. It deliberately omits filenames and freeform error text.
To investigate locally, use:

```bash
python tools/check_receipt.py ../my-project/.local/receipts/run-EXAMPLE/receipt.json --project ../my-project --json
```

That diagnostic output can contain local paths and filenames. Review it before
sharing it.

## Share only what you intend

Default Markdown omits command arguments, log contents, local paths, filenames
and freeform diagnostics. It still discloses timestamps, status/counts, log
hashes and optional Git commit hashes. It is not a secret scanner or a promise
that every observation is suitable for publication.

If you deliberately want to include the recorded arguments, add
`--include-command`. Arguments may contain secrets. They are displayed as an
escaped, bounded array, **not a shell command to copy and execute**. Review the
result before sharing; raw logs are never included.

Receipts are editable local files, not signed attestations. Matching hashes
establish consistency with the supplied receipt, not its authenticity. Checks
are non-atomic and limited to the selected files, adjacent log and optional
Git HEAD. The report cannot decide whether your acceptance criteria were good
enough or whether the user's intended outcome was achieved.

## Ask your agent

> Run the acceptance check for this change through the receipt tool. Select the
> relevant source and test files, inspect the actual output, and generate the
> default Markdown report. Explain what the check established and what remains
> unverified. Keep raw receipts local and show me the summary before sharing.

If this helped catch a misleading result—or was confusing—[submit a use
report](https://github.com/Grit-77/done-is-a-claim/issues/new?template=use-report.yml)
with the version, task boundary, observed result and limitations. Remove private
information first.
