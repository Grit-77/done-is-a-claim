"""Synthetic file deliveries against pre-frozen contracts; no controller invoked."""

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import sys


SPEC_DIRECTORY = Path(__file__).resolve().parent / "fixed-delivery"
REQUIRED_CHECKS = ("destination_exists", "sha256_matches_approved", "json_parse_ok")
INPUTS = {
    "inputs/approved/artifact.json": b'{"version":2,"reviewed":true}\n',
    "inputs/stale/artifact.json": b'{"version":1,"reviewed":false}\n',
    "inputs/invalid/artifact.json": b'{"version":2,\n',
}


def _relative_path(value):
    if (not isinstance(value, str) or not value or "\\" in value or ":" in value
            or PurePosixPath(value).is_absolute()
            or any(part in ("", ".", "..") for part in value.split("/"))):
        raise ValueError("invalid_relative_path")
    return value


def _path(root, relative):
    current = Path(root)
    if current.is_symlink():
        raise ValueError("linked_workspace")
    for part in PurePosixPath(_relative_path(relative)).parts:
        current = current / part
        if current.is_symlink():
            raise ValueError("linked_artifact")
    return current


def _reject_nonfinite(_value):
    raise ValueError("nonfinite_json")


@dataclass(frozen=True)
class FrozenContract:
    task_id: str
    task: str
    approved_artifact: str
    approved_sha256: str
    destination: str
    required_checks: tuple
    spec_sha256: str
    spec_bytes: bytes


def freeze_contract(path):
    """Read approval once, retaining the original bytes independently of the file."""
    raw = Path(path).read_bytes()
    data = json.loads(raw, parse_constant=_reject_nonfinite)
    if (not isinstance(data, dict) or type(data.get("schema_version")) is not int
            or data["schema_version"] != 1
            or not isinstance(data.get("task_id"), str)
            or not re.fullmatch(r"[a-z0-9-]{1,80}", data["task_id"])
            or not isinstance(data.get("task"), str) or not data["task"]
            or len(data["task"]) > 2048
            or not isinstance(data.get("approved_sha256"), str)
            or not re.fullmatch(r"[0-9a-f]{64}", data["approved_sha256"])
            or data.get("required_checks") != list(REQUIRED_CHECKS)):
        raise ValueError("invalid_task_spec")
    return FrozenContract(
        task_id=data["task_id"], task=data["task"],
        approved_artifact=_relative_path(data.get("approved_artifact")),
        approved_sha256=data["approved_sha256"],
        destination=_relative_path(data.get("destination")),
        required_checks=REQUIRED_CHECKS,
        spec_sha256=hashlib.sha256(raw).hexdigest(), spec_bytes=raw,
    )


def _identity(contract):
    return {
        "task_id": contract.task_id,
        "task_spec_sha256": contract.spec_sha256,
        "approved_sha256": contract.approved_sha256,
        "destination": contract.destination,
    }


def observe_destination(contract, root, *, copy_completed=None):
    """Read destination bytes against frozen approval; do not consult the source."""
    result = {
        **_identity(contract), "copy_completed": copy_completed,
        "destination_exists": False, "destination_sha256": None,
        "sha256_matches_approved": False, "json_parse_ok": False,
        "readback_error": None, "json_error": None,
    }
    try:
        destination = _path(root, contract.destination)
        result["destination_exists"] = destination.is_file()
        content = destination.read_bytes()
    except (OSError, ValueError) as error:
        result["readback_error"] = type(error).__name__
    else:
        result["destination_sha256"] = hashlib.sha256(content).hexdigest()
        result["sha256_matches_approved"] = result["destination_sha256"] == contract.approved_sha256
        try:
            json.loads(content, parse_constant=_reject_nonfinite)
        except (ValueError, UnicodeDecodeError) as error:
            result["json_error"] = type(error).__name__
        else:
            result["json_parse_ok"] = True
    result["accepted"] = all(result[name] for name in contract.required_checks)
    return result


def run_fixture(output):
    """Persist a new fixture workspace; leave artifacts available for inspection."""
    main = freeze_contract(SPEC_DIRECTORY / "task-spec.json")
    control = freeze_contract(SPEC_DIRECTORY / "format-control-spec.json")
    for contract in (main, control):
        if hashlib.sha256(INPUTS[contract.approved_artifact]).hexdigest() != contract.approved_sha256:
            raise ValueError("fixture_approval_mismatch")
    root = Path(output)
    if root.exists() or root.is_symlink():
        raise FileExistsError("output_exists")
    root.mkdir()
    (root / "task-spec.json").write_bytes(main.spec_bytes)
    (root / "format-control-spec.json").write_bytes(control.spec_bytes)
    for relative, content in INPUTS.items():
        path = _path(root, relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    def attempt(case_id, contract, source):
        destination = _path(root, contract.destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        completed, error_name = False, None
        try:
            shutil.copyfile(_path(root, source), destination)
        except OSError as error:
            error_name = type(error).__name__
        else:
            completed = True
        return {
            "case_id": case_id, "copy_error": error_name,
            **observe_destination(contract, root, copy_completed=completed),
        }

    attempts = [
        attempt("correct_copy", main, "inputs/approved/artifact.json"),
        attempt("stale_same_name", main, "inputs/stale/artifact.json"),
        attempt("invalid_json", main, "inputs/invalid/artifact.json"),
    ]
    format_observation = attempt("matching_invalid_json", control, "inputs/invalid/artifact.json")
    unchanged = (
        (root / "task-spec.json").read_bytes() == main.spec_bytes
        and (root / "format-control-spec.json").read_bytes() == control.spec_bytes
    )
    expected = [(True, True, True), (False, True, False), (False, False, False)]
    measured = [(r["sha256_matches_approved"], r["json_parse_ok"], r["accepted"]) for r in attempts]
    control_measured = tuple(format_observation[k] for k in ("sha256_matches_approved", "json_parse_ok", "accepted"))
    exercised = (unchanged and measured == expected and control_measured == (True, False, False)
                 and all(r["copy_completed"] and r["copy_error"] is None and r["readback_error"] is None
                         for r in [*attempts, format_observation]))
    report = {
        "schema_version": 1, "synthetic": True, "controller_evaluated": False,
        "main": {**_identity(main), "attempts": attempts},
        "format_control": {**_identity(control), "observation": format_observation},
        "specs_unchanged": unchanged, "suite_exercised_as_expected": exercised,
        "runner_exit_meaning": "0 means prescribed observations were exercised, not that every delivery was accepted.",
    }
    (root / "observations.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(prog="fixed_delivery.py", description=__doc__)
    parser.add_argument("--output", required=True, help="New persistent synthetic workspace; existing paths are refused")
    args = parser.parse_args(argv)
    try:
        report = run_fixture(Path(args.output))
    except (OSError, ValueError, KeyError) as error:
        print(json.dumps({"error": type(error).__name__}), file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2))
    return 0 if report["suite_exercised_as_expected"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
