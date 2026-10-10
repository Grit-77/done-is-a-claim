# Contributing

Bring a failure that taught you something an agent can act on.

## A useful proposal

Open a [rule proposal](https://github.com/Grit-77/done-is-a-claim/issues/new?template=new-rule.yml)
with the claim, what actually happened, and the evidence that separated them.
Remove credentials, personal information and private customer details. An honest
anonymized account is better than a raw log you cannot safely share.

For a core rule, add its incident to [INCIDENTS.md](INCIDENTS.md). For an optional
workflow, identify the existing incident or public source it extends. Label a
hypothetical example as synthetic; never present it as a production incident.

## Keep the toolkit small

- Core rules should apply across repositories and fit in [AGENTS.md](AGENTS.md).
- Conditional workflows belong in `skills/<name>/SKILL.md` with a specific trigger.
- Prefer a counterexample that exposes bad reasoning to another absolute command.
- New evidence takes precedence over an old rule. Explain the correction.
- Write original prose. Attribute inspiration and respect source licenses.

Keep the English and Turkish READMEs aligned when changing scope, installation or
limitations. Record source and verification limits in [CLAIMS.md](CLAIMS.md) or
[SOURCES.md](SOURCES.md), as appropriate.

## Check a change

Requires Python 3.10 or newer. From the repository root:

```bash
python tools/run_tests.py
python tools/check_repository.py
git diff --check
```

These checks exercise the repository checker and check document structure. They
reject empty test discovery and suites where every test is skipped. They
do not measure whether an agent follows a skill. For behavior changes, also run
the relevant [evaluation scenarios](evals/README.md) in a fresh session and report
the actual response and limitations. Open both READMEs in a Markdown renderer
when changing presentation.

Use the [completion receipt](templates/completion-receipt.md) in your PR. Include
checks you could not run. Do not turn a failed scenario into a pass by changing
its rubric after seeing the response.
