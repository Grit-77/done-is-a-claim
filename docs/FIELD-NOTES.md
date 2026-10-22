# What the check actually proved

Three short field notes about reading development evidence. The examples in
notes 1–3 are **synthetic local fixtures**, rerun on 22 October 2026 against
toolkit revision `1b5b53735939cc231cc67f1a4cbe929d4e708696`. They are not
production incidents or measurements of agent effectiveness.

The [real documentation PR below](#a-real-pr-with-a-bounded-receipt) is a separate
author-owned example. It does not establish independent user adoption.

## 1. The verifier failed; the summary finished

An outer process can finish successfully while the check inside it fails.
From this toolkit's root, with Python 3.10+:

```bash
python examples/false_green.py
```

The recorded synthetic run reports:

| Observation | Result |
| --- | --- |
| Verifier exit | 1 |
| Summarizer exit | 0 |
| Receipt state | FAIL |
| Demo exit | 0, because the intended mismatch was demonstrated |

The summarizer's exit answers whether the summarizer finished. Keep the
verifier's own exit when assessing its check. Then inspect whether that check
actually covers the task's acceptance condition.

[Runnable example](../examples/false_green.py) ·
[Recording and limits](demo-recording.md) ·
[Reading measurements skill](../skills/reading-measurements/SKILL.md)

## 2. A successful check can become stale

The command's historical result does not change when a selected file changes
later. Its evidence may no longer describe the current inputs.

For this note, a temporary project contained `app.py` and `test_app.py`. The
receipt tool captured the real unittest command with both files selected. The
reporter was run before and after appending a comment to `app.py`:

| Observation | Before selected-byte edit | After selected-byte edit |
| --- | --- | --- |
| Historical child exit | 0 | 0 |
| Recheck state | matches | different |
| Reporter exit | 0 | 1 |

The comment did not demonstrate a behavior regression. It demonstrated that
the selected bytes differed. The reporter did not rerun the tests, so it could
not say whether the edited project still passed them.

Use your actual project inputs and command with the
[existing-project receipt guide](REPORTS.md). Unselected dependencies and the
environment are outside that file comparison. Receipts are editable local
evidence, not signed attestations.

[Recheck semantics](RECHECK.md) ·
[Evidence freshness skill](../skills/evidence-freshness/SKILL.md)

## 3. A completed copy can contain the wrong artifact

The delivery demo compares the intended reviewed artifact, the copied bytes
and what the receiving side can parse:

```bash
python examples/wrong_delivery.py --json
```

| Synthetic case | Copy completed | Matches intended reviewed bytes | Parses as JSON |
| --- | --- | --- | --- |
| Correct copy | yes | yes | yes |
| Stale file with the same name | yes | no | yes |
| Matching invalid JSON | yes | yes | no |

Copy completion, provenance and consumer use answer different questions.
Read back the actual destination and apply the consumer check appropriate to
the deliverable. This demo's outer exit 0 means its expected contrasts were
observed; it does not mean every copied artifact was correct.

[Runnable example](../examples/wrong_delivery.py) ·
[Checking delivery skill](../skills/checking-delivery/SKILL.md)

## A real PR with a bounded receipt

[PR #9](https://github.com/Grit-77/done-is-a-claim/pull/9) moved the recommended
first use before the synthetic demo in English and Turkish, and added launch
drafts. It changed documentation, not executable toolkit behavior.

| Evidence boundary | Observation |
| --- | --- |
| Base | `a0f0c71539bacddbb21b5dfa5bb7fb6770d95800` |
| Reviewed PR head | `77700bc3cd767dbf96f66f5899e5d559241c73b9` |
| Merge commit | `1b5b53735939cc231cc67f1a4cbe929d4e708696` |
| Hosted repository checks | [Linux and Windows run](https://github.com/Grit-77/done-is-a-claim/actions/runs/39839834027) succeeded |
| Hosted static analysis | [Python and Actions CodeQL run](https://github.com/Grit-77/done-is-a-claim/actions/runs/39839830001) succeeded |
| Scope of the receipt | Historical checks on the named documentation PR |
| Still unverified by those checks | Whether a person can follow the guide; whether an agent follows the skills; improved outcomes or repeated use |

The [captured public check metadata](evidence/pr-9-public-checks.json) records
each selected check's name, head SHA, result and source URL. It is an index of
public historical observations, not an authenticity guarantee or a verdict
that the user-facing task is complete.

The author also ran a temporary receipt/report rehearsal locally. That is
author-observed synthetic evidence; it is not an independent user's first-use
report. Raw local logs and machine paths are not part of this public example.

## Try a boundary in your own work

Choose one real task and identify what its check can distinguish. Retain the
actual result and any gap, then [share a use report](https://github.com/Grit-77/done-is-a-claim/issues/new?template=use-report.yml)
if you can make the evidence public. A confusing step or failed attempt is
useful too.
