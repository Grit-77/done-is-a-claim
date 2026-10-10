#!/usr/bin/env python3
"""Install explicitly selected skills into an existing project, without overwrite.

Uses only the standard library; no network, global installs or instruction merges.
Preflight rejects links and collisions. This is not protection against malicious
concurrent filesystem changes. An interrupted publish can leave a partial install,
which is reported and never automatically removed.
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


SOURCE_REPOSITORY = "https://github.com/Grit-77/done-is-a-claim"
AGENT_FOLDERS = {"codex": ".agents", "claude-code": ".claude"}


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


def preflight(root, project, agents, skills):
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
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
            raise ValueError(f"Invalid skill name: {name!r}")
        source = root / "skills" / name
        reject_links(source)
        if not source.is_dir() or not (source / "SKILL.md").is_file():
            raise ValueError(f"Skill folder with SKILL.md does not exist: {name}")
        for item in source.rglob("*"):
            reject_links(item)
            if not item.is_file() and not item.is_dir():
                raise ValueError(f"Unsupported source entry: {item}")
        for reserved in ("LICENSE", "PROVENANCE.json"):
            if os.path.lexists(source / reserved):
                raise ValueError(f"Skill uses reserved installer filename: {name}/{reserved}")
        for agent in dict.fromkeys(agents):
            destination = project / AGENT_FOLDERS[agent] / "skills" / name
            # lexists catches dangling links as well as files and directories.
            if os.path.lexists(destination):
                raise ValueError(f"Destination already exists: {destination}")
            reject_links(destination)
            if not destination.resolve().is_relative_to(project):
                raise ValueError(f"Destination escapes project: {destination}")
            for ancestor in destination.parents:
                if ancestor == project:
                    break
                if ancestor.exists() and not ancestor.is_dir():
                    raise ValueError(f"Destination ancestor is not a directory: {ancestor}")
            selections.append((name, source, destination))
    return project, selections


def install(root, project, selections):
    installed = []
    incomplete = None
    try:
        # Stage every copy before publishing any selection. Cleanup owns only
        # this generated staging directory, never a destination or user file.
        with tempfile.TemporaryDirectory(prefix=".skill-install-", dir=project) as temporary:
            staged = []
            revision = source_revision(root)
            for index, (name, source, destination) in enumerate(selections):
                stage = Path(temporary) / str(index)
                shutil.copytree(source, stage)
                shutil.copyfile(root / "LICENSE", stage / "LICENSE")
                hashes = {item.relative_to(stage).as_posix(): hashlib.sha256(item.read_bytes()).hexdigest()
                          for item in sorted(stage.rglob("*")) if item.is_file()}
                metadata = {"source_repository": SOURCE_REPOSITORY, "source_revision": revision,
                            "skill": name, "files_sha256": hashes}
                (stage / "PROVENANCE.json").write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
                staged.append((stage, destination))
            for stage, destination in staged:
                reject_links(destination)
                destination.parent.mkdir(parents=True, exist_ok=True)
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
        print("Created parent directories may remain; no destination was deleted.", file=sys.stderr)
        return 1
    for destination in installed:
        print(f"Installed: {destination}")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True, help="existing project directory")
    parser.add_argument("--agent", choices=AGENT_FOLDERS, action="append", required=True)
    parser.add_argument("--skill", action="append", required=True, help="explicit source skill folder name; repeat to select more")
    parser.add_argument("--dry-run", action="store_true", help="preflight and print destinations without writes")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    try:
        project, selections = preflight(root, args.project, args.agent, args.skill)
    except (OSError, ValueError) as error:
        print(f"Preflight failed: {error}", file=sys.stderr)
        return 1
    if args.dry_run:
        for _, _, destination in selections:
            print(f"Would install: {destination}")
        return 0
    return install(root, project, selections)


if __name__ == "__main__":
    raise SystemExit(main())
