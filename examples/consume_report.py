#!/usr/bin/env python3
"""Parse a public JSON report without replacing the reporter's exit status.

Usage: python examples/consume_report.py RECEIPT --project EXISTING_ROOT
Python 3.10+, standard library only. Runs the local reporter once, without a
shell; never runs the recorded command. On successful parsing/output, exits
with the reporter's own code (0 matches, 1 different, 2 invalid,
3 recorded_failure, 4 incomplete). Consumer errors retain a nonzero reporter
code when available, otherwise return 5. No completion verdict is provided.
"""

import argparse
import json
from pathlib import Path
import subprocess
import sys


REPORTER = Path(__file__).resolve().parents[1] / "tools" / "report_receipt.py"


class PrivateArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        self.exit(5, "consume_report: invalid arguments; use --help for usage.\n")


def main(argv=None):
    parser = PrivateArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("receipt", type=Path)
    parser.add_argument("--project", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = subprocess.run(
            [sys.executable, "-E", "-s", "-B", str(REPORTER), str(args.receipt),
             "--project", str(args.project), "--format", "json"],
            stdin=subprocess.DEVNULL, capture_output=True, timeout=120,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except (OSError, subprocess.TimeoutExpired):
        print("consume_report: reporter could not complete.", file=sys.stderr)
        return 5
    # Save this before parsing or printing. Neither operation's success is the
    # reporter's result; historical_child_exit is also a different observation.
    reporter_exit = result.returncode
    try:
        summary = json.loads(result.stdout)
    except (ValueError, UnicodeError, RecursionError):
        print("consume_report: reporter JSON could not be parsed.", file=sys.stderr)
        return reporter_exit or 5
    try:
        print(json.dumps(summary, indent=2, sort_keys=True), flush=True)
    except (OSError, UnicodeError):
        # Prevent an interpreter-shutdown flush from replacing our exit code.
        sys.stdout = None
        print("consume_report: summary output failed.", file=sys.stderr)
        return reporter_exit or 5
    return reporter_exit


if __name__ == "__main__":
    raise SystemExit(main())
