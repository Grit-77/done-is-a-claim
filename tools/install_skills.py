#!/usr/bin/env python3
"""Install selected skills or profiles into an existing project.

Uses only the standard library; no network, global installs or instruction merges.
Preflight rejects links and collisions. This is not protection against malicious
concurrent filesystem changes. An interrupted publish can leave a partial install,
which is reported and never automatically removed. Explicit --update replaces
only unchanged copies with valid installer provenance and retains their backups.
Provenance is an unsigned integrity manifest, not proof of authenticity.
--json emits one schema-versioned object on stdout for list, plan, success and
operational failure; diagnostics may appear on stderr. Argument usage errors
retain argparse's standard stderr output and exit code 2 without a JSON report.
"""

import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import sys
import uuid


SOURCE_REPOSITORY = "https://github.com/Grit-77/done-is-a-claim"
AGENT_FOLDERS = {"codex": ".agents", "claude-code": ".claude"}
CAPABILITIES = {
    "using-done-is-a-claim": "Choose the relevant workflow for your task.",
    "planning-changes": "Plan a change with clear scope and checks.",
    "executing-plans": "Carry a plan through edits, checks and review.",
    "debugging-with-evidence": "Investigate a failure using a reproduction and evidence.",
    "reviewing-changes": "Review a change against your requirements.",
    "acceptance-design": "Define a check that can show whether the task worked.",
    "reading-measurements": "Check what a number or test result actually shows.",
    "whose-red": "Compare a failing change with its baseline.",
    "evidence-freshness": "Check that evidence matches the current inputs.",
    "public-claims": "Check public claims against their sources.",
    "checking-delivery": "Verify the result at its delivery destination.",
    "collecting-worker-results": "Inspect a worker's files and evidence before accepting them.",
    "resuming-work": "Resume work from a checkpoint and current files.",
}


def install_report(root, args):
    """Schema 1: paths and counts describe this operation, never activation."""
    version = None
    try:
        metadata_path = root / "plugin.json"
        reject_links(metadata_path)
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"), object_pairs_hook=unique_object)
        if isinstance(metadata, dict) and isinstance(metadata.get("version"), str):
            version = metadata["version"] or None
    except (OSError, ValueError, UnicodeError):
        pass  # Archives and test fixtures need not carry plugin metadata.
    revision = source_revision(root)
    return {
        "schema_version": 1, "state": "failed",
        "operation": "list" if args.list else "update" if args.update else "install",
        "project": str(args.project.absolute()) if args.project is not None else None,
        "agents": list(dict.fromkeys(args.agent or [])),
        "skills": list(dict.fromkeys(args.skill)), "profiles": list(dict.fromkeys(args.profile)),
        "source": {"repository": SOURCE_REPOSITORY, "version": version,
                   "revision": None if revision == "unknown" else revision},
        "available_skills": [], "available_profiles": {}, "planned": [],
        "copied_count": 0, "updated_count": 0, "installed_paths": [],
        "backups": [], "incomplete_path": None, "error": None,
        "staging": None,
        "instructions_changed": False, "activated": False,
        "capabilities": [], "next_step": None,
    }


def print_install_summary(report):
    """Keep the original path lines and explain the effect of copying skills."""
    for destination in report["installed_paths"]:
        print(f"Installed: {destination}")
    for backup in report["backups"]:
        print(f"Backup for {backup['destination']}: {backup['path']}")
    print(f"Copied {report['copied_count']} new skill folders; updated {report['updated_count']} existing folders.")
    print("Project instructions (AGENTS.md / CLAUDE.md) and agent settings were not changed.")
    print("This installed skill files; activation in an agent session has not been verified.")
    print("What you can use:")
    for capability in report["capabilities"]:
        print(f"  {capability['skill']}: {capability['description']}")
    print(f"Next step: {report['next_step']}")


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def load_profiles(root):
    path = root / "profiles.json"
    reject_links(path)
    profiles = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_object)
    if not isinstance(profiles, dict) or any(
        not valid_name(name) or not isinstance(members, list) or not members
        or any(not valid_name(member) for member in members)
        for name, members in profiles.items()
    ):
        raise ValueError("Invalid profiles.json: expected profile names mapped to skill-name lists")
    return profiles


def valid_name(name):
    return isinstance(name, str) and re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name)


