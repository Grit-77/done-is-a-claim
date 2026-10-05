---
name: whose-red
description: "Decide whether a failing test run is the change's fault or was already broken on main, before retrying, reverting or blaming anyone. A red is a measurement, not a verdict; the verdict needs a clean-main control on the same test files. Use when tests fail on a branch or PR, when an agent says 'this failure is pre-existing', or before spending another attempt on a fix."
---

# Whose red is it

A red says the suite failed, not who failed it. Nothing in the branch's own log
separates "the change is wrong" from "main was already broken". Only a control
does. Settle it before you retry, revert or block on the red.

## Procedure

1. **Read the error text first.** Some failures belong to the machine or the
   test command on sight, not to the change:
   - `command not found`, exit 127, a missing interpreter or tool;
   - `file or directory not found` for the test path itself (exit 4 in pytest);
   - `no tests ran` / nothing collected (exit 5 in pytest);
   - network, disk-full or permission errors.
   Fix the environment or the command; do not count these against the change.
2. **Prepare a clean control.** A scratch worktree detached at an explicit main
   commit, never your working checkout:

   ```bash
   git fetch origin
   git worktree add --detach ../control origin/main
   cd ../control && git rev-parse HEAD && git status --porcelain
   ```

   Quote the printed commit. `git status --porcelain` must print nothing.
3. **Run only the failing test files there**, with the same command, flags and
   environment the branch used. The narrow run takes seconds.
4. **Compare named tests, not counts.**

   | Control on main | Verdict | Do |
   |---|---|---|
   | Fails the same named test | Main's; the change is innocent | Record it, report main's red, spend no attempt on the change |
   | Same error, different count | Main's, load-sensitive | The same, and note that the count varies with load |
   | Green on those files | The change's | Record both runs; fix the change with the cause named |
   | The files exist only on the branch | The change's by construction | No control is possible or needed |

5. **Before retrying a change-owned red, rule out a stale base**: rebase on
   current main and run again first.
6. **Record both runs.** A verdict with one number in it is a guess:

   ```text
   red: <test id> — <error line>
   branch <commit>: FAIL   control main <commit>: PASS|FAIL
   verdict: change | main | environment
   ```

## Main's own reds

Keep a short list of tests that are red on main and why. One entry explains
other branches' reds for as long as it stands. Remove the entry when main is
green on it again, and re-check any decision that rested on it.
