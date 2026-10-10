#!/usr/bin/env python3
"""Record a command's local evidence using Python 3.10+ and the standard library.

Usage: python tools/receipt.py [--cwd PATH] [--input RELATIVE_FILE ...]
       [--output-dir PATH] -- COMMAND ARGS...
Relative output directories are resolved against cwd; default: .local/receipts.
Exit 3 means a successful child changed selected inputs or Git HEAD. Child
exit zero with lost Git observations returns 4 (evidence_incomplete). Windows
.bat/.cmd commands, including PATH/PATHEXT matches, are refused. Explicit shell
commands manage their own quoting; their exit is recorded as opaque evidence.
failures keep exits 1..255; signals map to 128+signal (capped at 255), other
nonportable exits map to 1. Setup/execution errors return 2. The JSON preserves
the child's actual exit code. This is evidence capture, not a test verdict.
"""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def input_snapshot(cwd, selected):
    """Follow only regular files within cwd; do not hash an escaped target."""
    try:
        relative = Path(selected)
        if relative.is_absolute() or relative.drive or relative.root:
            return {"status": "invalid", "error": "input must be relative to cwd"}
        path = (cwd / relative).resolve(strict=True)
        if not path.is_relative_to(cwd):
            return {"status": "outside", "error": "input resolves outside cwd"}
        if not stat.S_ISREG(path.stat().st_mode):
            return {"status": "not_regular", "error": "input must be a regular file"}
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
        return {"status": "present", "resolved_path": str(path), "sha256": digest.hexdigest()}
    except FileNotFoundError:
        return {"status": "missing", "error": "input does not exist"}
    except (OSError, RuntimeError, ValueError) as error:
        return {"status": "unreadable", "error": str(error)}


def git_snapshot(cwd):
    """Git is optional; record unavailable observations explicitly."""
    scope = "whole_worktree_tracked_and_untracked"
    result = {"available": False, "head": None, "dirty": None,
              "dirty_scope": scope, "porcelain": None, "errors": []}

    def git(*arguments):
        return subprocess.run(["git", "-C", str(cwd), *arguments],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              text=True, encoding="utf-8", errors="replace", check=False)
    try:
        repository = git("rev-parse", "--show-toplevel")
        if repository.returncode:
            result["errors"].append(repository.stderr.strip())
            return result
        result["available"] = True
        result["root"] = repository.stdout.strip()
        head = git("rev-parse", "--verify", "HEAD")
        if head.returncode == 0:
            result["head"] = head.stdout.strip()
        else:
            result["errors"].append(head.stderr.strip())
        dirty = git("status", "--porcelain=v1", "--untracked-files=all")
        if dirty.returncode == 0:
            result["porcelain"] = dirty.stdout
            result["dirty"] = bool(dirty.stdout)
        else:
            result["errors"].append(dirty.stderr.strip())
    except OSError as error:
        result["errors"].append(str(error))
    return result


def portable_failure(exit_code):
    if exit_code < 0:
        return min(255, 128 - exit_code)
    return exit_code if 1 <= exit_code <= 255 else 1


