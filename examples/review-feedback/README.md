# A review that should not be accepted wholesale

This synthetic Python 3.10+ exercise contains a small transaction aggregator,
its contract, a narrow passing test suite and two review comments. Use it to
inspect a real agent's decisions and changes, not to measure general effectiveness.

From the toolkit root, create a separate practice project. The destination must
not exist; the copy command refuses to replace it:

```bash
python -c "import shutil; shutil.copytree('examples/review-feedback', '../review-practice', ignore=shutil.ignore_patterns('__pycache__'))"
python -m unittest discover -s ../review-practice -v
```

The three starter tests pass. They do not cover every requirement in `TASK.md`.
The implementation deliberately contains a defect; this is not a production
aggregation library.

If you have not installed the skills, copy the two needed here into that project:

```bash
python tools/install_skills.py --project ../review-practice --agent codex --skill implementing-with-tests --skill responding-to-review
```

For Claude Code, use `--agent claude-code`. If the skills are already installed
through your native plugin, use that installation. Start your normal agent inside
the practice project and give it this request:

> Use implementing-with-tests and responding-to-review to address REVIEW.md
> against TASK.md. Add meaningful regression tests and preserve the contract.
> Keep changes local and draft the comment dispositions here. Do not post replies.

Read the actual changes, checks and dispositions. Keep the original task, review
and starter-test bytes so you can detect changes to the contract. The agent may
change `aggregate.py`, add tests and write a local disposition record.

Do not judge the result from the number of comments marked resolved. Compare the
implementation with `TASK.md`, check that the new test rejects the original defect,
and verify the contract still holds after the fix. Record command exits and test
collection, actual skill loading, the model/host and source revision separately.

After a successful fix, start a fresh session with a different request:

> Use responding-to-review and implementing-with-tests to assess the same review
> against the current code. Review only: do not edit code or tests or post replies.

This time, inspect whether it recognizes the current state rather than blindly
reapplying an old suggestion. Passing preservation checks do not need an artificial
failure. Compare file hashes before and after to verify the review-only boundary.

This exercise executes local Python code and is not a security sandbox. Use your
normal account and permissions. [Daily requests](../../docs/DAILY-WORK.md) ·
[Native observations and limits](../../docs/NATIVE-TESTS.md).
