#!/usr/bin/env python3
"""Compare editable receipt hashes with current local bytes; Python 3.10+.

Usage: python tools/check_receipt.py RECEIPT --project EXISTING_ROOT [--json]
Never executes recorded argv, follows recorded absolute paths, or writes files.
Exit 0: matches; 1: different/missing bytes or HEAD; 2: invalid metadata/path;
3: recorded command failure/mutation; 4: incomplete observations or scope.
Comparisons are non-atomic, limited to selected files, log bytes and optional
Git HEAD, and provide editable hash consistency rather than authentication or
a claim that a task is complete. Raw command output is never displayed.
"""

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
import subprocess
import sys


MAX_METADATA_BYTES = 1024 * 1024
EXITS = {"matches": 0, "different": 1, "invalid": 2,
         "recorded_failure": 3, "incomplete": 4}
LIMITATIONS = [
    "Editable hash consistency only; receipts and hashes can be changed together.",
    "Non-atomic observations of selected files, log bytes and optional Git HEAD only.",
    "Recorded command outcome is historical; no command is rerun and no task completion is established.",
]


class InvalidReceipt(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise InvalidReceipt(message)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON member: " + key)
        result[key] = value
    return result


def reject_constant(value):
    raise InvalidReceipt("non-finite JSON number: " + value)


def finite_float(value):
    number = float(value)
    require(math.isfinite(number), "non-finite JSON number")
    return number


def known_status(value, choices):
    return isinstance(value, str) and value in choices


def digest(value, label, lengths=(64,)):
    require(isinstance(value, str) and len(value) in lengths
            and re.fullmatch(r"[0-9a-f]+", value) is not None,
            label + " must be a lowercase hexadecimal digest")


def input_name(value):
    require(isinstance(value, str) and value, "input name must be a nonempty string")
    normalized = value.replace("\\", "/")
    parts = normalized.split("/")
    require(not normalized.startswith("/") and all(parts), "input must be a relative file without empty path components")
    for part in parts:
        require(part not in {".", ".."} and not part.endswith((".", " ")),
                "input contains traversal or a path alias")
        require(not any(ord(character) < 32 or character in ':<>"|?*' for character in part),
                "input contains a drive, stream, or nonportable path character")
        device = part.split(".")[0].upper()
        require(device not in {"CON", "PRN", "AUX", "NUL", "CONIN$", "CONOUT$"}
                and re.fullmatch(r"(?:COM|LPT)[1-9\u00b9\u00b2\u00b3]", device) is None,
                "input contains a Windows device alias")
    return normalized


def snapshots(value, label):
    require(isinstance(value, dict), label + " must be an object")
    normalized = {}
    aliases = set()
    for name, snapshot in value.items():
        name = input_name(name)
        require(name.casefold() not in aliases, label + " contains input aliases")
        aliases.add(name.casefold())
        require(isinstance(snapshot, dict), label + " snapshot must be an object")
        require(known_status(snapshot.get("status"), {"present", "missing", "outside", "invalid", "not_regular", "unreadable"}),
                label + " snapshot has unsupported status")
        if snapshot["status"] == "present":
            digest(snapshot.get("sha256"), label + " sha256")
        elif "sha256" in snapshot:
            digest(snapshot["sha256"], label + " sha256")
        for field in ["resolved_path", "error"]:
            if field in snapshot:
                require(isinstance(snapshot[field], str), label + " " + field + " must be a string")
        normalized[name] = snapshot
    return normalized


def git_observation(value, label):
    if value is None:
        return
    require(isinstance(value, dict), label + " must be an object or null")
    require(type(value.get("available")) is bool, label + " available must be boolean")
    require("head" in value and "dirty" in value, label + " missing HEAD/dirty observation")
    if value["head"] is not None:
        digest(value["head"], label + " head", (40, 64))
        require(value["available"], label + " cannot have HEAD while unavailable")
    require(value["dirty"] is None or type(value["dirty"]) is bool, label + " dirty must be boolean or null")
    if "errors" in value:
        require(isinstance(value["errors"], list) and all(isinstance(item, str) for item in value["errors"]),
                label + " errors must be an array of strings")
    for field in ["root", "dirty_scope"]:
        if field in value:
            require(isinstance(value[field], str), label + " " + field + " must be a string")
    if "porcelain" in value:
        require(value["porcelain"] is None or isinstance(value["porcelain"], str), label + " porcelain must be a string or null")


def load_receipt(path):
    require(stat.S_ISREG(path.stat().st_mode), "receipt must be a regular file")
    with path.open("rb") as stream:
        require(stat.S_ISREG(os.fstat(stream.fileno()).st_mode), "receipt must be a regular file")
        raw = stream.read(MAX_METADATA_BYTES + 1)
    require(len(raw) <= MAX_METADATA_BYTES, "receipt metadata exceeds 1 MiB")
    value = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_object,
                       parse_constant=reject_constant, parse_float=finite_float)
    pending = [(value, 0)]
    while pending:
        item, depth = pending.pop()
        require(depth <= 64, "receipt metadata nesting exceeds 64 levels")
        if isinstance(item, dict):
            pending.extend((child, depth + 1) for child in item.values())
        elif isinstance(item, list):
            pending.extend((child, depth + 1) for child in item)
    require(isinstance(value, dict), "receipt must be a JSON object")
    require(type(value.get("schema_version")) is int and value["schema_version"] == 1,
            "unsupported schema_version; expected integer 1")
    require(known_status(value.get("status"), {"not_run", "command_succeeded", "command_failed", "inputs_changed", "evidence_incomplete"}),
            "unsupported recorded status")
    command = value.get("command")
    require(isinstance(command, dict), "command must be an object")
    require(isinstance(command.get("argv"), list) and command["argv"]
            and all(isinstance(item, str) for item in command["argv"]), "command argv must be a nonempty string array")
    require(isinstance(command.get("cwd"), str), "command cwd must be a string")
    require(known_status(command.get("status"), {"not_run", "command_succeeded", "command_failed"}), "unsupported command status")
    require("exit_code" in command and (command["exit_code"] is None or type(command["exit_code"]) is int),
            "command exit_code must be an integer or null")
    require(type(value.get("wrapper_exit_code")) is int, "wrapper_exit_code must be an integer")
    require(value.get("log_file") == "command.log", "log_file must be the receipt sibling command.log")
    if "log_sha256" in value:
        digest(value["log_sha256"], "log_sha256")
    before = snapshots(value.get("inputs_before"), "inputs_before")
    after = snapshots(value.get("inputs_after"), "inputs_after")
    require(known_status(value.get("input_scope"), {"selected_files_only", "no_inputs_selected"}), "unsupported input_scope")
    require((value["input_scope"] == "selected_files_only") == bool(before or after), "input_scope disagrees with selected inputs")
    changed = value.get("changed_inputs")
    require(isinstance(changed, list), "changed_inputs must be a string array")
    changed = [input_name(name) for name in changed]
    require(len({name.casefold() for name in changed}) == len(changed), "changed_inputs contains aliases")
    require(all(name in before or name in after for name in changed), "changed_inputs names an unselected file")
    require("head_changed" in value and (value["head_changed"] is None or type(value["head_changed"]) is bool),
            "head_changed must be boolean or null")
    require(type(value.get("evidence_incomplete", False)) is bool, "evidence_incomplete must be boolean")
    require("git_before" in value and "git_after" in value, "missing recorded Git observations")
    git_observation(value["git_before"], "git_before")
    git_observation(value["git_after"], "git_after")
    require(value.get("error") is None or isinstance(value["error"], str), "error must be a string or null")
    return value, before, after, changed