def windows_batch(command):
    """Windows may implicitly use cmd.exe for batch files despite shell=False."""
    if os.name != "nt":
        return False
    executable = command[0]
    resolved = shutil.which(executable)
    return any(Path(name.rstrip(" .")).suffix.lower() in {".bat", ".cmd"}
               for name in [executable, resolved] if name)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--cwd", type=Path, default=Path.cwd(), help="existing command directory (default: current directory)")
    parser.add_argument("--input", action="append", default=[], metavar="RELATIVE_FILE", help="regular file within cwd to hash; repeat for multiple files (default: none)")
    parser.add_argument("--output-dir", type=Path, default=Path(".local/receipts"), help="receipt parent directory, relative to cwd (default: .local/receipts)")
    raw = list(sys.argv[1:] if argv is None else argv)
    separator = raw.index("--") if "--" in raw else len(raw)
    args = parser.parse_args(raw[:separator])
    if "--" not in raw:
        parser.error("separate the command with --")
    command = raw[separator + 1:]
    if not command:
        parser.error("a command is required after --")
    try:
        cwd = args.cwd.resolve(strict=True)
        if not cwd.is_dir():
            parser.error("cwd must be an existing directory")
        output = (cwd / args.output_dir).resolve()
        output.mkdir(parents=True, exist_ok=True)
        folder = Path(tempfile.mkdtemp(prefix="run-", dir=output))
    except (OSError, RuntimeError, ValueError) as error:
        print(f"Receipt setup failed: {error}", file=sys.stderr)
        return 2

    selected = list(dict.fromkeys(args.input))
    receipt = {
        "schema_version": 1,
        "status": "not_run",
        "command": {"argv": command, "cwd": str(cwd), "status": "not_run", "exit_code": None},
        "started_at": utc_now(), "finished_at": None,
        "input_scope": "selected_files_only" if selected else "no_inputs_selected",
        "inputs_before": {name: input_snapshot(cwd, name) for name in selected},
        "inputs_after": {}, "changed_inputs": [],
        "git_before": None, "git_after": None, "head_changed": None,
        "evidence_incomplete": False,
        "error": None, "wrapper_exit_code": 2, "log_file": "command.log",
        "limitations": [
            "Exit zero records command success; it does not establish that tests ran or passed.",
            "Hashes cover selected files only, not the whole repository or dependencies.",
            "Matching before/after snapshots do not rule out intermediate mutations.",
            "Git dirty scope includes tracked and untracked files in the whole worktree, including unignored receipt artifacts.",
            "Snapshots are observations, not atomic or tamper-proof; the child can modify evidence files.",
            "No timeout or process-tree monitoring is provided; abrupt interruption may leave incomplete evidence.",
            "Explicitly launched shells interpret their own arguments; only their own exit is recorded.",
        ],
    }
    invalid = [name for name, snapshot in receipt["inputs_before"].items() if snapshot["status"] != "present"]
    try:
        with (folder / "command.log").open("xb") as log:
            if invalid:
                receipt["error"] = "Invalid selected inputs: " + ", ".join(invalid)
            elif windows_batch(command):
                receipt["error"] = "Windows batch commands are refused because they can implicitly invoke a shell; use a native executable."
            else:
                receipt["git_before"] = git_snapshot(cwd)
                try:
                    child = subprocess.run(command, cwd=cwd, stdout=log, stderr=subprocess.STDOUT, shell=False, check=False)
                    receipt["command"]["exit_code"] = child.returncode
                    receipt["command"]["status"] = "command_succeeded" if child.returncode == 0 else "command_failed"
                except OSError as error:
                    receipt["error"] = str(error)
                receipt["inputs_after"] = {name: input_snapshot(cwd, name) for name in selected}
                receipt["changed_inputs"] = [name for name in selected if receipt["inputs_before"][name] != receipt["inputs_after"][name]]
                receipt["git_after"] = git_snapshot(cwd)
                before, after = receipt["git_before"], receipt["git_after"]
                if before["available"] and after["available"] and before["head"] is not None and after["head"] is not None:
                    receipt["head_changed"] = before["head"] != after["head"]
                receipt["evidence_incomplete"] = before["available"] and (
                    not after["available"]
                    or (before["head"] is not None and after["head"] is None)
                    or (before["dirty"] is not None and after["dirty"] is None))
                if receipt["evidence_incomplete"]:
                    reason = "Git observation became unavailable after the command; changes cannot be determined."
                    receipt["error"] = (receipt["error"] + "; " + reason) if receipt["error"] else reason
                code = receipt["command"]["exit_code"]
                if code is not None:
                    if code != 0:
                        receipt["status"] = "command_failed"
                        receipt["wrapper_exit_code"] = portable_failure(code)
                    elif receipt["evidence_incomplete"]:
                        receipt["status"] = "evidence_incomplete"
                        receipt["wrapper_exit_code"] = 4
                    elif receipt["changed_inputs"] or receipt["head_changed"]:
                        receipt["status"] = "inputs_changed"
                        receipt["wrapper_exit_code"] = 3
                    else:
                        receipt["status"] = "command_succeeded"
                        receipt["wrapper_exit_code"] = 0
        receipt["finished_at"] = utc_now()
        with (folder / "receipt.json").open("x", encoding="utf-8") as stream:
            json.dump(receipt, stream, indent=2, ensure_ascii=True)
            stream.write("\n")
    except OSError as error:
        print(f"Receipt write failed in {folder}: {error}", file=sys.stderr)
        return 2
    print(f"{receipt['status']}: {folder / 'receipt.json'}")
    if receipt["error"]:
        print(receipt["error"], file=sys.stderr)
    return receipt["wrapper_exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
