# Install only what you need

For an agent handling “install this repository,” use the root
[installation guide](../INSTALL.md). It covers host selection, preservation of
existing work, result checks and a short explanation in the user's language.

For native Claude Code and Codex plugin installation, see [PLUGINS.md](PLUGINS.md).
The plugin exposes the complete skill catalog. This page covers project-local
copies, selected profiles and manual rule adoption.

Clone this repository somewhere separate from the project you want to work on:

```bash
git clone https://github.com/Grit-77/done-is-a-claim.git
```

## Project installer — preview, then copy

Requires Python 3.10+. From the clone's root, replace `../my-project` with your
existing project directory:

```bash
python tools/install_skills.py --project ../my-project --agent codex --skill reading-measurements --dry-run
```

Inspect the printed destinations, then run the same command without `--dry-run`
to copy the skill. Use `--agent claude-code` for Claude Code, or repeat `--agent`
to select both. Repeat `--skill` to select more than one skill.

To see available skills and profiles without writing anything:

```bash
python tools/install_skills.py --list
```

| Profile | Selection |
|---|---|
| `workflow` | All 13 skills, starting with `using-done-is-a-claim` |
| `evidence` | The eight focused acceptance, measurement, collection, freshness, claims, resume and delivery skills |
| `review` | Entry and review, plus measurement, failure attribution, freshness, public claims and delivery |

Install the connected workflow for one or both agents:

```bash
python tools/install_skills.py --project ../my-project --agent codex --agent claude-code --profile workflow --dry-run
```

Omit `--dry-run` after reviewing the destinations. Repeat `--profile`, or combine
it with `--skill`, to take their union without duplicate copies. The exact
selections live in [profiles.json](../profiles.json).

The installer preflights all selections and refuses existing skill destinations,
including links. It does not merge or overwrite them. Each installed folder gets
the license and a `PROVENANCE.json` containing the source revision when available
and hashes of copied files. File hashes identify the copied bytes; a revision is
not a signature or a guarantee that the source checkout was clean. Source skills
with empty directories are refused before copying: the file manifest does not
track empty directories, so accepting them would produce an unupdatable copy.

This is project scope only. It preserves `AGENTS.md`, `CLAUDE.md`, settings and
unselected skills. Add the core rules separately as described below. Interrupted
filesystem operations can leave a partial installation; the error reports what
was installed. No automatic cleanup deletes user material. Preflight is not a
lock against another process changing the destination concurrently.

Staging uses an exclusive project directory with the parent's ordinary inherited
permissions. Cleanup removes only known staged names, types and bytes after
checking their identities and containment. Unexpected, changed or linked content
is retained and reported as a failure. It never changes ACLs or recursively
deletes the staging tree. A cleanup failure can occur after copies completed;
read the actual counts and retained path before deciding what to do next.

An agent's sandbox may protect its own skill directories separately from ordinary
project files. Use the host's normal approval flow for the exact installation
command if necessary. If approval is unavailable, report the failing operation
and run that command from an authorized terminal; do not disable protection or
claim that a preview installed the skills.

## Explain the result to the user