def hash_regular(path, root, reject_link=False):
    """Resolve confinement before opening; detect final symlinks/reparse logs."""
    info = path.lstat()
    reparse = getattr(info, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    if reject_link:
        require(not stat.S_ISLNK(info.st_mode) and not reparse,
                "command.log cannot be a symlink or reparse point")
    resolved = path.resolve()
    require(resolved.is_relative_to(root), "path resolves outside its explicit root")
    require(stat.S_ISREG(resolved.stat().st_mode), "path must be a regular file")
    hasher = hashlib.sha256()
    with resolved.open("rb") as stream:
        require(stat.S_ISREG(os.fstat(stream.fileno()).st_mode), "opened path must be a regular file")
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def compare_file(path, root, expected, reject_link=False):
    try:
        current = hash_regular(path, root, reject_link)
    except FileNotFoundError:
        return {"state": "missing", "expected_sha256": expected}
    except (OSError, RuntimeError) as error:
        return {"state": "unavailable", "reason": str(error), "expected_sha256": expected}
    return {"state": "matches" if current == expected else "different",
            "expected_sha256": expected, "current_sha256": current}


def compare_git(project, before, after):
    if before is None or after is None:
        return {"state": "incomplete", "reason": "recorded Git observation missing"}
    if not before["available"] and not after["available"]:
        return {"state": "outside_scope", "reason": "Git absent during capture; HEAD is outside comparison scope"}
    if not after["available"] or after["head"] is None:
        return {"state": "incomplete", "reason": "recorded expected Git HEAD unavailable"}
    expected = after["head"]
    # Ignore inherited overrides that could point Git at a different repository.
    environment = {key: val for key, val in os.environ.items() if not key.upper().startswith("GIT_")}
    environment["GIT_OPTIONAL_LOCKS"] = "0"
    try:
        result = subprocess.run(["git", "-C", str(project), "rev-parse", "--verify", "HEAD"],
                                capture_output=True, text=True, encoding="utf-8", errors="replace",
                                check=False, env=environment)
    except OSError as error:
        return {"state": "unavailable", "expected_head": expected, "reason": str(error)}
    current = result.stdout.strip()
    if result.returncode or not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", current):
        return {"state": "unavailable", "expected_head": expected, "reason": "current Git HEAD unavailable"}
    return {"state": "matches" if expected == current else "different",
            "expected_head": expected, "current_head": current}


def check(receipt_path, project):
    project = project.resolve(strict=True)
    require(project.is_dir(), "--project must be an existing directory")
    receipt_path = receipt_path.absolute()
    value, before, after, changed = load_receipt(receipt_path)
    parent = receipt_path.parent.resolve(strict=True)
    log = compare_file(parent / "command.log", parent, value.get("log_sha256"), reject_link=True)
    if "log_sha256" not in value and log["state"] not in {"missing", "unavailable"}:
        log = {"state": "unbound", "reason": "legacy receipt has no log digest"}
    inputs = {}
    for name in sorted(set(before) | set(after)):
        # Validate confinement even when the historical snapshot is missing.
        path = project.joinpath(*name.split("/"))
        require(path.resolve().is_relative_to(project), "selected input resolves outside --project")
        snapshot = after.get(name)
        if snapshot is None or snapshot["status"] != "present":
            inputs[name] = {"state": "incomplete", "recorded_status": snapshot["status"] if snapshot else "unobserved"}
        else:
            inputs[name] = compare_file(path, project, snapshot["sha256"])
    git = compare_git(project, value["git_before"], value["git_after"])
    recorded = {"status": value["status"], "command_status": value["command"]["status"],
                "exit_code": value["command"]["exit_code"], "changed_inputs": changed,
                "head_changed": value["head_changed"], "evidence_incomplete": value.get("evidence_incomplete", False)}
    reasons = []
    if not inputs:
        reasons.append("no selected file hashes")
    if set(before) != set(after) or any(item["status"] != "present" for item in before.values()):
        reasons.append("selected input observations incomplete")
    old_git, new_git = value["git_before"], value["git_after"]
    if any(observation and observation["available"] and
           (observation["head"] is None or observation["dirty"] is None)
           for observation in [old_git, new_git]):
        reasons.append("recorded Git HEAD or dirty observation unavailable")
    if old_git and old_git["available"] and (not new_git or not new_git["available"]
            or (old_git["head"] is not None and new_git["head"] is None)
            or (old_git["dirty"] is not None and new_git["dirty"] is None)):
        reasons.append("recorded Git observations were lost")
    if recorded["evidence_incomplete"] or recorded["status"] == "evidence_incomplete":
        reasons.append("recorded evidence incomplete")
    components = [log, git, *inputs.values()]
    historical_mutation = changed or recorded["head_changed"] or any(
        (before[name]["status"], before[name].get("sha256")) !=
        (after[name]["status"], after[name].get("sha256"))
        for name in set(before) & set(after))
    if old_git and new_git and old_git["head"] is not None and new_git["head"] is not None:
        historical_mutation = historical_mutation or old_git["head"] != new_git["head"]
    historical_failure = (recorded["status"] != "command_succeeded"
                          or recorded["command_status"] != "command_succeeded"
                          or recorded["exit_code"] != 0 or value["wrapper_exit_code"] != 0
                          or historical_mutation or value.get("error") is not None)
    if any(item["state"] in {"different", "missing"} for item in components):
        state = "different"
    elif reasons or any(item["state"] in {"unbound", "unavailable", "incomplete"} for item in components):
        state = "incomplete"
    elif historical_failure:
        state = "recorded_failure"
    else:
        state = "matches"
    return {"state": state, "recorded": recorded, "log": log, "inputs": inputs,
            "git": git, "reasons": reasons, "limitations": LIMITATIONS}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("receipt", type=Path)
    parser.add_argument("--project", type=Path, required=True, help="explicit existing project root; recorded roots are ignored")
    parser.add_argument("--json", action="store_true", help="emit stable structured comparison results")
    args = parser.parse_args(argv)
    try:
        report = check(args.receipt, args.project)
    except (InvalidReceipt, OSError, UnicodeError, ValueError, RuntimeError, RecursionError) as error:
        report = {"state": "invalid", "reason": str(error), "limitations": LIMITATIONS}
    if args.json:
        print(json.dumps(report, sort_keys=True, ensure_ascii=True, allow_nan=False))
    else:
        print("Editable hash consistency: " + report["state"])
        if report["state"] == "invalid":
            print(report["reason"])
        else:
            recorded = report["recorded"]
            print(f"Recorded outcome: {recorded['status']} (child exit {recorded['exit_code']})")
            print("Log: " + report["log"]["state"])
            for name, component in report["inputs"].items():
                print(f"Input {name}: {component['state']}")
            print("Git HEAD: " + report["git"]["state"])
            for reason in report["reasons"]:
                print(reason)
        print(LIMITATIONS[0])
        print(LIMITATIONS[1])
    return EXITS[report["state"]]


if __name__ == "__main__":
    raise SystemExit(main())
