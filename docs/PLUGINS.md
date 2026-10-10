# Native plugin installation

The `done-is-a-claim` plugin ships the connected skills in this repository as one
optional package, version **1.3.0**. Its marketplace is
`done-is-a-claim-marketplace`. Installing it makes instructions available to the
agent. It provides no MCP server, credentials, executable hooks, or tool intercepts.
The compatibility manifest's `hooks: {}` registers no hooks.

The command syntax below was checked against **Codex CLI 0.160.1** and
**Claude Code 2.1.289**. Availability depends on the host and its plugin policy;
older clients may need an update. A validated package is not evidence that an
installed skill was selected or followed in a live session.

## Codex

Register the GitHub marketplace and install its plugin:

```bash
codex plugin marketplace add Grit-77/done-is-a-claim
codex plugin add done-is-a-claim@done-is-a-claim-marketplace
```

These commands change the current Codex profile's marketplace and plugin
configuration. They are not a project-local file-copy install. To test an
unpublished checkout, replace the first command's source with that checkout's
absolute directory, or select a published branch with `--ref <branch>`.
The selected source must already contain the package manifests and catalog.

Restart Codex or begin a fresh session after installation. Check the available
package with `codex plugin list`, then select `using-done-is-a-claim` from the
installed skills in the host's skill picker or `$` completion. If a name collides
with another installed skill, select the entry from this plugin. Start with:

> Use the installed Done is a claim skill `using-done-is-a-claim`. Read this
> project's instructions, identify the acceptance outcome and command, and
> choose the next workflow for this task.

Check that the selected skill belongs to this installed package before relying
on the result. A plugin listing confirms registration; it does not confirm the
agent used the workflow. If the host does not expose the skill, report that gap
and use the [file-copy installation](INSTALL.md) instead.

Update a Git marketplace snapshot, then reinstall the plugin from it:

```bash
codex plugin marketplace upgrade done-is-a-claim-marketplace
codex plugin remove done-is-a-claim@done-is-a-claim-marketplace
codex plugin add done-is-a-claim@done-is-a-claim-marketplace
```

`marketplace upgrade` refreshes Git snapshots; it does not by itself establish
that an installed plugin cache changed. `remove` deletes this plugin's local
cache. Restart afterward and check the installed version. Local marketplace
edits can likewise be picked up by removing and adding the plugin again.

To uninstall, use just the `codex plugin remove` command above. If the catalog
is also no longer needed, use:

```bash
codex plugin marketplace remove done-is-a-claim-marketplace
```

## Claude Code

Register the marketplace, then install into the current project's settings:

```bash
claude plugin marketplace add Grit-77/done-is-a-claim
claude plugin install done-is-a-claim@done-is-a-claim-marketplace --scope project
```

Marketplace registration changes Claude's marketplace configuration. The
explicit install scope records the plugin in this project's settings. Use
`--scope local` for settings local to this checkout, or `--scope user` only when
you want it across projects. Check your team's settings before committing a
project-scope installation. These commands do not copy rules into `CLAUDE.md`.

Restart Claude Code. In the project session, invoke:

```text
/done-is-a-claim:using-done-is-a-claim
```

Other packaged skills use the same namespace, for example
`/done-is-a-claim:debugging-with-evidence` and
`/done-is-a-claim:reviewing-changes`. Confirm their presence in the session's
skill list and inspect the agent's output against your acceptance criteria.

For an unpublished checkout, register its absolute directory instead of the
GitHub source. You can also preview directly from the repository root without
installing into settings:

```bash
claude --plugin-dir .
```

Update the marketplace and the project installation:

```bash
claude plugin marketplace update done-is-a-claim-marketplace
claude plugin update done-is-a-claim@done-is-a-claim-marketplace --scope project
```

Restart after updating. For an installation made with `local` or `user` scope,
use that same scope when updating or uninstalling:

```bash
claude plugin uninstall done-is-a-claim@done-is-a-claim-marketplace --scope project
```

## Rules and tools are opt-in

The repository's root [AGENTS.md](../AGENTS.md) and [CLAUDE.md](../CLAUDE.md) are
project instruction files. Plugin installation does **not** adopt them as your
project's rules. Merge the rules you choose into your project instructions;
Claude's `CLAUDE.md` can import the corresponding project-local `AGENTS.md`.
The entry skill helps choose workflows, and cannot enforce agent compliance.

The optional Python tools under [tools/](../tools/) stay ordinary scripts. An
installed skill does not grant shell access, make `python tools/receipt.py` exist
in another project, or register a tool API. To run the scripts, keep a trusted
checkout, resolve their actual paths, and use Python 3.10+, Git and the project's
allowed tools. Run project acceptance commands in the target project, with the
permissions that project requires. Without tool access, the agent must report
which checks remain unrun. See [receipt usage](RECEIPTS.md) and
[the connected workflow](WORKFLOW.md).

## Package checks and their limits

From the repository root:

```bash
python tools/check_package.py
python tools/check_repository.py
python tools/run_tests.py
claude plugin validate --json .
claude plugin validate --json .claude-plugin/plugin.json
```

The package checker verifies manifest identity/version agreement, presentation,
catalog references, contained skill paths and the skills-only package policy.
Its tests use complete fixtures and deliberately broken versions. The repository
checker validates document targets and the supported simple skill frontmatter.
Neither checker is a replacement for the host's parser or a behavioral eval.

Validate the **complete repository**, rather than a copied `skills/` directory:
the latter skips the package metadata and can hide packaging defects. Claude
may choose the marketplace as the root validation target; the explicit manifest
command also checks the plugin manifest. Its expected warning that root
`CLAUDE.md` is not loaded as project context is consistent with the opt-in rules
above. `--strict` turns that warning into a failure. Report warnings and the
command's own exit status instead of labelling a strict run green.

There is no Codex package-validation subcommand in the checked CLI's plugin
help. These structural and Claude checks do not demonstrate Codex installation,
session activation, or skill effectiveness. Test selection in a fresh host
session and use the [manual behavioral scenarios](../evals/README.md) for those
separate claims.

## Package layout and sources

`plugin.json` is the portable Agent Plugins 1.0 manifest. Skills are discovered
from root `skills/`; OpenAI presentation belongs under
`extensions.com.openai.interface`. `.codex-plugin/plugin.json` is the synchronized
compatibility overlay. `.agents/plugins/marketplace.json` advertises the local
package to Codex. Claude uses `.claude-plugin/plugin.json` and
`.claude-plugin/marketplace.json`, whose `./` source points to the full package.

The formats follow [OpenAI's package guide](https://developers.openai.com/plugins/build/plugins),
[Claude's plugin manifest reference](https://code.claude.com/docs/en/plugins-reference),
and [Claude's marketplace guide](https://code.claude.com/docs/en/plugin-marketplaces).
The shell syntax was checked with each installed CLI's `plugin --help` and
the relevant subcommand help. No native installation or runtime activation is
claimed by these documentation and structure checks.
