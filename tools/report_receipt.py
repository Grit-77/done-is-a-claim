#!/usr/bin/env python3
"""Emit scoped, shareable Markdown or JSON from editable local receipt evidence.

Usage: python tools/report_receipt.py RECEIPT --project EXISTING_ROOT
       [--format markdown|json] [--include-command]
Python 3.10+, standard library only. No files are written and recorded argv
is never executed. Exit codes match check_receipt: 0 matches, 1 different,
2 invalid, 3 recorded_failure, 4 incomplete. This is not a test verdict.
"""

import argparse
from collections import Counter
from datetime import datetime
import json
from pathlib import Path
import re
import sys

# Importing the checker must not create a bytecode cache in the toolkit.
sys.dont_write_bytecode = True
import check_receipt


MAX_COMMAND_CHARACTERS = 8192
COMPONENT_STATES = ("matches", "different", "missing", "unavailable", "incomplete")
TIMESTAMP = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}"
    r"(?:\.[0-9]{1,6})?(?:Z|[+-](?:[01][0-9]|2[0-3]):[0-5][0-9])"
)


def safe_timestamp(value):
    """Only render bounded ISO calendar timestamps with an explicit offset."""
    if not isinstance(value, str) or TIMESTAMP.fullmatch(value) is None:
        return "unavailable"
    # Python 3.10 accepts only 3/6 fractional digits. Normalize validation
    # precision while preserving the original strict timestamp for display.
    normalized = re.sub(r"\.([0-9]{1,6})", lambda match: "." + match[1].ljust(6, "0"), value)
    try:
        datetime.fromisoformat(normalized.replace("Z", "+00:00"))
    except ValueError:
        return "unavailable"
    return value


def child_exit(value):
    if value is None:
        return "unavailable"
    if -(2 ** 31) <= value <= 2 ** 32 - 1:
        return str(value)
    return "outside portable range"


def command_display(argv):
    """Display a bounded escaped argument array inside a fixed code fence.

    The parser bounds source metadata to 1 MiB. ASCII JSON escapes controls
    and Unicode direction characters; escaping backticks and HTML delimiters
    prevents any argument from terminating the fence or emitting HTML.
    """
    encoded = json.dumps(argv, ensure_ascii=True)
    for character, replacement in [("`", "\\u0060"), ("<", "\\u003c"),
                                   (">", "\\u003e"), ("&", "\\u0026")]:
        encoded = encoded.replace(character, replacement)
    if len(encoded) > MAX_COMMAND_CHARACTERS:
        return encoded[:MAX_COMMAND_CHARACTERS] + "\n[argument display truncated]"
    return encoded


def render(report, metadata=None, include_command=False):
    """Render fixed labels and parser-validated values, never freeform errors."""
    lines = ["## Receipt evidence", "", "| Observation | Value |", "| --- | --- |"]

    def row(label, value):
        lines.append(f"| {label} | {value} |")

    row("Recheck state", report["state"])
    if report["state"] == "invalid":
        row("Diagnostic", "receipt metadata or local observation invalid/unavailable")
    else:
        recorded = report["recorded"]
        row("Historical receipt status", recorded["status"])
        row("Historical command status", recorded["command_status"])
        row("Historical child exit", child_exit(recorded["exit_code"]))
        row("Recorded start", safe_timestamp(metadata.get("started_at")))
        row("Recorded finish", safe_timestamp(metadata.get("finished_at")))
        row("Selected input count", len(report["inputs"]))
        counts = Counter(item["state"] for item in report["inputs"].values())
        row("Selected input freshness", "; ".join(f"{state}: {counts[state]}" for state in COMPONENT_STATES if counts[state]) or "no selected files")
        row("Log freshness", report["log"]["state"])
        row("Recorded log SHA-256", report["log"].get("expected_sha256") or "unavailable")
        row("Current log SHA-256", report["log"].get("current_sha256") or "unavailable")
        row("Git HEAD freshness", report["git"]["state"])
        row("Recorded Git HEAD", report["git"].get("expected_head") or "unavailable")
        row("Current Git HEAD", report["git"].get("current_head") or "unavailable")
        row("Incomplete observation categories", len(report["reasons"]))
    lines += ["", "Recorded command outcome is historical; no command was rerun.",
              "No test-pass or task-completion verdict is provided.",
              "Editable hash consistency only; receipts and hashes can be changed together.",
              "Non-atomic observations cover selected files, log bytes and optional Git HEAD; dependencies and other files are outside this scope.",
              "Default output omits command arguments, log contents, local paths, file names and freeform diagnostics."]
    if include_command and metadata is not None and report["state"] != "invalid":
        lines += ["", "Disclosed arguments may contain secrets. This escaped argument array is not a runnable shell command.",
                  "", "```text", command_display(metadata["command"]["argv"]), "```"]
    return "\n".join(lines) + "\n"


def render_json(report):
    """Serialize the public v1 projection, never local diagnostic text."""
    state = report["state"]
    if state == "different":
        reason = ("selected_input_missing" if any(
            item["state"] == "missing" for item in report["inputs"].values()
        ) else "observations_differ")
    elif state == "incomplete":
        components = [report["log"], report["git"], *report["inputs"].values()]
        reason = ("observation_unavailable" if any(
            item["state"] == "unavailable" for item in components
        ) else "evidence_incomplete")
    else:
        reason = {
            "matches": "observations_match",
            "recorded_failure": "historical_failure",
            "invalid": "invalid_evidence_or_context",
        }[state]
    recorded = report["recorded"] if state != "invalid" else {}
    child = recorded.get("exit_code")
    if type(child) is not int or not -(2 ** 31) <= child <= 2 ** 32 - 1:
        child = None
    summary = {
        "schema_version": 1,
        "historical_command_status": recorded.get("command_status"),
        "historical_child_exit": child,
        "recheck_state": state,
        "freshness": "changed" if state == "different" else (
            "unverifiable" if state in {"invalid", "incomplete"} else "matches"),
        "reason_code": reason,
    }
    return json.dumps(summary, indent=2, sort_keys=True) + "\n"


class PrivateArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        # argparse's error text can echo unknown CLI arguments or local paths.
        self.print_usage(sys.stderr)
        self.exit(2, "report_receipt: invalid arguments; use --help for usage.\n")


def main(argv=None):
    parser = PrivateArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("receipt", type=Path)
    parser.add_argument("--project", type=Path, required=True, help="explicit existing project root")
    parser.add_argument("--include-command", action="store_true", help="disclose escaped arguments, which may contain secrets")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown",
                        help="public summary format (default: markdown)")
    args = parser.parse_args(argv)
    if args.format == "json" and args.include_command:
        parser.error("include-command is not available for JSON summaries")
    metadata = None
    try:
        validated = check_receipt.load_receipt(args.receipt.absolute())
        metadata = validated[0]
        report = check_receipt._check_loaded(args.receipt, args.project, validated)
    except (check_receipt.InvalidReceipt, OSError, UnicodeError, ValueError, RuntimeError, RecursionError):
        report = {"state": "invalid"}
    if args.format == "json":
        print(render_json(report), end="")
    else:
        print(render(report, metadata, args.include_command), end="")
    return check_receipt.EXITS[report["state"]]


if __name__ == "__main__":
    raise SystemExit(main())
