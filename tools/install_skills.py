#!/usr/bin/env python3
"""Install selected skills or profiles into an existing project.

Uses only the standard library; no network, global installs or instruction merges.
Preflight rejects links and collisions. This is not protection against malicious
concurrent filesystem changes. An interrupted publish can leave a partial install,
which is reported and never automatically removed. Explicit --update replaces
only unchanged copies with valid installer provenance and retains their backups.
Provenance is an unsigned integrity manifest, not proof of authenticity.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import sys
import tempfile
import uuid


SOURCE_REPOSITORY = "https://github.com/Grit-77/done-is-a-claim"
AGENT_FOLDERS = {"codex": ".agents", "claude-code": ".claude"}


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


def install(root, project, selections):
    installed = []
    backups = []
    incomplete = None
    try:
        # Stage every copy before publishing any selection. Cleanup owns only
        # this generated staging directory, never a destination or user file.
        with tempfile.TemporaryDirectory(prefix=".skill-install-", dir=project) as temporary:
            staged = []
            revision = source_revision(root)
            for index, (name, source, destination, state) in enumerate(selections):
                stage = Path(temporary) / str(index)
                shutil.copytree(source, stage)
                shutil.copyfile(root / "LICENSE", stage / "LICENSE")
                hashes = {item.relative_to(stage).as_posix(): hashlib.sha256(item.read_bytes()).hexdigest()
                          for item in sorted(stage.rglob("*")) if item.is_file()}
                metadata = {"source_repository": SOURCE_REPOSITORY, "source_revision": revision,
                            "skill": name, "files_sha256": hashes}
                (stage / "PROVENANCE.json").write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
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
    except (OSError, ValueError) as error:
        print(f"Install failed: {error}", file=sys.stderr)
        print("Partial status: installed destinations: " + (", ".join(map(str, installed)) or "none"), file=sys.stderr)
        if incomplete is not None:
            print(f"Incomplete destination retained: {incomplete}", file=sys.stderr)
        for destination, backup in backups:
            print(f"Original for {destination} retained at: {backup}", file=sys.stderr)
        print("Created directories may remain. Publication is not atomic; no automatic rollback or deletion.", file=sys.stderr)
        return 1
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
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    try:
        if args.list or args.profile:
            profiles = load_profiles(root)
        if args.list:
            if args.project or args.agent or args.skill or args.profile or args.update or args.dry_run:
                parser.error("--list cannot be combined with installation options")
            print("Skills:")
            for path in sorted((root / "skills").iterdir()):
                reject_links(path)
                if path.is_dir() and (path / "SKILL.md").is_file():
                    print(f"  {path.name}")
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
        project, selections = preflight(root, args.project, args.agent, skills, args.update)
    except (OSError, ValueError) as error:
        print(f"Preflight failed: {error}", file=sys.stderr)
        return 1
    if args.dry_run:
        for _, _, destination, state in selections:
            print(f"Would {'update' if state is not None else 'install'}: {destination}")
        return 0
    return install(root, project, selections)


if __name__ == "__main__":
    raise SystemExit(main())
