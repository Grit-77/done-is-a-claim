"""Synthetic delivery/read-back trap, using only temporary local fixtures.

Python 3.10+; standard library only. No real delivery, provider, or API is used.
Copy completion describes shutil.copyfile returning; it is not a process exit.
The demo exits 0 only when its expected contrasts are demonstrated, not when
all deliveries are correct. This is not a production incident or a measure of
agent performance. Run with --json for structured observations.
"""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile


def inspect_delivery(expected_reviewed, source, destination):
    """Read the actual destination; compare provenance and attempt JSON parsing.

    The expected reviewed artifact and copy source must be readable files.
    Missing or unreadable destinations are observations, never successful checks.
    """
    expected_bytes = Path(expected_reviewed).read_bytes()
    source_bytes = Path(source).read_bytes()
    checks = {
        "destination_exists": Path(destination).is_file(),
        "expected_reviewed_sha256": hashlib.sha256(expected_bytes).hexdigest(),
        "copy_source_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "destination_sha256": None,
        "bytes_match_source": False,
        "digest_matches_reviewed": False,
        "json_parse_ok": False,
        "readback_error": None,
        "json_error": None,
    }
    try:
        delivered_bytes = Path(destination).read_bytes()
    except OSError as error:
        checks["readback_error"] = type(error).__name__
        return checks
    checks["destination_sha256"] = hashlib.sha256(delivered_bytes).hexdigest()
    checks["bytes_match_source"] = delivered_bytes == source_bytes
    checks["digest_matches_reviewed"] = (
        checks["destination_sha256"] == checks["expected_reviewed_sha256"]
    )
    try:
        json.loads(delivered_bytes)
    except (ValueError, UnicodeDecodeError) as error:
        checks["json_error"] = type(error).__name__
    else:
        checks["json_parse_ok"] = True
    return checks


def contrasts_observed(scenarios):
    """Require all three observed outcomes, including successful real copies."""
    expected = {
        "correct_copy": (True, True),
        "stale_same_name": (False, True),
        "matching_invalid_json": (True, False),
    }
    for name, (digest_match, parse_ok) in expected.items():
        case = scenarios[name]
        checks = case["checks"]
        if not (
            case["copy_completed"] and case["copy_error"] is None
            and checks["destination_exists"] and checks["bytes_match_source"]
            and checks["readback_error"] is None
            and checks["digest_matches_reviewed"] == digest_match
            and checks["json_parse_ok"] == parse_ok
        ):
            return False
    return True


def run_demo():
    # Cleanup is registered before creating any synthetic artifact.
    with tempfile.TemporaryDirectory(prefix="synthetic-delivery-") as folder:
        root = Path(folder)
        fixtures = {
            "reviewed/artifact.json": b'{"version":2,"reviewed":true}\n',
            "stale/artifact.json": b'{"version":1,"reviewed":false}\n',
            "invalid/artifact.json": b'{"version":2,\n',
        }
        for relative, content in fixtures.items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        cases = {
            "correct_copy": ("reviewed/artifact.json", "reviewed/artifact.json"),
            "stale_same_name": ("reviewed/artifact.json", "stale/artifact.json"),
            "matching_invalid_json": ("invalid/artifact.json", "invalid/artifact.json"),
        }
        scenarios = {}
        for name, (expected, source) in cases.items():
            destination = f"delivered/{name}/artifact.json"
            (root / destination).parent.mkdir(parents=True)
            copy_completed, copy_error = False, None
            try:
                shutil.copyfile(root / source, root / destination)
            except OSError as error:
                copy_error = type(error).__name__
            else:
                copy_completed = True
            scenarios[name] = {
                "expected_reviewed": expected,
                "source": source,
                "destination": destination,
                "copy_completed": copy_completed,
                "copy_error": copy_error,
                "checks": inspect_delivery(root / expected, root / source, root / destination),
            }
    observed = contrasts_observed(scenarios)
    return {
        "case": "synthetic_wrong_delivery",
        "synthetic": True,
        "label": "SYNTHETIC local fixtures; not a production incident or agent performance measure.",
        "scenarios": scenarios,
        "expected_contrasts_observed": observed,
        "demo_exit_code": 0 if observed else 1,
        "demo_exit_meaning": (
            "expected contrasts demonstrated; not delivery success"
            if observed else "expected contrasts not demonstrated; not delivery success"
        ),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit structured synthetic observations")
    args = parser.parse_args()
    report = run_demo()
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(report["label"])
        for name, case in report["scenarios"].items():
            checks = case["checks"]
            print(f"{name}: source={case['source']} expected_reviewed={case['expected_reviewed']}")
            print("  " + " ".join(
                f"{key}={json.dumps(value)}" for key, value in (
                    ("copy_completed", case["copy_completed"]),
                    ("bytes_match_source", checks["bytes_match_source"]),
                    ("digest_matches_reviewed", checks["digest_matches_reviewed"]),
                    ("json_parse_ok", checks["json_parse_ok"]),
                )
            ))
        print(f"Demo exit: {report['demo_exit_code']} ({report['demo_exit_meaning']})")
    return report["demo_exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
