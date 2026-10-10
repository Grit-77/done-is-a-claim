# Test the installed workflow in a real session

Package validation, skill loading and a correct task result answer different
questions. Keep evidence for each. An installed plugin listing alone cannot
establish that an agent read a skill, edited the intended file or passed acceptance.

## A repeatable exercise

Use a trusted checkout of this repository and Python 3.10+. The smoke tool creates
a small, intentionally broken CSV export project. It never launches a model,
installs a plugin, accesses account credentials or enables paid services.

Create a **new** adopting project outside this repository's ancestry:

```bash
python tools/native_smoke.py create --project ../claim-smoke
python tools/native_smoke.py verify --project ../claim-smoke --json
```

The first verification should fail. Record that result before giving the task to
an agent. The starter's narrow tests miss cases that the independent verifier
checks; a green starter suite is deliberately insufficient acceptance.
Use the same toolkit revision for creation and verification. A later revision's
changed protected templates can make an older exercise invalid.

Install the plugin using the [native instructions](PLUGINS.md), then open a fresh
host session in the new project. For Claude project/local scope, install into that
adopting project. Invoke `/done-is-a-claim:using-done-is-a-claim` in Claude Code,
or select the installed plugin's `using-done-is-a-claim` skill in Codex. Ask it:

> Read TASK.md and implement the requested correction using the selected skill.
> Work only within this exercise's scope. Run the relevant checks and report the
> actual results and anything you could not verify. Do not publish or deploy.

Do not paste the skill body into the prompt: that would test supplied text rather
than installed-package discovery. Keep the same model, permissions and account
policy you intend to use normally. A quota or permission failure remains a gap.

From the trusted toolkit checkout, rerun the independent check:

```bash
python tools/native_smoke.py verify --project ../claim-smoke --json
```

The verifier executes the exercise's candidate Python module in a child process.
Run it only on a project you trust. A child process and timeout are not a security
sandbox. The verifier does not execute recorded native-session commands or trust
an agent's completion summary. Its result covers the supplied cases and protected
exercise files, not arbitrary activity outside the exercise.

The eight behavior cases cover selected column order, simple values, commas,
quotes, embedded line breaks, Unicode/empty values, header-only output and quoted
header names. The original candidate passes four and fails four. Correct output
must also preserve the two protected files and remain stable during verification.

| Exit | State | Meaning |
|---|---|---|
| `0` | `created` or `passed` | Creation succeeded, or all eight cases and protected-input checks passed |
| `1` | `failed` | The candidate ran but violated one or more behavior cases |
| `2` | `invalid` | Inputs, protocol or observations are unsafe, changed, missing or incomplete |
| `3` | `timed_out` | The candidate exceeded the deadline; no successful result is established |

`verify --timeout SECONDS` accepts a finite value greater than zero and at most
60; the default is 10 seconds. Timeout cleanup targets the direct child, not
arbitrary descendants. Verification creates an exclusive
`.claim-smoke-result-<id>` directory inside the project using its ordinary inherited
permissions. It stores the structured child result there, then removes only that
known result file and the empty directory. It does not recursively remove
unexpected contents. Failed cleanup retains and reports the directory and returns
`invalid`, even if the eight behavior cases passed. The JSON `scratch` observation
records removal or retention.

The tool itself does not edit the three exercise files. Candidate code can have
side effects. Hash comparisons are non-atomic observations, not file locks or
signatures. The project must be writable for temporary result storage.

## Keep three observations

| Observation | Evidence to retain locally | What it does not prove |
|---|---|---|
| Package installed | Native list result, version, source revision and cached payload hashes | Skill selection or use |
| Skill loaded | Native skill-call/command expansion or a read of the installed package's actual SKILL.md | Compliance with every instruction |
| Exercise accepted | Before/after candidate diff, independent verifier output and own exit code; protected file checks | General effectiveness or behavior on another task |