def check_destination(project, destination):
    reject_links(destination)
    if not destination.resolve().is_relative_to(project):
        raise ValueError(f"Destination escapes project: {destination}")
    for ancestor in destination.parents:
        if ancestor == project:
            break
        if ancestor.exists() and not ancestor.is_dir():
            raise ValueError(f"Destination ancestor is not a directory: {ancestor}")


def installed_state(destination, name):
    """Verify the exact legacy manifest/tree; return a snapshot for rechecks."""
    reject_links(destination)
    if not destination.is_dir():
        raise ValueError(f"Update requires an installed directory: {destination}")
    provenance = destination / "PROVENANCE.json"
    reject_links(provenance)
    try:
        raw = provenance.read_bytes()
        metadata = json.loads(raw, object_pairs_hook=unique_object)
    except (OSError, ValueError, UnicodeError) as error:
        raise ValueError(f"Invalid installer provenance: {provenance}: {error}") from error
    keys = {"source_repository", "source_revision", "skill", "files_sha256"}
    if (not isinstance(metadata, dict) or set(metadata) != keys
            or metadata["source_repository"] != SOURCE_REPOSITORY or metadata["skill"] != name
            or not isinstance(metadata["source_revision"], str)
            or not re.fullmatch(r"unknown|[0-9a-fA-F]{40}|[0-9a-fA-F]{64}", metadata["source_revision"])):
        raise ValueError(f"Unknown or malformed installer provenance: {provenance}")
    hashes = metadata["files_sha256"]
    if not isinstance(hashes, dict) or not {"SKILL.md", "LICENSE"}.issubset(hashes):
        raise ValueError(f"Invalid provenance file manifest: {provenance}")
    expected_dirs = set()
    aliases = set()
    for path, digest in hashes.items():
        parts = path.split("/")
        if (any(not part or part in (".", "..") or part.endswith((".", " "))
                or re.search(r'[\\:*?"<>|\x00-\x1f]', part)
                or re.fullmatch(r"(?i)(?:con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?", part)
                for part in parts)
                or path.casefold() == "provenance.json" or path.casefold() in aliases
                or not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest)):
            raise ValueError(f"Invalid provenance path or hash: {path!r}")
        aliases.add(path.casefold())
        expected_dirs.update("/".join(parts[:index]) for index in range(1, len(parts)))
    actual = {}
    actual_dirs = set()
    for item in destination.rglob("*"):
        reject_links(item)
        relative = item.relative_to(destination).as_posix()
        mode = item.lstat().st_mode
        if stat.S_ISDIR(mode):
            actual_dirs.add(relative)
        elif stat.S_ISREG(mode):
            if relative != "PROVENANCE.json":
                actual[relative] = hashlib.sha256(item.read_bytes()).hexdigest()
        else:
            raise ValueError(f"Unsupported installed entry: {item}")
    if actual != hashes or actual_dirs != expected_dirs:
        raise ValueError(f"Installed content modified, missing or untracked: {destination}")
    return raw, actual, actual_dirs


def reject_links(path):
    """Check lexical ancestors before resolve can hide a link or junction."""
    for part in (path, *path.parents):
        try:
            info = part.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
            raise ValueError(f"Symlink or junction is not allowed: {part}")


def source_revision(root):
    """Read Git HEAD locally, including worktrees, without invoking Git."""
    try:
        git = root / ".git"
        if git.is_file():
            line = git.read_text(encoding="utf-8").strip()
            if not line.startswith("gitdir: "):
                return "unknown"
            git = (root / line[8:]).resolve()
        head = (git / "HEAD").read_text(encoding="ascii").strip()
        if head.startswith("ref: "):
            ref = head[5:]
            if not re.fullmatch(r"refs/[A-Za-z0-9._/-]+", ref) or ".." in ref:
                return "unknown"
            common_file = git / "commondir"
            common = (git / common_file.read_text().strip()).resolve() if common_file.is_file() else git
            loose = common / ref
            if loose.is_file():
                head = loose.read_text(encoding="ascii").strip()
            else:
                head = "unknown"
                for line in (common / "packed-refs").read_text(encoding="ascii").splitlines():
                    fields = line.split()
                    if len(fields) == 2 and fields[1] == ref:
                        head = fields[0]
                        break
        return head if re.fullmatch(r"[0-9a-fA-F]{40}|[0-9a-fA-F]{64}", head) else "unknown"
    except (OSError, UnicodeError):
        return "unknown"


