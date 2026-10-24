# Fixed-contract delivery fixture

A small Python 3.10+ standard-library fixture for the
[agreed shared testing contract](https://github.com/openai/codex/issues/36718#issuecomment-6388910622).
All data and operations are synthetic local files. No model, provider, agent or
Truth Firewall controller is invoked.

From the repository root, choose a new output directory whose parent exists:

```sh
python examples/fixed_delivery.py --output fixed-delivery-run
```

For ignored artifacts, use a new child of an existing `.local` directory instead.
The command refuses an existing output file,
directory or symlink without overwriting it. It prints the JSON report and keeps
the workspace for inspection; choose another new directory for another run.
Remove only your own synthetic workspace when finished. A failed run can leave
partial artifacts for diagnosis and must not be presented as a completed suite.

## One main task, three attempts

`task-spec.json` declares one approved valid artifact, its SHA-256, one destination
and the required checks. Its exact bytes are frozen before copying. The three
attempts all use that same approval and `delivered/artifact.json` in the same
workspace. The approved digest is not recalculated from the mutable copy source
or the resulting destination.

| Main attempt | Approved digest matches | JSON parses | Local acceptance |
| --- | --- | --- | --- |
| Correct approved artifact | true | true | accept |
| Stale valid JSON, same basename | false | true | reject |
| Invalid JSON | false | false | reject |

`format-control-spec.json` is a **separate pre-frozen control** approving the
invalid bytes at `format-control/artifact.json`. Its digest matches but JSON
parsing fails, so local acceptance is false. It never replaces the main task's
approval, destination or criteria.

The workspace contains both unchanged specs, the three synthetic inputs,
delivery files and `observations.json`. Repeated main attempts intentionally
overwrite the one declared main destination; the final file is the rejected
invalid attempt. The report retains each earlier observation.

## Reading the report

`main` and `format_control` identify their frozen spec digest, approved artifact
digest and relative destination. Main `attempts` and the control `observation`
record copy completion, destination existence and digest, digest match, JSON
parse result, local `accepted` and bounded error-class labels. Copy completion
means `shutil.copyfile` returned, not that a child process exited or delivery was
accepted. Missing, non-regular or unreadable artifacts remain failed observations; symbolic
links along the checked workspace/destination path are refused.
Parsing checks JSON syntax, not a business schema; non-finite constants are
rejected. No raw artifact contents or absolute machine paths are reported.

`suite_exercised_as_expected` and runner exit **0** mean the prescribed contrasts
were exercised. Two main deliveries and the format control still fail acceptance.
Exit 1 means observations differed; exit 2 reports setup/input failure. Neither a
green fixture exit nor `controller_evaluated: false` establishes a controller's
decision or a native agent's behavior.

For a later external harness, import `freeze_contract` before the operation and
hold that snapshot. Call `observe_destination` against the declared workspace
afterward; it reads the actual destination, without consulting the copy source.
Omit `copy_completed` when no independent operation observation is available.
Transport/controller integration and its isolation need their own checks. This
trusted local example is not a sandbox, signed attestation or atomic readback.

The original [wrong-delivery demo](../wrong_delivery.py) remains unchanged. Its
matching-invalid illustration has a different approval from its valid baseline;
this fixture makes that distinction an explicit separate contract.
