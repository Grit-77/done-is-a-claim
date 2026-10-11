# Use reports and their evidence

Share what the toolkit helped you notice, what failed, or what was confusing.
Use the existing [use-report form](https://github.com/Grit-77/done-is-a-claim/issues/new?template=use-report.yml).
A report can be useful without claiming an improvement or comparing tools.

Keep these evidence categories separate:

| Category | Source | What it establishes and leaves open |
| --- | --- | --- |
| Synthetic demonstration | [Recorded false-green example](demo-recording.md), [source](../examples/false_green.py), [animation](../assets/demo/false-green-recorded.gif), [static proof](../assets/demo/false-green-recorded.png) | Captured output demonstrates a verifier/wrapper exit mismatch. It is not a production incident, native agent session or effectiveness benchmark. |
| Author-observed native sessions | [Native observations dated 2026-10-10](NATIVE-TESTS.md#observed-native-runs--2026-10-10) | The author recorded installation, skill loading and bounded fixture results separately. Codex fixture acceptance and Claude's quota-blocked execution are both reported. These historical samples used the revisions named there; they do not verify the current release or isolate the plugin's causal contribution. Raw transcripts remain local. |
| Independent reports | [Public use-report search](https://github.com/Grit-77/done-is-a-claim/issues?q=is%3Aissue+%22%5BUse+report%5D%22) | No independent report is included here yet. Reports should be read for their actual evidence and limitations before treating them as independent outcomes. |
| Author-observed daily workflow | [Review sessions dated 2026-10-11](NATIVE-TESTS.md#observed-daily-review-sessions--2026-10-11), [repeatable fixture](../examples/review-feedback/README.md) | Initial-candidate implementation showed failing regression tests before the fix; revised skills received a fresh review-only probe. These are different source snapshots and paths, not a comparative effectiveness result. |

This page indexes selected evidence; it does not count adoption or imply that
unlisted private experiences do not exist.

## What makes a report useful

The existing form asks for environment, selected rule/skill/tool (and release or
revision when known), task, actual observation and uncertainty. Include a concrete
command/output excerpt or reviewed artifact link when you can make it public.
Identify whether your case was synthetic or a real task and which result you
checked yourself. A [Markdown receipt report](REPORTS.md) can help describe command
history and evidence freshness; it cannot establish that the task met acceptance.

For example, describe the specific claim the instructions helped you question,
the missed failure, an unclear step or the installation problem you encountered.
If you lack a comparison run or cannot share the underlying evidence, say so.
Remove credentials, personal information and private customer details before
sharing; omit raw transcripts you cannot safely publish.

For a repeatable native exercise, see [NATIVE-TESTS.md](NATIVE-TESTS.md). Keep
package registration, actual skill loading and independently checked task outcome
as separate observations. A configured profile alone does not establish the
runtime model used.