Successful installation prints the paths written, actual copy/update counts,
what the selected skills help with and the next step for a fresh session.
It does not claim that the host has loaded the new skills. When an agent installs
for someone, follow the [short welcome format](../INSTALL.md#4-finish-with-a-short-explanation)
in their language: what changed, where, the practical benefit and how to start.
Keep the raw file list and technical details out of that short explanation.

For an installing agent or script, append `--json`:

```bash
python tools/install_skills.py --project ../my-project --agent codex --profile workflow --dry-run --json
python tools/install_skills.py --project ../my-project --agent codex --profile workflow --json
```

Inspect the preview before executing; an already authorized installation does
not require another routine approval. The schema-version-1 report is one JSON
object on stdout. Operational diagnostics can also appear on stderr. Invalid
CLI arguments retain argparse's usual exit 2 and do not promise a JSON object.

| Field | Interpretation |
|---|---|
| `state` | `listed`, `planned`, `installed` or `failed`; a plan is not an installation |
| `skills`, `agents` | Unique requested names and selected hosts |
| `copied_count`, `updated_count`, `installed_paths` | Completed destination folders only; two agents can receive 26 copies of 13 skills |
| `planned` | Intended actions, including actions that may remain unfinished after failure |
| `backups`, `incomplete_path`, `error` | Retained material and failure information to inspect before retrying |
| `staging` | Null when no staging occurred; otherwise its path, removal status and retained path/error |
| `source` | Declared package version and observed revision when available; unknown values are null, and neither authenticates the copied bytes |
| `capabilities` | Guidance for the selected skills, restricted to completed copies after a publication failure |
| `instructions_changed`, `activated` | The copier does not modify instructions/settings; it does not verify runtime activation |
| `next_step` | An actual selected skill to use after successful installation; null for previews and failures |

`--list --json` also works without a project or writes. On failure, use the exit
code and actual completed/retained paths; do not turn planned counts into a
success message. Backups and editable provenance have the same limits as before.

## Rules

Copy `AGENTS.md` from the clone to your project's root. If the project already has
instructions, merge the relevant rules into them; preserve its commands, scope
and conventions. Do not replace the project's context with this generic file.

For Claude Code, the included `CLAUDE.md` imports `@AGENTS.md`. If your project
already has a `CLAUDE.md`, add the import there instead of replacing it. Current
Claude Code versions can also read `AGENTS.md` directly under their configured
instruction policy; the explicit import remains useful for compatible setups.

## Manual and user-wide installation

Choose one skill from the [catalog](../README.md#choose-a-skill). The examples
below install `reading-measurements` for your user account. To install another,
replace the folder name in both source and destination.

| Agent | User scope | Project scope |
|---|---|---|
| Codex | `~/.agents/skills/` | `.agents/skills/` in your target repository |
| Claude Code | `~/.claude/skills/` | `.claude/skills/` in your target repository |

Run these commands from the parent directory of the clone.

### macOS / Linux / Git Bash

Codex:

```bash
mkdir -p "$HOME/.agents/skills"
cp -R -i done-is-a-claim/skills/reading-measurements "$HOME/.agents/skills/"
```

Claude Code:

```bash
mkdir -p "$HOME/.claude/skills"
cp -R -i done-is-a-claim/skills/reading-measurements "$HOME/.claude/skills/"
```

The `-i` option asks before overwriting existing files. Review an existing skill
before replacing it; your copy may contain local changes.
This manual copy can merge files individually. Use the project installer above
when you want the entire operation refused on a destination collision.

### Windows PowerShell

Codex:

```powershell
$skillRoot = Join-Path $HOME '.agents/skills'
$destination = Join-Path $skillRoot 'reading-measurements'
if (Test-Path -LiteralPath $destination) { throw 'Skill already exists; review it before replacing.' }
New-Item -ItemType Directory -Force -Path $skillRoot | Out-Null
Copy-Item -LiteralPath './done-is-a-claim/skills/reading-measurements' -Destination $destination -Recurse
```

For Claude Code, use `.claude/skills` instead of `.agents/skills` in `$skillRoot`.
For project scope, point `$skillRoot` at the chosen directory inside your project.

## Discover with the skills CLI

The existing skill folders are also discoverable by the third-party
[Vercel skills CLI](https://github.com/vercel-labs/skills). This optional route
requires Node.js 22.20.0 or newer for the pinned version below:

```bash
npx skills@1.7.2 add Grit-77/done-is-a-claim --list
```

`add --list` lists source skills; `list` lists skills already installed in the
current project. For a new destination, a selected copy can use:

```bash
npx skills@1.7.2 add Grit-77/done-is-a-claim --skill reading-measurements --agent codex claude-code --copy
```

Run inside the adopting project and choose project scope when prompted. Unlike
this repository's installer, that CLI replaces an existing selected skill
directory; `--yes` does not protect local edits. Keep the local installer for
collision refusal. The third-party CLI also maintains its own lockfiles and
telemetry behavior; consult its documentation. Its `DISABLE_TELEMETRY=1` or
`DO_NOT_TRACK=1` environment option disables telemetry.

Version 1.7.2 was exercised with v1.1.0's layout as a local source, in an isolated
project: source discovery found its six skills; selected copies for both agents
matched the source. That historical smoke check does not establish behavior for future
package versions or every host's agent-discovery policy.

## Check discovery

Start a new session in your target project. In Codex, request
`$reading-measurements`; in Claude Code, request `/reading-measurements`. Ask the
agent to identify the skill's source and explain how it would report a command
that exits successfully while collecting no tests.

Discovery and a reasonable explanation do not prove future compliance. Try a
[behavioral scenario](../evals/README.md) as well.

If the skill is missing, check that the installed layout is
`<skill-root>/reading-measurements/SKILL.md`, that your session can access it, and
that skill loading is enabled by the host. Other agents can read the Markdown
directly, but this repository does not claim automatic discovery for every agent.

## Update copies without losing edits

Review and fetch the desired upstream changes in the source clone first. To
upgrade copies previously made by this installer, including expanding an older
installation to the complete workflow:

```bash
python tools/install_skills.py --project ../my-project --agent codex --profile workflow --update --dry-run
```

Inspect the plan, then omit `--dry-run`. Existing selected skills must have valid
installer provenance and match every recorded file hash. Modified, missing or
extra files are refused, as are links and unrelated folders. An edited skill must
be reconciled manually; there is no force-overwrite flag. New selections can be
installed in the same run. Existing project instructions and unselected skills
stay untouched.

Replaced folders are retained under the target project's
`.local/done-is-a-claim/backups/`; the command prints their locations. Treat backups
as local material and exclude that directory from version control according to
your project's conventions. The installer does not edit your ignore rules.
Inspect a retained folder before manually restoring it to its exact former
destination; preserve the current copy separately rather than merging blindly.

All selections are checked and staged before replacement, and destinations are
checked again during publication. This is not an atomic transaction across
multiple folders or a lock against concurrent writers. On an interrupted or failed
run, inspect the reported installed paths and retained backups before retrying.
Do not run two installers against the same destination at once.

The provenance manifest and hashes are editable local records, not signatures.
They help detect drift relative to the manifest; they cannot authenticate a
package against an attacker who can rewrite both files and provenance.

## Remove

This repository installs no background updater. To remove a skill, remove only the specific folder you copied;
do not delete the entire shared skills directory. Remove or revise the rules you
merged into your project independently.

## Official references

Installation paths and instruction behavior checked on 2026-10-10:

- [OpenAI: local skill locations](https://learn.chatgpt.com/docs/build-skills)
- [Claude Code: skills](https://code.claude.com/docs/en/skills)
- [Claude Code: project instructions and imports](https://code.claude.com/docs/en/memory)
