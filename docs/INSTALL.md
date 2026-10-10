# Install only what you need

Clone this repository somewhere separate from the project you want to work on:

```bash
git clone https://github.com/Grit-77/done-is-a-claim.git
```

## Rules

Copy `AGENTS.md` from the clone to your project's root. If the project already has
instructions, merge the relevant rules into them; preserve its commands, scope
and conventions. Do not replace the project's context with this generic file.

For Claude Code, the included `CLAUDE.md` imports `@AGENTS.md`. If your project
already has a `CLAUDE.md`, add the import there instead of replacing it. Current
Claude Code versions can also read `AGENTS.md` directly under their configured
instruction policy; the explicit import remains useful for compatible setups.

## Optional skills

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
