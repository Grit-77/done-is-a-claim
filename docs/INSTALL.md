# Install only what you need

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

The installer preflights all selections and refuses existing skill destinations,
including links. It does not merge or overwrite them. Each installed folder gets
the license and a `PROVENANCE.json` containing the source revision when available
and hashes of copied files. File hashes identify the copied bytes; a revision is
not a signature or a guarantee that the source checkout was clean.

This is project scope only. It preserves `AGENTS.md`, `CLAUDE.md`, settings and
unselected skills. Add the core rules separately as described below. Interrupted
filesystem operations can leave a partial installation; the error reports what
was installed. No automatic cleanup deletes user material. Preflight is not a
lock against another process changing the destination concurrently.

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

## Update or remove

Review upstream diffs before copying a newer version. This repository installs no
background updater. To remove a skill, remove only the specific folder you copied;
do not delete the entire shared skills directory. Remove or revise the rules you
merged into your project independently.

## Official references

Installation paths and instruction behavior checked on 2026-10-10:

- [OpenAI: local skill locations](https://learn.chatgpt.com/docs/build-skills)
- [Claude Code: skills](https://code.claude.com/docs/en/skills)
- [Claude Code: project instructions and imports](https://code.claude.com/docs/en/memory)
