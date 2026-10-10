# Done is a claim

Rules for coding agents. Each one exists because breaking it cost us a real failure; the story behind each is in INCIDENTS.md.

## Before you start

1. **Write the acceptance command before the work.** Name the observable outcome it checks. Never weaken it to make it pass; if the command is wrong, explain and record a correction that preserves the intended outcome before relying on it.
2. **Check that every path you were given exists.** Resolve missing inputs before relying on them. An explicitly requested new file is different: verify its intended parent and scope.

## Before you say "done"

3. **Re-run the acceptance yourself, on the current work, and quote its output.** Name the revision and any uncommitted inputs. A check that changes those inputs does not certify the resulting tree.
4. **Run the whole relevant suite, not only your test.** Your test passing says nothing about the tests next to it. If a required check cannot run, name the gap instead of claiming full verification.
5. **Record the command's own exit code.** In `cmd | tail; echo $?` the `$?` belongs to `tail`. Capture the producer's status before reading its saved output, or use the shell's per-command pipeline statuses. `pipefail` detects a failing pipeline but is not necessarily the producer's own code.
6. **"No tests ran" is a failure.** An exit code of 4 or 5 from pytest, an empty collection or a skipped suite is not a pass.
7. **Unknown is not pass.** If a check could not run, report it as not run, with the reason.
8. **Green means every required check.** Read every required CI job on the revision, not the one you picked; report skipped or unavailable checks explicitly.

## When you report

9. **Read the artefact, not the summary.** A `status: ok` file, a log that says "Saved" or a falling counter describes something narrower than your claim. Open the diff, the file, the frame.
10. **A file that exists is not a file that works.** Decode the image, load the page, run the binary.
11. **Look at it yourself.** A 200 response is not a working page; open it and look.
12. **Verify every citation.** Check repository citations with `git cat-file -e <sha>` and `git cat-file -e <ref>:<path>`; open external sources and verify that they support the claim. Identify private or historical sources and their access limits.
13. **State the base, and re-check it before you publish.** "Tested on abc123" stays true; "abc123 is current main" expires.

## When you write tests and fixes

14. **A test that repeats a constant proves nothing.** If the code says `MIN = 3.51` and the test checks 3.51, ask where 3.51 came from.
15. **Fix the class, not the instance.** Find every call site of the defect before you call it fixed, and test more than the one you changed.
16. **Run a detector on a known-good case first.** A check that flags 100% of its inputs is measuring itself.
17. **Register cleanup before the work it cleans up.** Cleanup placed after the work never runs on the path that fails.

## Never

18. **Never run a destructive command to answer a question.** `git status` and `git diff` answer "does this match main"; `git reset --hard` destroys the answer.
