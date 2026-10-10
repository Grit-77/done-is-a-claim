# Small evidence recipes

These are templates. Replace the acceptance command with your project's real
check; do not report these examples as executed verification.

For automatic local capture without a shell pipeline, see the
[receipt tool](RECEIPTS.md). The manual recipes below explain the same exit-code
distinction and remain useful in existing scripts.

## Capture the producer's exit, then read the log

Bash (works even when the surrounding script has `set -e`):

```bash
mkdir -p .local
if python path/to/your_check.py > .local/acceptance.log 2>&1; then
  check_status=0
else
  check_status=$?
fi
tail -n 40 .local/acceptance.log
printf 'Acceptance exit: %s\n' "$check_status"
exit "$check_status"
```

The `exit` is for an acceptance wrapper script; omit it when you only want to
inspect a result interactively. Read beyond the tail when the cause is earlier
in the log. Exit zero still needs the expected behavior and executed test count.

`set -o pipefail` is useful for detecting pipeline failure, but when more than
one command fails its result need not be the producer's code. Saving output first
keeps the report independent of the program used to display it.

PowerShell, for a native executable such as Python:

```powershell
New-Item -ItemType Directory -Force -Path .local | Out-Null
python path/to/your_check.py *> .local/acceptance.log
$checkStatus = $LASTEXITCODE
Get-Content -LiteralPath .local/acceptance.log -Tail 40
Write-Output "Acceptance exit: $checkStatus"
exit $checkStatus
```

Capture `$LASTEXITCODE` immediately after the native command; it is not the status
of a PowerShell cmdlet. An exception or a command that never launched is not an
executed check. As with Bash, use `exit` in a wrapper script, not when you intend
to keep an interactive session open.

## Name the work that was tested

```bash
git rev-parse HEAD
git status --short
git diff --stat
```

A commit plus a dirty-tree note still does not identify the dirty bytes. Keep a
diff or selected input fingerprints when those files affect the result. Include
untracked and generated inputs if the check consumes them. See
[evidence-freshness](../skills/evidence-freshness/SKILL.md) for the race and
environment limits of this approach.

## Separate a result from its delivery

Use distinct fields in a [receipt](../templates/completion-receipt.md):

- **Implemented:** the relevant diff or artifact exists.
- **Checked:** the stated command ran on identified inputs with a stated result.
- **Delivered:** the intended destination actually contains the result.

A local commit does not prove a remote deployment. A passing test on an unchanged
base does not prove that a worker implemented a requested feature. Keep the
decision tied to the [original acceptance brief](../templates/acceptance-brief.md).

## Reopen what was delivered

Name the inspected source and the intended destination before comparing them.
Read back that destination's actual artifact or revision. Keep these findings
separate: the send attempt, its matching acknowledgement, the destination bytes
or content, and the result of opening them in the intended consumer.

For a local example:

```bash
python examples/wrong_delivery.py
```

This synthetic exercise performs real copies in temporary directories. It shows
a stale same-named file copied successfully, a correct-copy control, and matching
bytes that fail JSON parsing. Parsing JSON only establishes syntax in this demo;
a real delivery may also need schema, rendering or application-specific checks.

For a service that transforms uploaded content, compare the relevant content and
revision instead of claiming byte equality. An acknowledgement for another
operation is not evidence for the intended one, and system acceptance does not
mean a human read a message. If read-back is unavailable, record that limit.
The [checking-delivery skill](../skills/checking-delivery/SKILL.md) and updated
[completion template](../templates/completion-receipt.md) give the full workflow.