def preflight(root, project, agents, skills, update=False):
    # Preserve ".." until link checks: normalizing first can hide an ancestor.
    project = project.absolute()
    reject_links(project)
    if not project.is_dir():
        raise ValueError(f"Project must be an existing directory: {project}")
    project = project.resolve()
    license_file = root / "LICENSE"
    reject_links(license_file)
    if not license_file.is_file():
        raise ValueError("Source repository LICENSE is missing")
    selections = []
    for name in dict.fromkeys(skills):
        if not valid_name(name):
            raise ValueError(f"Invalid skill name: {name!r}")
        source = root / "skills" / name
        reject_links(source)
        if not source.is_dir() or not (source / "SKILL.md").is_file():
            raise ValueError(f"Skill folder with SKILL.md does not exist: {name}")
        for item in source.rglob("*"):
            reject_links(item)
            if not item.is_file() and not item.is_dir():
                raise ValueError(f"Unsupported source entry: {item}")
            # The legacy provenance records files, so every copied directory
            # must be implied by a file path for an unchanged copy to update.
            if item.is_dir() and next(item.iterdir(), None) is None:
                raise ValueError(f"Source empty directory cannot be tracked by provenance: {item}")
        for reserved in ("LICENSE", "PROVENANCE.json"):
            if os.path.lexists(source / reserved):
                raise ValueError(f"Skill uses reserved installer filename: {name}/{reserved}")
        for agent in dict.fromkeys(agents):
            destination = project / AGENT_FOLDERS[agent] / "skills" / name
            # lexists catches dangling links as well as files and directories.
            exists = os.path.lexists(destination)
            if exists and not update:
                raise ValueError(f"Destination already exists: {destination}")
            check_destination(project, destination)
            state = installed_state(destination, name) if exists else None
            selections.append((name, source, destination, state))
    if any(state is not None for _, _, _, state in selections):
        check_destination(project, project / ".local/done-is-a-claim/backups" / "preflight")
    return project, selections


def checked_staging_root(project, scratch, identity):
    check_destination(project, scratch)
    current = scratch.lstat()
    if (not stat.S_ISDIR(current.st_mode) or (current.st_dev, current.st_ino) != identity
            or scratch.resolve(strict=True).parent != project):
        raise ValueError(f"Staging directory identity or containment changed: {scratch}")


def checked_staged_entry(scratch, path, known):
    reject_links(path)
    relative = path.relative_to(scratch).as_posix()
    if relative not in known or not path.resolve(strict=True).is_relative_to(scratch):
        raise ValueError(f"Unexpected staging contents; retained: {path}")
    metadata = path.lstat()
    expected = known[relative]
    if expected is None:
        matches = stat.S_ISDIR(metadata.st_mode)
    else:
        matches = stat.S_ISREG(metadata.st_mode) and hashlib.sha256(path.read_bytes()).hexdigest() == expected
    if not matches:
        raise ValueError(f"Staging content changed or has unsupported type; retained: {path}")
    return metadata


@contextmanager
def staging_directory(project, status):
    """Inherit project permissions; delete only identified, unchanged stage data."""
    scratch = project / (".skill-install-" + uuid.uuid4().hex)
    check_destination(project, scratch)
    scratch.mkdir()  # exclusive ordinary mkdir, preserving normal ACL inheritance
    identity = None
    known = {}
    try:  # cleanup registered immediately after successful creation
        status.update(path=str(scratch), removed=False, retained_path=str(scratch), error=None)
        reject_links(scratch)
        original = scratch.lstat()
        identity = original.st_dev, original.st_ino
        yield scratch, known
    finally:
        try:
            checked_staging_root(project, scratch, identity)
            # Survey the entire tree before deleting anything. Reject unknown
            # names, altered bytes and links before descending into directories.
            pending = list(scratch.iterdir())
            entries = []
            while pending:
                path = pending.pop()
                checked_staging_root(project, scratch, identity)
                metadata = checked_staged_entry(scratch, path, known)
                entries.append((path, metadata.st_dev, metadata.st_ino))
                if stat.S_ISDIR(metadata.st_mode):
                    pending.extend(path.iterdir())
            for path, device, inode in sorted(entries, key=lambda entry: len(entry[0].parts), reverse=True):
                checked_staging_root(project, scratch, identity)
                current = checked_staged_entry(scratch, path, known)
                if (current.st_dev, current.st_ino) != (device, inode):
                    raise ValueError(f"Staging entry identity changed; retained: {path}")
                if stat.S_ISDIR(current.st_mode):
                    path.rmdir()  # only empty known directories, never recursive deletion
                else:
                    path.unlink()
            checked_staging_root(project, scratch, identity)
            scratch.rmdir()
            status.update(removed=True, retained_path=None)
        except (OSError, ValueError) as error:
            status["error"] = str(error)


