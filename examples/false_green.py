"""Dependency-free synthetic false-green demo; not an incident raw log.

A failing verifier's output is passed to a successful summarizer. Both are real
Python child processes, launched without a shell. Output merges stdout/stderr.
The demo's own exit 0 means the expected mismatch was demonstrated, not fixture
success. The verifier's exit status determines the receipt. Use --json for the
captured command argv, output, exit statuses, receipt, and demo exit meaning.
"""

import argparse
import json
import subprocess
import sys


def run_demo():
    verifier_command = [
        sys.executable,
        "-c",
        "import sys; print('SYNTHETIC verifier: FAIL (expected 2, got 3)'); "
        "sys.exit(1)",
    ]
    summarizer_command = [
        sys.executable,
        "-c",
        "import sys; lines = sys.stdin.read().splitlines(); "
        "print('SYNTHETIC summarizer: displayed final line'); "
        "print(lines[-1] if lines else '(no output)')",
    ]
    verifier = subprocess.run(
        verifier_command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    summarizer = subprocess.run(
        summarizer_command,
        input=verifier.stdout,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    expected_mismatch = verifier.returncode == 1 and summarizer.returncode == 0
    demo_exit_code = 0 if expected_mismatch else 1
    return {
        "case": "synthetic_false_green",
        "synthetic": True,
        "label": "Synthetic demo, not incident raw log.",
        "verifier": {
            "command": verifier_command,
            "output": verifier.stdout,
            "exit_code": verifier.returncode,
        },
        "summarizer": {
            "command": summarizer_command,
            "output": summarizer.stdout,
            "exit_code": summarizer.returncode,
        },
        "verdict": {
            "state": "FAIL" if verifier.returncode != 0 else "NOT VERIFIED",
            "command": verifier_command,
            "exit_code": verifier.returncode,
            "reason": (
                f"Verifier exited {verifier.returncode}; summarizer exit "
                f"{summarizer.returncode} does not verify the fixture."
            ),
        },
        "demo_exit_code": demo_exit_code,
        "demo_exit_meaning": (
            "expected mismatch demonstrated; not fixture success"
            if expected_mismatch else
            "expected mismatch was not demonstrated; not fixture success"
        ),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit captured structured evidence")
    args = parser.parse_args()
    data = run_demo()
    if args.json:
        print(json.dumps(data, indent=2))
    else:
        print(data["label"])
        for role in ("verifier", "summarizer"):
            print(f"{role.capitalize()} command argv: {json.dumps(data[role]['command'])}")
            print(f"{role.capitalize()} output:")
            print(data[role]["output"], end="")
            print(f"{role.capitalize()} exit: {data[role]['exit_code']}")
        print(f"Receipt state: {data['verdict']['state']}")
        print(f"Command argv: {json.dumps(data['verdict']['command'])}")
        print(f"Command exit: {data['verdict']['exit_code']}")
        print(f"Reason: {data['verdict']['reason']}")
        print(f"Demo exit: {data['demo_exit_code']} ({data['demo_exit_meaning']})")
    return data["demo_exit_code"]


if __name__ == "__main__":
    sys.exit(main())