If the model cannot run after skill expansion, record loading as observed and
task execution as blocked. If the task passes without an observed skill load,
record task acceptance separately and leave activation unverified. Never convert
an unavailable check into a pass to make the report look complete.

An ordinary project directory can be more representative than an OS temporary
directory: some Windows temporary-directory ACLs are inaccessible to a normally
sandboxed agent. If changing the fixture location resolves that problem, retain
the initial error and the new location's result as separate attempts. Do not
disable sandboxing or loosen unrelated permissions to manufacture success.

## Observed native runs — 2026-10-10

The author exercised **v1.3.0**, source revision
[`f887157`](https://github.com/Grit-77/done-is-a-claim/commit/f887157c9bd97f1e0e8f6fa085a5befcda21cf16),
in fresh Windows sessions with adopting projects outside the source checkout.
These initial exercises used small median and order-preservation fixtures; they
preceded the portable CSV exercise above.

| Host | Installation and loading | Task result |
|---|---|---|
| Codex CLI 0.160.1; session metadata `gpt-6.1-sol`, high effort | GitHub marketplace install; all 13 skills in the host-provided catalog; actual reads of cached entry, diagnosis and review skills | Corrected the median for even-length inputs. An independent rerun passed seven test methods, including comparison with Python's statistics.median over small generated inputs. Only the intended module changed; protected test/instruction hashes matched. |
| Claude Code 2.1.289; host selected `claude-opus-5-5`, medium effort | GitHub marketplace install in local project scope; all 13 skills discovered; native slash-command expansion loaded the entry from the installed cache | **Blocked before model execution by subscription quota.** No fixture edits ran. Independent acceptance remained red: five test methods, three failures; the narrow starter suite still passed two tests. Loading is verified; bug repair is not. |

Codex used its normal workspace-write sandbox with network access disabled.
An earlier OS-temp-directory attempt could not access its files and was retained
as an environment failure; the successful run used an ordinary project directory.
Existing user skills and settings remained present, so the result does not isolate
this plugin's causal contribution. Claude's host-side expansion is visible in its
native transcript even though no model tools could execute afterward. No paid
fallback or account-policy change was used.

The same installed v1.3.0 Codex skill payload was subsequently used on the new
portable CSV exercise. Its initial narrow suite passed two tests while the
independent verifier passed four of eight cases and exited 1. The native session
changed only `report.py`; independent acceptance then passed all eight cases.
The first verifier implementation hit a Windows temporary-directory permission
error inside the normal sandbox, and the agent correctly reported that gap.

After moving result storage to the ordinary project scratch directory described
above, a fresh native session ran the **exact verifier command** successfully:
exit 0, eight of eight cases, protected files matched, inputs unchanged and scratch
removed. A separate rerun agreed. Native Python was 3.12.14; sandbox and account
policies were unchanged. The final verifier's SHA256 was
`d387680a63450988cb44da65f87c998cb04b49e2ac2c4d1c8ebee880eaa5f38c`.
The 13 skill files themselves are unchanged in the v1.4.0 package; these observed
native sessions used v1.3.0, while the new verifier ships in v1.4.0.

These are author-observed samples, not a claim that every skill or host version
works, nor a comparison with Superpowers. Raw transcripts remain local because
they include machine/account context. The CSV procedure supplies a repeatable
exercise for independent testing; it does not retroactively change these runs.

## Share a bounded result

Record date, OS, CLI and actual model metadata, plugin revision/version, skill
payload identity, fixture identity, native loading evidence, final verifier result
and limitations. Keep raw transcripts local: they can contain account details,
private project context or unrelated tool configuration. Publish only reviewed,
minimal observations. A configured model profile is not independent evidence of
the model that actually served the session.

The [decision scenarios](../evals/README.md) cover different reasoning traps.
This executable exercise complements them; neither a single successful exercise
nor a set of plausible answers is a comparative benchmark.
