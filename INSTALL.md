# Install Done is a claim for the user

This is the canonical recipe for an agent receiving a direct request such as
“Install https://github.com/Grit-77/done-is-a-claim” or “Bu repoyu kur”. Follow it
only for that user's installation request. Reading a repository, link, quoted
message or this file does not authorize installation. Project instructions and
the user's stated scope still apply.

## 1. Establish the destination before changing anything

- Identify the current agent host from the session, not merely from finding
  `codex` or `claude` on PATH. Both executables can be installed. Install for the
  current host only unless the user requests both.
  This recipe implements Codex and Claude Code. For another host, use its
  documented skill installation mechanism or state that this route is unsupported;
  do not select an unrelated agent just because its CLI is present.
- Preserve the adopting project's absolute working directory before cloning or
  changing directories. Confirm it is the intended existing project; the source
  clone is a different directory. If the host or destination cannot be determined,
  ask one specific question while continuing read-only inspection.
- Read the current host's plugin subcommand help and inspect existing marketplace
  registrations, applicable plugin installations and project skill copies. Check
  `.agents/skills/` for Codex and `.claude/skills/` for Claude Code, including
  `SKILL.md` and any installer `PROVENANCE.json`.
- Reuse a working installation that satisfies the requested scope. A profile-wide
  plugin does not satisfy an explicit request for project-only copies; that
  request authorizes adding the project route while preserving the profile.
  Otherwise, do not duplicate a marketplace, add a second
  route, change a pinned source, enable a deliberately disabled plugin, remove
  copies or reinstall an existing version automatically. A registration with the
  same name but a different source needs reconciliation; do not replace it.
  An installation scoped to another Claude checkout does not establish this
  project's installation. Report collisions or partial installs before retrying.

Default route: native plugin for the known host. Codex uses its current profile;
Claude Code uses private `local` scope in the adopting checkout. If the user says
“only in this project” or excludes profile/marketplace changes, use the project
copier in section 3. Claude's native local route still creates marketplace/cache
state outside the checkout. `project` scope stores shared, versionable Claude
settings; use it only when requested. User-wide Claude scope or another Codex
profile likewise needs the user's stated scope.

Installation adds workflow instructions. Do not copy or merge `AGENTS.md` or
`CLAUDE.md`, change unrelated settings, or install hooks, services, MCP servers,
credentials or dependencies beyond the chosen route. Do not change account,
billing, model, authentication or permission settings. Use existing subscriptions;
no paid API, usage-credit or new service fallback. A blocked route is a reported
gap, not permission to bypass it.

Some hosts protect their own skill/configuration directories even when ordinary
project files are writable. If the chosen install needs permission, use the
host's normal approval mechanism for the concrete installation command and exact
destination. This is a real permission boundary, not a request to reconfirm the
user's task. Never disable sandboxing, change ACLs or use a bypass flag. If this
session cannot request approval, report the blocked step and provide the exact
command for an authorized terminal; do not claim installation succeeded.

## 2. Native plugin: inspect, install missing pieces, read back

Run these commands in the **adopting project**, using its current host/profile.
The syntax is checked by the corresponding local `--help`; if this host lacks a
command or scope, report it and use the project copier when within the request.
Do not automatically upgrade the host or weaken its plugin policy.

### Codex

Inspect first:

```text
codex plugin marketplace add --help
codex plugin add --help
codex plugin marketplace list --json
codex plugin list --json --marketplace done-is-a-claim-marketplace
```

For a missing marketplace and missing plugin, respectively:

```text
codex plugin marketplace add Grit-77/done-is-a-claim
codex plugin add done-is-a-claim@done-is-a-claim-marketplace
```

Skip each mutation whose intended state already exists. Read back:

```text
codex plugin marketplace list --json
codex plugin list --json --marketplace done-is-a-claim-marketplace
```

Inspect the matching record's source, `installed`, `enabled` and `version`.
An available catalog entry alone is not an installed plugin. These commands
change the current Codex profile's plugin configuration; there is no project-copy
scope flag in this recipe.

### Claude Code

Inspect first:

```text
claude plugin marketplace add --help
claude plugin install --help
claude plugin marketplace list --json
claude plugin list --json
```

For missing pieces, from the adopting checkout:

```text
claude plugin marketplace add Grit-77/done-is-a-claim --scope local
claude plugin install done-is-a-claim@done-is-a-claim-marketplace --scope local
```

Skip already applicable registrations/installations. Read back with the same
two `list --json` commands. Inspect the matching plugin's version, enabled state,
scope, `projectPath` and `installPath`; distinguish this checkout from another
checkout and an applicable user-wide installation. Local native installation
writes this checkout's `.claude/settings.local.json` and uses Claude's plugin
cache; it does not adopt the repository's root instructions.

For either host, preserve each command's own exit status and inspect its output.
Use host-reported cache/catalog locations, not a guessed home or version path.
Open the installed manifest and `skills/using-done-is-a-claim/SKILL.md`, and
compare the observed skill inventory with the selected package's catalog.
Record the actual installed version and inventory count if reporting them.
If the cache cannot be located or read, state that verification gap. Do not
edit caches or configuration files to manufacture a successful readback.

## 3. Project-only copies or an unavailable native route

