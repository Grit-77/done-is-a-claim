---
name: reading-measurements
description: "Read a number without being fooled by it: an exit code, a passing result file, a test count, a list size, a control run, a red or a green. Use before reporting any figure, before turning a test run into a verdict, before acting on 'N items are broken', and whenever two outputs or two counts of the same thing disagree."
---

# Reading measurements

Wrong reports rarely lack a measurement. They read a real number as answering a
question it never asked. Before you report, decide or spend anything on a
figure, ask:

> What would this same number look like if my claim were false?

If the answer is "exactly the same", the number alone does not distinguish the
claim from its alternative. Seek a discriminating observation or control.

## Reading any figure

Use the relevant checks below to decide what the figure supports. A limitation
may invalidate an interpretation without invalidating the observation itself.

1. **An exit code is not a verdict.** pytest exit 4 indicates a usage error,
   such as a missing path; exit 5 indicates nothing was collected. Read the
   collection and result summaries. `no tests ran` does not establish a pass;
   investigate selection, setup and the change before assigning cause.
2. **Capture the command's own exit code.** In `cmd | tail; echo $?` the
   status is `tail`'s in ordinary shell pipeline behavior. Capture the tested
   command's status before reading a saved log, or use the shell's pipeline
   status facility. `set -o pipefail` detects a failing pipeline in shells
   that support it; its status is not necessarily the tested command's code.
3. **Read the relevant artefacts.** A result file, a CI summary, a log and a
   progress counter are separate claims about one run. When they disagree, the
   disagreement is the finding.
4. **A green names its tree.** Quote the branch and commit with each code-run figure
   and say whether the working tree was dirty. A run on main measured main,
   not your change.
5. **Match the scope of a comparison**: paths, flags, environment and relevant
   machine conditions, with clean trees and quoted commits. Rerun a narrowed
   command on both trees before comparing; use the full suite if order or
   shared state matters. Record unavoidable differences as limits. Matching
   test names alone does not establish the same failure or exclude extra reds.
6. **A result belongs to the revision measured.** It remains historical
   evidence when main moves, but a claim about current main needs a fresh run.
7. **An all-positive detector needs investigation.** The inputs may all be
   affected, or the detector may be wrong. Check a known-good case and inspect
   its classification before trusting the inferred failure rate.
8. **A count travels with its filter.** Print the query, and every exclusion,
   with the total, including the unit counted: definitions, collected test
   cases and executed cases are different quantities. Investigate differences
   in filters, revisions, inputs and method before attributing a discrepancy.
9. **A returned value needs interpretation.** An HTTP 4xx, an empty response,
   a constant column or a 0-byte file may be valid for one question and useless
   for another. Check contents and status; record size and modification time
   when emptiness or freshness matters to the claim.
10. **Capture the whole output** to a file and read its tail from the file;
    a live `| tail` may omit the cause and hide progress.
11. **Agreement needs independence.** Two numbers copied from one source agree
    with themselves.
12. **A timeout is an observation, not a cause.** Record the deadline and last
    progress. Isolate tests under a wall-clock limit when useful, but preserve
    the original suite run: isolation can hide order or shared-state failures.
13. **A quiet log is not a stall.** A pipe ending in `| tail` prints nothing
    until the run exits. Check process state and progress before calling it
    stuck; CPU time alone does not distinguish useful work, waiting or a loop.

## Acting on a count

A list size measures the selected set, not necessarily the broken population.
Before acting on "N items are broken":

1. **Which filter produced this number?** Quote it with the figure.
2. **Is it one kind of thing?** Group the members by what they are about.
3. **Does one class dominate?** Classify failures by cause and count each
   class. A large class is a lead for a shared mechanism, not proof that one
   fix covers every member.
4. **Would this detector ever say no?** Run it on a case known to be clean.

A self-selected sample does not predict the rate of the whole list, and a
larger denominator does not repair it; draw the sample differently.

## A reportable figure

For a code-run figure, record its command, branch and commit, whether the tree
was dirty, relevant summary and log path. Include scope and filters for counts,
both runs for a comparison, and any limits or untested scope. Other figures
need their source, date and method. If evidence is unavailable, omit the factual
claim or explicitly attribute a report; do not present it as your measurement.
