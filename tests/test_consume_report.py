"""Synthetic public-JSON consumer checks; no recorded command is executed."""

from contextlib import redirect_stderr, redirect_stdout
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "examples" / "consume_report.py"
REPORTER = ROOT / "tools" / "report_receipt.py"


class ConsumeReportTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.project = self.root / "PRIVATE_PROJECT_SENTINEL"
        self.project.mkdir()
        self.input = self.project / "PRIVATE_INPUT_SENTINEL.txt"
        self.input.write_bytes(b"selected\x00\xff\n")
        self.receipt = self.root / "receipt.json"
        self.marker = self.root / "executed"
        log = b"PRIVATE_LOG_SENTINEL\n"
        (self.root / "command.log").write_bytes(log)
        snapshot = {self.input.name: {
            "status": "present", "sha256": hashlib.sha256(self.input.read_bytes()).hexdigest(),
        }}
        self.data = {
            "schema_version": 1, "status": "command_succeeded",
            "command": {
                "argv": [sys.executable, "-c", "from pathlib import Path; Path(" + repr(str(self.marker)) + ").touch()"],
                "cwd": "PRIVATE_CWD_SENTINEL", "status": "command_succeeded", "exit_code": 0,
            },
            "wrapper_exit_code": 0, "log_file": "command.log",
            "log_sha256": hashlib.sha256(log).hexdigest(),
            "inputs_before": snapshot, "inputs_after": snapshot,
            "input_scope": "selected_files_only", "changed_inputs": [],
            "head_changed": None,
            "git_before": {"available": False, "head": None, "dirty": None},
            "git_after": {"available": False, "head": None, "dirty": None},
        }
        self.save()

    def save(self):
        self.receipt.write_text(json.dumps(self.data), encoding="utf-8")

    def command(self, script):
        return [sys.executable, "-E", "-s", "-B", str(script), str(self.receipt),
                "--project", str(self.project)]

    def run_command(self, command):
        return subprocess.run(command, stdin=subprocess.DEVNULL, capture_output=True,
                              timeout=120, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))

    def snapshot(self):
        return {str(path.relative_to(self.root)): path.read_bytes()
                for path in self.root.rglob("*") if path.is_file()}

    def test_real_reporter_codes_survive_parsing_and_output(self):
        cases = [("matches", 0), ("different", 1), ("invalid", 2),
                 ("recorded_failure", 3), ("incomplete", 4)]
        for state, expected in cases:
            with self.subTest(state=state):
                if state == "different":
                    self.input.write_bytes(b"changed")
                elif state == "invalid":
                    self.receipt.write_bytes(b"{PRIVATE_INVALID_SENTINEL")
                elif state == "recorded_failure":
                    self.input.write_bytes(b"selected\x00\xff\n")
                    self.data["status"] = "command_failed"
                    self.data["command"].update(status="command_failed", exit_code=7)
                    self.data["wrapper_exit_code"] = 7
                    self.save()
                elif state == "incomplete":
                    del self.data["log_sha256"]
                    self.save()
                before = self.snapshot()
                producer = self.run_command(self.command(REPORTER) + ["--format", "json"])
                consumer = self.run_command(self.command(SCRIPT))
                self.assertEqual(producer.returncode, expected, producer.stderr)
                self.assertEqual(consumer.returncode, expected, consumer.stderr)
                summary = json.loads(consumer.stdout)
                self.assertEqual(summary, json.loads(producer.stdout))
                self.assertEqual(summary["recheck_state"], state)
                self.assertEqual(consumer.stderr, b"")
                self.assertNotIn(b"PRIVATE_", consumer.stdout + consumer.stderr)
                if state == "different":
                    self.assertEqual(summary["historical_child_exit"], 0)
                    self.assertEqual(summary["historical_command_status"], "command_succeeded")
                    self.assertEqual(summary["freshness"], "changed")
                if state == "recorded_failure":
                    self.assertEqual(summary["historical_child_exit"], 7)
                    self.assertEqual(summary["freshness"], "matches")
                self.assertEqual(before, self.snapshot())
                self.assertFalse(self.marker.exists())

    def test_unsafe_parser_masks_changed_input_but_safe_consumer_retains_one(self):
        self.assertEqual(self.run_command(self.command(SCRIPT)).returncode, 0)
        self.input.write_bytes(b"changed")
        producer = self.run_command(self.command(REPORTER) + ["--format", "json"])
        safe = self.run_command(self.command(SCRIPT))
        # Deliberately wrong: a successful parser/print process supplies its own
        # zero exit, ignoring the real reporter's return code.
        unsafe = self.run_command([
            sys.executable, "-I", "-B", "-c",
            "import json, subprocess, sys; "
            "result = subprocess.run(sys.argv[1:], capture_output=True, timeout=120); "
            "print(json.dumps(json.loads(result.stdout)))",
            *self.command(REPORTER), "--format", "json",
        ])
        self.assertEqual(producer.returncode, 1, producer.stderr)
        self.assertEqual(unsafe.returncode, 0, unsafe.stderr)
        self.assertEqual(safe.returncode, 1, safe.stderr)
        self.assertEqual(json.loads(unsafe.stdout), json.loads(safe.stdout))
        self.assertEqual(json.loads(safe.stdout), json.loads(producer.stdout))

    def load_example(self):
        spec = importlib.util.spec_from_file_location("consume_report_example", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_actual_closed_stdout_retains_reporter_one(self):
        self.input.write_bytes(b"changed")
        child = subprocess.Popen(self.command(SCRIPT), stdin=subprocess.DEVNULL,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        self.addCleanup(child.stderr.close)
        self.addCleanup(child.stdout.close)
        self.addCleanup(lambda: child.kill() if child.poll() is None else None)
        child.stdout.close()
        self.assertEqual(child.wait(timeout=120), 1)
        error = child.stderr.read()
        self.assertIn(b"summary output failed", error)
        self.assertNotIn(b"PRIVATE_", error)
        self.assertNotIn(b"Traceback", error)

    def test_startup_and_timeout_errors_are_private_nonzero(self):
        module = self.load_example()
        for error in (OSError("PRIVATE_START_SENTINEL"),
                      subprocess.TimeoutExpired("PRIVATE_COMMAND_SENTINEL", 120)):
            with self.subTest(error=type(error).__name__), \
                    patch.object(module.subprocess, "run", side_effect=error), \
                    redirect_stdout(io.StringIO()) as output, redirect_stderr(io.StringIO()) as errors:
                self.assertEqual(module.main([str(self.receipt), "--project", str(self.project)]), 5)
                self.assertEqual(output.getvalue(), "")
                self.assertNotIn("PRIVATE_", errors.getvalue())

    def test_parse_failure_never_turns_reporter_failure_into_success(self):
        module = self.load_example()
        for code in range(5):
            with self.subTest(code=code), patch.object(module.subprocess, "run", return_value=
                    subprocess.CompletedProcess([], code, b"PRIVATE_BAD_JSON", b"PRIVATE_ERROR")), \
                    redirect_stdout(io.StringIO()) as output, redirect_stderr(io.StringIO()) as errors:
                self.assertEqual(module.main([str(self.receipt), "--project", str(self.project)]), code or 5)
                self.assertEqual(output.getvalue(), "")
                self.assertNotIn("PRIVATE_", errors.getvalue())

    def test_write_and_flush_failure_never_mask_reporter_failure(self):
        module = self.load_example()
        producer = self.run_command(self.command(REPORTER) + ["--format", "json"])

        class BrokenOutput(io.StringIO):
            def __init__(self, operation):
                super().__init__()
                self.operation = operation

            def write(self, value):
                if self.operation == "write":
                    raise BrokenPipeError("PRIVATE_WRITE_SENTINEL")
                return super().write(value)

            def flush(self):
                if self.operation == "flush":
                    raise OSError("PRIVATE_FLUSH_SENTINEL")

        for operation in ("write", "flush"):
            for code in (0, 1):
                with self.subTest(operation=operation, code=code), \
                        patch.object(module.subprocess, "run", return_value=
                            subprocess.CompletedProcess([], code, producer.stdout, b"")), \
                        redirect_stdout(BrokenOutput(operation)), redirect_stderr(io.StringIO()) as errors:
                    self.assertEqual(module.main([str(self.receipt), "--project", str(self.project)]), code or 5)
                    self.assertNotIn("PRIVATE_", errors.getvalue())


if __name__ == "__main__":
    unittest.main()