def install(root, project, selections, report=None):
    installed = []
    backups = []
    incomplete = None
    staging_status = {}
    try:
        # Stage every copy before publishing any selection. Cleanup owns only
        # this generated staging directory, never a destination or user file.
        with staging_directory(project, staging_status) as (temporary, known):
            staged = []
            revision = source_revision(root)
            if report is not None:
                report["source"]["revision"] = None if revision == "unknown" else revision
            for index, (name, source, destination, state) in enumerate(selections):
                stage = Path(temporary) / str(index)
                known[str(index)] = None
                for item in source.rglob("*"):
                    reject_links(item)
                    relative = (stage / item.relative_to(source)).relative_to(temporary).as_posix()
                    known[relative] = None if item.is_dir() else hashlib.sha256(item.read_bytes()).hexdigest()
                known[f"{index}/LICENSE"] = hashlib.sha256((root / "LICENSE").read_bytes()).hexdigest()
                shutil.copytree(source, stage)
                shutil.copyfile(root / "LICENSE", stage / "LICENSE")
                hashes = {item.relative_to(stage).as_posix(): hashlib.sha256(item.read_bytes()).hexdigest()
                          for item in sorted(stage.rglob("*")) if item.is_file()}
                metadata = {"source_repository": SOURCE_REPOSITORY, "source_revision": revision,
                            "skill": name, "files_sha256": hashes}
                provenance = (json.dumps(metadata, indent=2, sort_keys=True) + "\n").encode("utf-8")
                known[f"{index}/PROVENANCE.json"] = hashlib.sha256(provenance).hexdigest()
                (stage / "PROVENANCE.json").write_bytes(provenance)
                staged.append((name, stage, destination, state))
            # Check every destination again after staging, before any publication.
            for name, _, destination, state in staged:
                check_destination(project, destination)
                if state is not None:
                    if installed_state(destination, name) != state:
                        raise ValueError(f"Installed content changed after preflight: {destination}")
                elif os.path.lexists(destination):
                    raise ValueError(f"Destination already exists: {destination}")
            backup_run = None
            for name, stage, destination, state in staged:
                check_destination(project, destination)
                destination.parent.mkdir(parents=True, exist_ok=True)
                if state is not None:
                    backup_root = project / ".local/done-is-a-claim/backups"
                    check_destination(project, backup_root / "preflight")
                    if backup_run is None:
                        backup_root.mkdir(parents=True, exist_ok=True)
                        backup_run = backup_root / uuid.uuid4().hex
                        backup_run.mkdir()
                    backup = backup_run / (destination.parent.parent.name + "-" + name)
                    # Recheck immediately before moving the user's installed copy.
                    check_destination(project, destination)
                    if installed_state(destination, name) != state:
                        raise ValueError(f"Installed content changed after preflight: {destination}")
                    destination.rename(backup)
                    backups.append((destination, backup))
                # Exclusive creation refuses even a newly appeared empty folder;
                # POSIX rename alone could overwrite such a destination.
                destination.mkdir()
                incomplete = destination
                for item in stage.iterdir():
                    item.rename(destination / item.name)
                installed.append(destination)
                incomplete = None
                if report is not None:
                    report["installed_paths"].append(str(destination))
                    report["updated_count" if state is not None else "copied_count"] += 1
        if staging_status.get("error"):
            raise ValueError(f"Staging cleanup incomplete: {staging_status['error']}")
    except (OSError, ValueError) as error:
        print(f"Install failed: {error}", file=sys.stderr)
        print("Partial status: installed destinations: " + (", ".join(map(str, installed)) or "none"), file=sys.stderr)
        if incomplete is not None:
            print(f"Incomplete destination retained: {incomplete}", file=sys.stderr)
        for destination, backup in backups:
            print(f"Original for {destination} retained at: {backup}", file=sys.stderr)
        if staging_status.get("retained_path"):
            print(f"Staging directory retained: {staging_status['retained_path']}: {staging_status['error']}", file=sys.stderr)
        print("Created directories may remain. Publication is not atomic; no automatic rollback or deletion.", file=sys.stderr)
        if report is not None:
            report["state"] = "failed"
            report["staging"] = staging_status or None
            report["error"] = str(error)
            report["incomplete_path"] = str(incomplete) if incomplete is not None else None
            report["backups"] = [{"destination": str(destination), "path": str(backup)}
                                 for destination, backup in backups]
            completed_skills = {destination.name for destination in installed}
            report["capabilities"] = [item for item in report["capabilities"] if item["skill"] in completed_skills]
        return 1
    if report is not None:
        report["state"] = "installed"
        report["staging"] = staging_status
        report["backups"] = [{"destination": str(destination), "path": str(backup)}
                             for destination, backup in backups]
        entry = "using-done-is-a-claim" if "using-done-is-a-claim" in report["skills"] else report["skills"][0]
        report["next_step"] = f"Start a fresh agent session in this project and ask it to use {entry} for your next task."
        return 0
    for destination in installed:
        print(f"Installed: {destination}")
    for destination, backup in backups:
        print(f"Backup for {destination}: {backup}")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, help="existing project directory")
    parser.add_argument("--agent", choices=AGENT_FOLDERS, action="append")
    parser.add_argument("--skill", action="append", default=[], help="explicit source skill folder name; repeat to select more")
    parser.add_argument("--profile", action="append", default=[], help="named profile; repeat and combine with --skill")
    parser.add_argument("--list", action="store_true", help="list source skills and profiles without a target or writes")
    parser.add_argument("--update", action="store_true", help="replace unchanged installer copies; retain originals in project backups")
    parser.add_argument("--dry-run", action="store_true", help="preflight and print destinations without writes")
    parser.add_argument("--json", action="store_true", help="emit one schema 1 JSON report; argument usage errors remain standard argparse errors")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    report = install_report(root, args)
    try:
        if args.list or args.profile:
            profiles = load_profiles(root)
        if args.list:
            if args.project or args.agent or args.skill or args.profile or args.update or args.dry_run:
                parser.error("--list cannot be combined with installation options")
            for path in sorted((root / "skills").iterdir()):
                reject_links(path)
                if path.is_dir() and (path / "SKILL.md").is_file():
                    report["available_skills"].append(path.name)
            report["available_profiles"] = profiles
            report["state"] = "listed"
            if args.json:
                print(json.dumps(report))
            else:
                print("Skills:")
                for name in report["available_skills"]:
                    print(f"  {name}")
                print("Profiles:")
                for name, members in profiles.items():
                    print(f"  {name}: {', '.join(members)}")
            return 0
        if args.project is None or not args.agent or not (args.skill or args.profile):
            parser.error("installation requires --project, --agent and --skill or --profile")
        skills = list(args.skill)
        for profile in args.profile:
            if profile not in profiles:
                raise ValueError(f"Unknown profile: {profile}")
            skills.extend(profiles[profile])
        report["skills"] = list(dict.fromkeys(skills))
        project, selections = preflight(root, args.project, args.agent, skills, args.update)
        report["project"] = str(project)
        report["planned"] = [{"skill": name,
                              "agent": next(agent for agent, folder in AGENT_FOLDERS.items()
                                            if folder == destination.parent.parent.name),
                              "path": str(destination), "action": "update" if state is not None else "install"}
                             for name, _, destination, state in selections]
        report["capabilities"] = [{"skill": name, "description": CAPABILITIES.get(
            name, f"Use the {name} skill's instructions when requested.")} for name in report["skills"]]
    except (OSError, ValueError) as error:
        print(f"Preflight failed: {error}", file=sys.stderr)
        report["error"] = str(error)
        if args.json:
            print(json.dumps(report))
        return 1
    if args.dry_run:
        report["state"] = "planned"
        if args.json:
            print(json.dumps(report))
        else:
            for _, _, destination, state in selections:
                print(f"Would {'update' if state is not None else 'install'}: {destination}")
        return 0
    result = install(root, project, selections, report)
    if args.json:
        print(json.dumps(report))
    elif result == 0:
        print_install_summary(report)
    return result


if __name__ == "__main__":
    raise SystemExit(main())
