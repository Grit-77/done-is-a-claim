---
name: reading-measurements
description: "Read a number without being fooled by it: an exit code, a passing result file, a test count, a list size, a control run, a red or a green. Use before reporting any figure, before turning a test run into a verdict, before acting on 'N items are broken', and whenever two outputs or two counts of the same thing disagree."
---

# Reading measurements

Wrong reports rarely lack a measurement. They read a real number as answering a
question it never asked. Before you report, decide or spend anything on a
figure, ask:

> What would this same number look like if my claim were false?

If the answer is "exactly the same", you hold agreement, not evidence. Build the
control.

## Reading any figure

Any item that fails invalidates the figure until it is fixed.

1. **An exit code is not a verdict.** pytest exits 4 (usage error, such as a
   path that does not exist) or 5 (nothing collected) when no test ran. Read
   the count line. `no tests ran` is a broken test command, not a pass.
2. **Capture the command's own exit code.** In `cmd | tail; echo $?` the
   status is `tail`'s. Use `set -o pipefail`, or write the output to a file
   and read the status before reading the file.
3. **Read every artefact.** A result file, a CI summary, a log and a progress
   counter are separate claims about one run. When they disagree, the
   disagreement is the finding.
4. **A green names its tree.** Quote the branch and commit with every figure
   and say whether the working tree was dirty. A run on main measured main,
   not your change.
5. **A control is the same experiment**: the same paths, flags, environment
   and machine, a clean tree and a quoted commit. A control that runs a subset
   of the treatment is not a control.
6. **Results expire when main moves.** Re-run any red older than the last merge
   before acting on it.
7. **A detector that never says no is broken.** If every input is flagged, the
   instrument is at fault until a known-good case answers the other way.
8. **A count travels with its filter.** Print the query, and every exclusion,
   with the total. Two correct counts of the same thing usually differ by
   filter, not by error.
9. **An unreadable value is not a value.** An HTTP 4xx, an empty response, a
   column holding one value on every row and a 0-byte file all return
   something. Print size and modification time with every file you read.
10. **Capture the whole output** to a file and read its tail from the file;
    `| tail` keeps the verdict and drops the cause.
11. **Agreement needs independence.** Two numbers copied from one source agree
    with themselves.
12. **A hang is not a verdict.** Run the tests one per process under a wall
    clock and name the one that never returns.
13. **A quiet log is not a stall.** A pipe ending in `| tail` prints nothing
    until the run exits. Check the process's CPU time before calling it stuck.

## Acting on a count

A list size is a filter, not a fact. Before acting on "N items are broken":

1. **Which filter produced this number?** Quote it with the figure.
2. **Is it one kind of thing?** Group the members by what they are about.
3. **Does one class dominate?** Classify failures by cause and count each
   class. The largest class usually has one mechanism and earns one fix.
4. **Would this detector ever say no?** Run it on a case known to be clean.

A self-selected sample does not predict the rate of the whole list, and a
larger denominator does not repair it; draw the sample differently.

## A reportable figure

It carries its full command, its branch and commit, whether the tree was dirty,
its count line, the control's commit for a verdict, the filter for a count, and
the path of its log. A figure with no receipt is removed, not qualified.