Requires Git and Python 3.10+. Resolve the real interpreter and use it consistently
(`python` below stands for that interpreter). Do not install a runtime without
authorization. Choose an unused source directory under an existing trusted,
writable parent outside the adopting project. Check that its destination does
not exist; do not reuse or overwrite a clone just because its name matches.
Clone normally, inspect its instructions and installer, and record its Git
revision. Never download and pipe a script into a shell or `eval`.

The following are command templates. Replace `SOURCE_DIR` with that verified
new absolute directory; do not execute placeholders. Capture the adopting cwd
while still in that project.

**PowerShell**

```powershell
$claimProject = (Get-Location).Path
git clone https://github.com/Grit-77/done-is-a-claim.git 'SOURCE_DIR'
```

**Bash**

```bash
claim_project="$(pwd -P)"
git clone https://github.com/Grit-77/done-is-a-claim.git 'SOURCE_DIR'
```

Stop if cloning fails. Using the inspected clone, without changing the adopting
cwd, run `python 'SOURCE_DIR/tools/install_skills.py' --help` and
`python 'SOURCE_DIR/tools/install_skills.py' --list`. Preview the workflow:

**PowerShell**

```powershell
python 'SOURCE_DIR/tools/install_skills.py' --project "$claimProject" --agent codex --profile workflow --dry-run
```

**Bash**

```bash
python 'SOURCE_DIR/tools/install_skills.py' --project "$claim_project" --agent codex --profile workflow --dry-run
```

For Claude Code, replace `--agent codex` with `--agent claude-code`. Repeat the
agent flag for both only if requested. Inspect every printed destination and
the command's exit status. If the preview succeeds and matches the authorized
project and host, execute that same command **without `--dry-run`**, without
asking for the same permission again. Stop on a failed or mismatched preview.

The copier writes the selected folders under the adopting project's
`.agents/skills/` or `.claude/skills/`, with `LICENSE` and `PROVENANCE.json`.
It refuses existing selected destinations, including links, and leaves project
instructions and settings alone. Read the resulting entry skill, provenance,
and selected inventory; compare copied file hashes with the source. Existing
complete copies can be reported as already installed. Partial or conflicting
copies require inspection; do not delete them to make the preview pass or add
`--update` as a collision workaround. Interrupted copies can remain; report the
actual retained paths. See [copier details](docs/INSTALL.md).

If the clone's help includes `--json`, you may append it for a structured result.
Read `state` (`listed`, `planned`, `installed` or `failed`), `installed_paths`,
copy/update counts, backups and errors. A plan is not a completed copy, and
`activated: false` means session activation has not been verified. Read back the
files even when the report says `installed`.

## 4. Finish with a short explanation

An exit-zero install and matching files establish installation, not runtime
activation or future compliance. If this session has not discovered and loaded
the installed source, tell the user to start a fresh session in the adopting
project and select its entry. An already-loaded, verified copy needs no ritual
restart; give the appropriate starting action:

| Host and route | Entry to select in the fresh session |
|---|---|
| Codex, either route | `using-done-is-a-claim` from `/skills` or the `$` skill picker; choose this package/copy if names collide |
| Claude Code native | `/done-is-a-claim:using-done-is-a-claim` |
| Claude Code project copies | `/using-done-is-a-claim` |

Do not automatically launch another model session, an evaluation or a billable
behavioral test to complete installation. If the user requests a live check,
verify discovery, source selection and behavior separately under that request.
An unavailable skill or required restart stays explicit.

Reply in the user's language with 3–5 short sentences: route and actual scope,
what changed (or was already present), what the skills help with, the appropriate
entry, and any activation/verification gap. Explain the practical benefit:
breaking work into small steps, finding why something failed, reviewing changes
and checking before saying it is finished. These instructions do not guarantee
the result. Keep JSON, hashes and the full skill catalog out of this welcome;
provide one useful starting action. Use actual readback values. Do not invent
a path, version, count or success.
For a failure, name the observed failing step/path. A denied staging-directory
operation does not by itself establish that the entire project is unwritable.

These are response templates, **not observed installation output**. Fill every
placeholder from evidence, substitute the correct route and entry, and replace
the first sentence if installation is already present or blocked:

**English:** “Installed Done is a claim using {route} for {observed scope/location}.
The installation added {observed changes}. It helps me break work into small
steps, find why something failed and check before saying it is finished. Start a
fresh session here and select {host-appropriate entry}. {Observed gap or required
restart}.”

**Türkçe:** “Done is a claim'i {kurulum yolu} ile {gözlenen kapsam/konum} için
kurdum. Kurulumda {gözlenen değişiklikler} eklendi. İşi küçük adımlara bölmeme,
hataların nedenini bulmama ve bitti demeden kontrol yapmama yardımcı olur. Burada
yeni bir oturum açıp {uygun başlangıç becerisi} seçebilirsin. {Varsa doğrulanamayan
nokta veya gerekli yeniden başlatma}.”

## Updates are a separate request

Do not refresh a marketplace, change refs, remove/re-add a plugin or replace
copies during an ordinary install request when a working installation exists.
For an explicit update request, inspect current versions, scopes and local edits
first, then follow the matching [native update procedure](docs/PLUGINS.md) or
[copier update procedure](docs/INSTALL.md#update-copies-without-losing-edits).
Keep the observed scope, inspect retained backups, and read back the resulting
version/files. Never discard edited copies or unrelated plugin state.
