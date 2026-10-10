---
name: whose-red
description: "Investigate whether a failing test run is caused by a change, was already broken on main, or is inconclusive, using matched branch and clean-main runs. Use when tests fail on a branch or PR, when an agent says 'this failure is pre-existing', or before retrying or reverting a fix."
---

# Whose red is it

A red says the suite failed, not who failed it. The branch's log alone may not
separate "the change is wrong" from "main was already broken". Use a matched
control where possible, investigate differences, and report uncertainty before
you retry, revert or block on the red.

## Procedure

1. **Read the error text first.** These errors can point to setup or command
   problems, but can also result from the change:
   - `command not found`, exit 127, a missing interpreter or tool;
   - `file or directory not found` for the test path itself (exit 4 in pytest);
   - `no tests ran` / nothing collected (exit 5 in pytest);
   - network, disk-full or permission errors.
   Check the paths, dependencies, configuration and relevant diff before
   assigning cause. A removed test path, changed tool requirement or broken
   setup may be a regression. A check that never ran is not a pass.
2. **Prepare a clean control.** A scratch worktree detached at an explicit main
   commit, never your working checkout:

   ```bash
   git fetch origin
   git worktree add --detach ../control origin/main
   cd ../control && git rev-parse HEAD && git status --porcelain
   ```

   Quote the printed commit. `git status --porcelain` must print nothing.
3. **Match the experiment on both trees.** Use the same command, paths, flags
   and environment. If narrowing a full-suite failure to files or tests, rerun
   that narrowed command on the branch before comparing it with main. If the
   failure depends on order or shared state, compare the full suite, including
   its order or seed. Record any unavoidable differences; they limit the verdict.
4. **Compare failure signatures and all failures in the matched scope.** Test
   names alone do not identify a cause. Compare error text, failing assertion
   and relevant stack or context; check for additional branch failures.

   | Control on main | Verdict | Do |
   |---|---|---|
   | Same failure signature on both | Evidence that this failure existed on the tested main commit | Report the shared failure; assess extra failures or changed behavior separately; this does not exonerate the whole change |
   | Extra branch failures or a different signature | Possible additional regression | Investigate each difference against the diff and matched runs |
   | Main green, branch red | Evidence implicating the change in this scope | Investigate the cause; repeat matched runs if nondeterminism is plausible |
   | Outcomes or counts vary between runs | Nondeterministic or otherwise inconclusive | Record repeated matched outcomes and investigate variability; do not infer load sensitivity from a count alone |
   | Files exist only on the branch, or setup prevents comparison | No direct matched control yet | Investigate the new test or setup; report the comparison as inconclusive rather than assigning cause by construction |

5. **Check the base before retrying.** Record the branch's base and the main
   commit tested. If a newer main could matter, test integration in a separate
   scratch worktree. Do not automatically rebase or modify the owner's branch.
6. **Record both runs.** A verdict with one number in it is a guess:

   ```text
   command/scope: <matched command, environment, order or seed if relevant>
   red: <test id> — <failure signature>; extra branch failures: <ids or none>
   branch <commit>: FAIL   control main <commit>: PASS|FAIL
   verdict: evidence of pre-existing failure | additional regression | environment | inconclusive
   limits: <unmatched conditions, repetitions, or untested scope>
   ```

## Main's own reds

Keep a short list of failures observed on main, including their signatures,
commands and commits. Use it as a lead, not a standing exemption for other
branches. Re-check it on the relevant main commit before using it to explain
a new red, and retire entries once matched runs show them resolved.
