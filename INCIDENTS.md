# Incidents

The author's failure accounts behind the original rules in AGENTS.md, from
September 2026 while running Claude Code and Codex agents on Grit's own repository.
Numbers are reported from the internal records, not independently reproduced by
this public repository. See [CLAIMS.md](CLAIMS.md) for the source mapping and limits.
Rule wording may be refined without rewriting the historical account.

## The numbers that started it

Between 14 and 29 September 2026 a server re-ran the acceptance command of 3,489 agent tasks, each on its own. 2,282 passed on that first independent re-run. The others failed or could not run; part of that is environment, so we do not call them all defects.

Separately, 736 tasks passed their own acceptance and still turned the full test suite red on main. (Rules 3, 4.)

## 1–2. Acceptance first, paths that exist

In one night 66 tasks were opened and 48 had no scope. Each brief said `IN SCOPE: -, nothing else`. Twenty-one workers ran one attempt each and returned zero lines of code, quoting their brief back: the scope authorised no file. Two tasks also named test directories that did not exist on main, and their workers reported `file or directory not found`.

## 3–4. Your test is not the suite

A task's own acceptance passed: 12 passed. The tests beside it gave 5 failed, against 741 passed and 0 failed on a clean copy of main. The commit caused them.

## 5. The pipe's exit code

Three times in one day `cmd | tail` was recorded as exit 0:
- a site check reported green was exit 1, with three lint errors;
- a test run logged `exit: 0` had died on `unrecognized arguments` and executed no tests;
- the same pipe hid a dev server's failure behind buffered output.

## 6. No tests ran

pytest exits 4 for a path that does not exist and 5 for a directory with no tests. Both are failures. Our pipeline discarded the code and recorded a verification anyway, and those tasks moved on as verified. Two sessions had also told each other for an hour that the exit code was 0; nobody ran the two-second check.

## 7. Unknown is not pass

The same class as rule 6: a tool that could not run was read as a verdict. "Not run, because X" is the only honest state.

## 8. Green means every check

A release was reported green on Windows and Ubuntu because the job we chose, an install smoke test, passed. The repository's own CI workflow had failed on every push since that evening: it ran `pytest tests`, the exported repository shipped no `tests/` and pytest exited 5.

## 9. The artefact, not the summary

One night produced three wrong reports, all the same shape:
- "the collector processes a row every ninety seconds", from a falling counter; the collector's own line said `80 -> 65 (1 reconciled)`, one row;
- "four green results", from `status: ok, verify.passed: true, commits: 1`; two of those commits changed only the worker's own report file;
- "verified", from the task's own 12 passing tests (see rule 3).

## 10. A file that exists is not a file that works

A render logged `Saved:` for every frame. Eleven frames were 0 bytes and 46 more were cut off, because the disk filled during the run. A share copy had already been encoded from them before a full decode caught it.

## 11. Look at it yourself

A terminal dashboard was reported finished with sixty rendered frames and an HTML contact sheet. Nobody had looked at it in a real terminal. The first person who did saw an empty middle, a logo that read as a blob and sparse gauges within seconds.

## 12. Verify every citation

A sub-agent closed a task as "superseded by c9476137". That commit does not exist. Another proof cited a test file that was not on main. A closing loop then trusted the list and closed 12 tasks unverified.

## 13. The base expires

Seventeen handover lines said `base 90a3fcd9 = current main`, checked by a fetch at the start of the run. Forty minutes later main was fourteen commits ahead and every line was false. The measurements were fine; the label was not.

## 14. A test that repeats a constant

A new health check refused SQLite below 3.51.3. Its test checked 3.51.2 as "below" and 3.51.3 as "supported", the number quoted back at itself. Nothing stated why 3.51.3. Both Linux machines ran stock Ubuntu 24.04 with SQLite 3.45.1, so the check would have turned every Linux host red, and every new one after it.

## 15. Fix the class

A helper that released a claim on refusal was correct, documented and tested, and called from one of four refusal branches. Its two tests covered that one branch. The other three kept leaking while the suite stayed green.

## 16. A detector that flags everything

Two sessions independently built a static check for the same question: does this branch have the CLI command its test calls? One flagged 208 of 208 branches, the other 8 of 8. Both read the command list from one or a few files; the real list is spread over many modules. One known-good branch would have shown it in a minute.

## 17. Cleanup before the work

A verifier locked each task at startup and released the locks in an `atexit` handler registered at the end of the file. A run died on a timeout before reaching that line, and every lock it held stayed locked.

## 18. A destructive command as a question

To check whether a working tree matched main, an agent ran `git fetch && git reset --hard origin/main`. It answered the question and destroyed four uncommitted edits. `git status --short` and `git diff --stat origin/main` would have answered it without writing anything.
