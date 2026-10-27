# Bring a receipt to your next PR

**English** · [Türkçe](REPORTS.tr.md)

Run your project's real check, then turn its local receipt into a Markdown
summary or minimal JSON projection. No plugin or provider account is required for these optional tools;
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

The reporter prints Markdown to your terminal by default. Review it, then copy it into a
PR description or comment alongside your acceptance condition and any checks
you did not run. It does not publish anything or rerun the recorded command.
Raw receipts and logs should remain local; add `.local/` to your project's
ignore rules if it is not already ignored.

## Optional JSON for CI consumers

For a machine-readable public summary, use the same receipt and project with
`--format json`:

```bash
python tools/report_receipt.py ../my-project/.local/receipts/run-EXAMPLE/receipt.json --project ../my-project --format json
```

This is a separate **public-summary v1** projection, not the raw receipt or
the local rechecker's diagnostic JSON. It has exactly these six fields:

```json
{
  "schema_version": 1,
  "historical_command_status": "command_succeeded",
  "historical_child_exit": 0,
  "recheck_state": "different",
  "freshness": "changed",
  "reason_code": "observations_differ"
}
```

The example represents a recorded zero followed by changed selected bytes; it
does not turn the historical command result into a current success claim.
`historical_command_status` is `command_succeeded`, `command_failed`, `not_run`
or `null`. A recorded `not_run` remains distinct from an unavailable historical
result. The child exit is an integer or `null`; the existing Markdown portable
range, `-2147483648` through `4294967295`, is retained. Larger or smaller values
are withheld as `null` without changing the recheck state or reporter exit.
For an overall `invalid` report, both historical fields are `null`.

`freshness` is `changed` for `different`, `unverifiable` for `invalid` or
`incomplete`, and `matches` otherwise. Matching observations can still retain a
recorded failure. These values describe only the selected observation scope.

| Recheck state | Fixed `reason_code` |
| --- | --- |
| `matches` | `observations_match` |
| `different` | `selected_input_missing` if a previously captured selected input is missing; otherwise `observations_differ` |
| `invalid` | `invalid_evidence_or_context` |
| `recorded_failure` | `historical_failure`, including a recorded capture failure or input/HEAD mutation |
| `incomplete` | `observation_unavailable` if a structured component is unavailable; otherwise `evidence_incomplete` |

The existing overall state and exit precedence still applies before choosing a
reason. One reason describes the dominant condition, not every observation.
Reason codes never contain filenames or exception text.

JSON omits arguments, log contents, paths, filenames, hashes, HEADs, timestamps,
counts and freeform diagnostics. It cannot be combined with `--include-command`;
that combination is a private CLI error with exit `2` and no summary. Other CLI
parsing errors can also have empty stdout. Invalid evidence or context produces
the six-field `invalid` summary instead. Do not substitute
`tools/check_receipt.py --json`: that local diagnostic format can disclose paths.

Keep the reporter's own nonzero exit visible when parsing or publishing JSON;
a downstream parser succeeding does not replace it. Markdown remains the
default, including its deliberate `--include-command` option. Neither format
reruns the recorded command or authenticates an asserted historical result.

Schema and test-plan design input:
[sacravenger / NaN Mesh](https://github.com/Grit-77/done-is-a-claim/issues/14#issuecomment-6389322903).

### Consumer example: preserve the reporter exit

The standard-library [consumer example](../examples/consume_report.py) runs the
local reporter once, saves its return code before parsing JSON, and prints the
parsed summary:

```bash
python examples/consume_report.py ../my-project/.local/receipts/run-EXAMPLE/receipt.json --project ../my-project
```

With successful parsing and output, its exit is the reporter's own `0`–`4`,
never `historical_child_exit` or the parser's success. A historical zero followed
by changed selected bytes still yields `different` / `changed` and exit `1`.
The [synthetic regression](../tests/test_consume_report.py) contrasts this with
an unsafe consumer that parses and prints the same summary but exits `0`.
This is a consumer failure mode, not a reporter defect; see the
[scoped contribution request](https://github.com/Grit-77/done-is-a-claim/issues/14#issuecomment-6400428209).

Startup, 120-second reporter timeout, parse and output errors produce a fixed
diagnostic. Consumer errors retain an available nonzero reporter code; otherwise
they return `5` (including consumer CLI errors). Raw reporter stderr is withheld.
Only successfully parsed JSON is printed; an output failure can leave partial
stdout. The example parses the trusted local reporter's output; it is not an
independent schema validator, publisher, service integration or security sandbox.
It does not rerun recorded argv, authenticate history or decide task completion.
If you pipe the example into another process, preserve the example's own exit
too; a successful downstream process can mask it again.


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
