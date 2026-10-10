# Done is a claim

**English** · [Türkçe](README.tr.md)

<picture>
  <source media="(prefers-reduced-motion: reduce)" srcset="assets/receipt.svg">
  <img src="assets/receipt-stamp.gif" alt="Done is a claim. A red SHOW THE RECEIPT stamp lands on the ivory cover.">
</picture>

[Replay stamp](assets/receipt-stamp.gif) · [Static cover](assets/receipt.svg)

**Your agent says “done”. What would prove it?**

An evidence-first development workflow for coding agents: **understand → plan →
implement → diagnose → review → verify → deliver**. 13 connected skills, 18
incident-backed rules, and optional tools that keep the evidence attached to the
work it tested. Small tasks take a shorter path.

[Get started](#get-started) · [Follow the workflow](docs/WORKFLOW.md) · [Choose a skill](#choose-a-skill) · [Try the demo](#watch-a-false-green)

## Get started

Install all skills as a native plugin:

**Claude Code**

```bash
claude plugin marketplace add Grit-77/done-is-a-claim
claude plugin install done-is-a-claim@done-is-a-claim-marketplace --scope project
```

**Codex**

```bash
codex plugin marketplace add Grit-77/done-is-a-claim
codex plugin add done-is-a-claim@done-is-a-claim-marketplace
```

Start a fresh session. In Claude Code, invoke
`/done-is-a-claim:using-done-is-a-claim`; in Codex, select
`using-done-is-a-claim` through `/skills` or the `$` skill picker.
[Plugin scope, updates and validation limits →](docs/PLUGINS.md)

Prefer project-local copies or the rules alone? Clone the repository:

```bash
git clone https://github.com/Grit-77/done-is-a-claim.git
cd done-is-a-claim
```

| You use | Add to your project |
|---|---|
| Codex or an agent that reads `AGENTS.md` | Copy [AGENTS.md](AGENTS.md) to the project root. |
| Claude Code | Copy [AGENTS.md](AGENTS.md) and [CLAUDE.md](CLAUDE.md), which imports it with `@AGENTS.md`. |
| Existing instructions | Merge the relevant rules into your file. Keep your project-specific commands and constraints. |

You can start with that one rules file. Native plugin installation does not add
these rules to the adopting project's instructions.
[Installation options on macOS, Linux or Windows →](docs/INSTALL.md)

Want the workflow in your project without overwriting existing files? From this clone,
replace `../my-project` with your existing project path and preview the copy:

```bash
python tools/install_skills.py --project ../my-project --agent codex --profile workflow --dry-run
```

Then omit `--dry-run` to install. For Claude Code, use `--agent claude-code`.
Existing skill destinations are refused; your project instructions stay untouched.
Use `--list` to see profiles and individual skills. Explicit `--update` can replace
unmodified installer-owned copies while retaining backups; local edits are refused.

Try this first request in your own project:

> Use using-done-is-a-claim for this task. Identify observable acceptance, take a
> proportionate path through implementation and review, and report the actual
> result, tested inputs and remaining gaps. Continue within my existing authorization.

This checks whether the agent understood the request. It does not enforce compliance.

## One workflow, short paths

Start with [using-done-is-a-claim](skills/using-done-is-a-claim/SKILL.md). It routes
substantial work through planning and execution, sends unexpected results into
diagnosis, and closes review findings with fixes and fresh checks. A clear, small
change goes straight from inspection to implementation, review and verification.
Workers are optional; an unavailable reviewer is reported as a self-review limit.

[See the flow and a worked task →](docs/WORKFLOW.md)

Want to test your installation on real work? From this repository's clone, create a small broken CSV project,
let your installed skill handle it, then check the result independently:

```bash
python tools/native_smoke.py create --project ../claim-smoke
python tools/native_smoke.py verify --project ../claim-smoke --json
```

The initial independent check deliberately fails even though the starter's narrow
tests pass. The tool creates and checks the fixture; you run the agent through
your normal host and account. [Real session procedure and observed limits →](docs/NATIVE-TESTS.md)

## Watch a false green

A command fails. The process reading its output succeeds. Report the wrong exit
code, and a failed check becomes a green report.

[Runnable source](examples/false_green.py). This is a synthetic demonstration,
not a production log or a benchmark.

Run it yourself from the cloned repository's root with Python 3.10+:

```bash
python examples/false_green.py
```

The demo succeeds when it exposes the mismatch. **The verifier inside it still
fails.** That distinction is the point.

A successful copy can also deliver the wrong artifact. The
[delivery demo](examples/wrong_delivery.py) contrasts a stale copy, the correct
copy, and identical bytes that still fail to parse:

```bash
python examples/wrong_delivery.py
```

It uses temporary local fixtures. Exit zero means the traps were demonstrated,
not that a real delivery succeeded.

## Get a real receipt

Capture a command's own exit, full output and Git state with the optional local tool:

```bash
python tools/receipt.py -- python tools/run_tests.py
```

It writes a fresh `receipt.json` and `command.log` under `.local/receipts/`.
Use `--input` to fingerprint selected files before and after the run. A zero exit
records command success; it does not declare the user's task complete.
[Usage, input scope and limits →](docs/RECEIPTS.md)

Reusing a saved receipt after an edit or handoff? Compare it with the current
project using the exact receipt path printed earlier:

```bash
python tools/check_receipt.py path/to/receipt.json --project .
```

[What this rechecks—and what a match cannot prove →](docs/RECHECK.md)

## What changes in the report

| A claim | Evidence that can support it |
|---|---|
| “The tests passed.” | The command, collected cases, actual result, its own exit status and the tested tree. |
| “That failure was already on main.” | Comparable branch and clean-base runs, with matching failure signatures. |
| “The worker finished.” | The worker's actual diff, checked inputs and acceptance result. Delivery is recorded separately. |
| “The screenshot was saved.” | An image that decodes and has been visually inspected. |
| “Ready to publish.” | The reviewed artifact still matches the artifact being published. |

Use the [completion receipt](templates/completion-receipt.md),
[acceptance brief](templates/acceptance-brief.md) and [handoff](templates/handoff.md)
as small, reusable formats. A missing check belongs in the report.

[Practical Bash and PowerShell evidence recipes →](docs/RECIPES.md)

## Choose a skill

| When this happens | Use this skill | It helps you decide |
|---|---|---|
| You want one entry point for the task | [using-done-is-a-claim](skills/using-done-is-a-claim/SKILL.md) | What is the next useful step, given the task, authority and available evidence? |
| The change has dependencies or substantial scope | [planning-changes](skills/planning-changes/SKILL.md) | Which bounded tasks, owners and observations will reach the requested outcome? |
| A plan has ready, authorized work | [executing-plans](skills/executing-plans/SKILL.md) | What can proceed now, and what evidence closes each task? |
| Behavior contradicts expectations | [debugging-with-evidence](skills/debugging-with-evidence/SKILL.md) | Which experiment distinguishes the plausible causes? |
| A change is ready for review | [reviewing-changes](skills/reviewing-changes/SKILL.md) | Does the actual diff meet the request, and are findings resolved and rechecked? |
| The task's “pass” condition is vague | [acceptance-design](skills/acceptance-design/SKILL.md) | Does this check cross the boundary the user actually cares about? |
| A number looks convincing | [reading-measurements](skills/reading-measurements/SKILL.md) | What does this output establish, and what does it leave unknown? |
| A test fails on your branch | [whose-red](skills/whose-red/SKILL.md) | Is there comparable evidence for a regression, an existing failure or an unresolved cause? |
| A subagent reports success | [collecting-worker-results](skills/collecting-worker-results/SKILL.md) | Is there relevant work, was that work tested, and was it delivered? |
| Work changed after a check | [evidence-freshness](skills/evidence-freshness/SKILL.md) | Does the receipt still describe the inputs you are about to act on? |
| A README or launch post makes a claim | [public-claims](skills/public-claims/SKILL.md) | Can the reader trace it, and are the verification limits stated? |
| You inherit unfinished work | [resuming-work](skills/resuming-work/SKILL.md) | Which checkpoint, artifacts and next action still apply in this checkout? |
| A send or publication reports success | [checking-delivery](skills/checking-delivery/SKILL.md) | Does the actual destination contain the reviewed result, and can its consumer use it? |

Each skill is a standalone `SKILL.md`. No Grit service, account or CLI is needed.

## The field rules

The complete wording lives in [AGENTS.md](AGENTS.md). Each original rule has a
failure story in [INCIDENTS.md](INCIDENTS.md).

| Moment | Rules |
|---|---|
| **Before you start** | **01** Define acceptance before the work. **02** Check the paths. |
| **Before you say “done”** | **03** Re-run on the current work. **04** Check the wider suite. **05** Capture the command's own exit code. **06** No tests is no pass. **07** Unknown is not pass. **08** Read every required check. |
| **When you report** | **09** Read the artifact. **10** Open what was written. **11** Look at it yourself. **12** Verify citations. **13** State the base and re-check it before publication. |
| **When you test and fix** | **14** Test behavior, not agreement with a constant. **15** Fix the defect class. **16** Test the detector on a known-good case. **17** Register cleanup before the work. |
| **Always preserve the work** | **18** Never use a destructive command to answer a question. |

## Where this came from

These rules grew out of running Claude Code and Codex on Grit's own repository.
The original internal records report **3,489** task acceptance re-runs between
14–29 September 2026, with **2,282** passing the first independent re-run. A
separate internal count reports **736** tasks whose own acceptance passed while
the full suite broke on main.

**These are author-reported historical observations, not a public benchmark.** The
raw internal logs are not included. Some unsuccessful re-runs were environment
failures; these figures do not establish an agent-error rate or the effectiveness
of this toolkit. [Claims and limits →](CLAIMS.md)

The additional workflows distill Grit's operational runbooks. They are identified
as guidance, not newly measured incidents. We also studied how related projects
organize installation, skills and verification. [Sources and design decisions →](SOURCES.md)

## Try to fool it

An agent can repeat a rule and still make the wrong decision. The
[scenario pack](evals/README.md) puts the instructions under pressure: a passing
pipe, mismatched controls, a worker with no relevant changes, stale evidence and
other traps. Participant prompts are separate from evaluator rubrics. Run the
prompts in fresh sessions and keep the responses.

These are manual behavioral evaluations, not published success-rate claims.

For the repository itself:

```bash
python tools/run_tests.py
python tools/check_repository.py
python tools/check_package.py
```

The test runner rejects empty or entirely skipped suites. The checks exercise the
tools and validate local document targets, skill metadata
and imports. [CI](.github/workflows/check.yml) runs on Windows and Linux. Passing
these checks does not prove that an agent follows the instructions.

## Rules are not a gate

This repository supplies instructions, small local tools, examples and evaluation material. It does
not intercept an agent's tools, block a merge or enforce a deployment policy.
Use your project's actual test and release gates for enforcement.

## Bring the failure that taught you

A useful contribution starts with what the agent claimed, what was true, and the
evidence that revealed the difference. [Propose a rule](https://github.com/Grit-77/done-is-a-claim/issues/new?template=new-rule.yml)
or [read the contribution guide](CONTRIBUTING.md).

Tried it in your own project? [Share a concrete use report](https://github.com/Grit-77/done-is-a-claim/issues/new?template=use-report.yml):
which piece you used, what happened, and what remains uncertain.

[Apache-2.0](LICENSE) · Made by [Grit](https://github.com/Grit-77), Ankara.
