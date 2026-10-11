"""Shareable Markdown must preserve observations without disclosing local data."""

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


TOOLS = Path(__file__).resolve().parents[1] / "tools"


class ReportReceiptTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.project = self.root / "PRIVATE_PROJECT_SENTINEL"
        self.project.mkdir()
        self.input = self.project / "PRIVATE_INPUT_SENTINEL.txt"
        self.input.write_bytes(b"selected\x00\xff\n")
        self.output = self.root / "evidence"

    def emit(self, code="print('PRIVATE_LOG_SENTINEL')", inputs=True, expected_exit=0):
        argv = [sys.executable, str(TOOLS / "receipt.py"), "--cwd", str(self.project),
                "--output-dir", str(self.output)]
        if inputs:
            argv += ["--input", self.input.name]
        child = subprocess.run(argv + ["--", sys.executable, "-c", code],
                               capture_output=True, text=True)
        self.assertEqual(child.returncode, expected_exit, child.stderr)
        self.path = next(self.output.glob("*/receipt.json"))
        self.data = json.loads(self.path.read_text(encoding="utf-8"))

    def save(self):
        self.path.write_text(json.dumps(self.data), encoding="utf-8")

    def report(self, *options, project=None):
        result = subprocess.run([sys.executable, str(TOOLS / "report_receipt.py"),
                                 str(self.path), "--project", str(project or self.project),
                                 *options], capture_output=True, text=True)
        self.assertNotIn("Traceback", result.stderr)
        return result

    def assert_state(self, result, state, code):
        self.assertEqual(result.returncode, code, result.stdout + result.stderr)
        self.assertIn("| Recheck state | " + state + " |", result.stdout)

    def test_success_report_has_scoped_hashes_and_separate_history(self):
        self.emit()
        report = self.report()
        self.assert_state(report, "matches", 0)
        self.assertIn("| Historical command status | command_succeeded |", report.stdout)
        self.assertIn("| Historical child exit | 0 |", report.stdout)
        self.assertIn("| Selected input count | 1 |", report.stdout)
        self.assertIn("| Log freshness | matches |", report.stdout)
        self.assertIn(hashlib.sha256(self.path.with_name("command.log").read_bytes()).hexdigest(), report.stdout)
        self.assertNotIn("task done", report.stdout.lower())
        self.assertNotIn("tests passed", report.stdout.lower())
        self.assertIn("No test-pass or task-completion verdict is provided.", report.stdout)
        self.assertIn("Non-atomic", report.stdout)
        self.assertEqual(report.stderr, "")

    def test_historical_failure_is_nonzero_even_with_matching_bytes(self):
        self.emit("print('PRIVATE_LOG_SENTINEL'); raise SystemExit(7)", expected_exit=7)
        report = self.report()
        self.assert_state(report, "recorded_failure", 3)
        self.assertIn("| Historical child exit | 7 |", report.stdout)
        self.assertIn("| Historical command status | command_failed |", report.stdout)
        self.assertIn("| Log freshness | matches |", report.stdout)
        self.assertIn("matches: 1", report.stdout)

    def test_historical_mutation_remains_nonzero(self):
        self.emit("from pathlib import Path; Path('PRIVATE_INPUT_SENTINEL.txt').write_text('changed')", expected_exit=3)
        self.assert_state(self.report(), "recorded_failure", 3)

    def test_changed_or_missing_input_is_different(self):
        self.emit()
        self.input.write_bytes(b"changed")
        report = self.report()
        self.assert_state(report, "different", 1)
        self.assertIn("different: 1", report.stdout)
        self.input.unlink()
        report = self.report()
        self.assert_state(report, "different", 1)
        self.assertIn("missing: 1", report.stdout)

    def test_changed_or_missing_log_is_different(self):
        self.emit()
        log = self.path.with_name("command.log")
        log.write_bytes(b"changed")
        self.assert_state(self.report(), "different", 1)
        log.unlink()
        self.assert_state(self.report(), "different", 1)

    def test_legacy_log_binding_and_missing_observations_are_incomplete(self):
        self.emit()
        del self.data["log_sha256"]
        self.save()
        report = self.report()
        self.assert_state(report, "incomplete", 4)
        self.assertIn("| Log freshness | unbound |", report.stdout)
        self.data["log_sha256"] = hashlib.sha256(self.path.with_name("command.log").read_bytes()).hexdigest()
        self.data["inputs_after"] = {}
        self.save()
        self.assert_state(self.report(), "incomplete", 4)

    def test_real_no_input_capture_is_incomplete(self):
        self.emit(inputs=False)
        report = self.report()
        self.assert_state(report, "incomplete", 4)
        self.assertIn("| Selected input count | 0 |", report.stdout)

    def test_default_omits_secrets_paths_and_arbitrary_hostile_metadata(self):
        self.emit()
        self.data["command"]["argv"] = ["PRIVATE_ARGV_SENTINEL", "```\n[link](https://evil.invalid)\n<script>bad</script>\x1b[31m"]
        self.data["command"]["cwd"] = "PRIVATE_CWD_SENTINEL"
        self.data["error"] = "PRIVATE_ERROR_SENTINEL"
        for side in ["git_before", "git_after"]:
            self.data[side].update(root="PRIVATE_ROOT_SENTINEL", porcelain="PRIVATE_DIRTY_SENTINEL",
                                  errors=["PRIVATE_GIT_ERROR_SENTINEL"])
        for field in ["inputs_before", "inputs_after"]:
            self.data[field][self.input.name].update(resolved_path="PRIVATE_RESOLVED_SENTINEL", error="PRIVATE_SNAPSHOT_SENTINEL")
        self.data.update(started_at="PRIVATE_DATE_SENTINEL", finished_at="<img src=x>",
                         limitations=["PRIVATE_LIMITATION_SENTINEL"])
        self.save()
        report = self.report()
        self.assert_state(report, "recorded_failure", 3)
        combined = report.stdout + report.stderr
        self.assertNotIn("PRIVATE_", combined)
        for forbidden in [str(self.root), "<script>", "evil.invalid", "<img", "\x1b"]:
            self.assertNotIn(forbidden, combined)

    def test_invalid_diagnostics_never_echo_sensitive_values(self):
        self.emit()
        valid = json.dumps(self.data)
        payloads = ["{PRIVATE_INVALID_SENTINEL", "[]", valid[:-1] + ',"PRIVATE_DUPLICATE_SENTINEL":0,"PRIVATE_DUPLICATE_SENTINEL":1}',
                    valid.replace('"schema_version": 1', '"schema_version": 2'),
                    valid[:-1] + ',"unknown":NaN}', '[' * 2000 + '0' + ']' * 2000,
                    '{"padding":"' + 'x' * (1024 * 1024) + '"}']
        for payload in payloads:
            with self.subTest(prefix=payload[:50]):
                self.path.write_text(payload, encoding="utf-8")
                report = self.report()
                self.assert_state(report, "invalid", 2)
                self.assertNotIn("PRIVATE_", report.stdout + report.stderr)

    def test_invalid_project_diagnostics_are_private(self):
        self.emit()
        self.assert_state(self.report(project=self.root / "PRIVATE_MISSING_SENTINEL"), "invalid", 2)
        report = self.report(project=self.input)
        self.assert_state(report, "invalid", 2)
        self.assertNotIn("PRIVATE_", report.stdout + report.stderr)

    def test_cli_errors_never_echo_unknown_arguments(self):
        self.emit()
        report = self.report("--PRIVATE_UNKNOWN_ARGUMENT_SENTINEL")
        self.assertEqual(report.returncode, 2)
        self.assertNotIn("PRIVATE_", report.stdout + report.stderr)
        self.assertNotIn("Traceback", report.stderr)

    def test_opt_in_argv_cannot_escape_fence_or_inject_links_html_controls(self):
        self.emit()
        self.data["command"]["argv"] = ["PRIVATE_ARGV_SENTINEL", "```\n[link](https://evil.invalid)\n<script>x</script>\x1b\u202e"]
        self.save()
        report = self.report("--include-command")
        self.assert_state(report, "matches", 0)
        self.assertIn("PRIVATE_ARGV_SENTINEL", report.stdout)
        self.assertIn("may contain secrets", report.stdout)
        self.assertIn("not a runnable shell command", report.stdout)
        self.assertEqual(report.stdout.count("```"), 2)
        self.assertNotIn("<script>", report.stdout)
        self.assertNotIn("\x1b", report.stdout)
        self.assertNotIn("\u202e", report.stdout)
        self.assertIn("\\u0060", report.stdout)
        self.assertNotIn("PRIVATE_LOG_SENTINEL", report.stdout + report.stderr)

    def test_command_output_is_bounded_even_for_large_metadata(self):
        self.emit()
        self.data["command"]["argv"] = ["PRIVATE_ARGV_SENTINEL", "`" * 100000]
        self.save()
        report = self.report("--include-command")
        self.assert_state(report, "matches", 0)
        self.assertLess(len(report.stdout), 12000)
        self.assertIn("truncated", report.stdout)

    def test_report_does_not_write_or_execute_recorded_argv(self):
        self.emit()
        marker = self.root / "executed"
        self.data["command"]["argv"] = [sys.executable, "-c", "from pathlib import Path; Path(" + repr(str(marker)) + ").touch()"]
        self.save()
        before = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in self.root.rglob("*") if path.is_file()}
        self.assert_state(self.report(), "matches", 0)
        self.assert_state(self.report("--include-command"), "matches", 0)
        after = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in self.root.rglob("*") if path.is_file()}
        self.assertEqual(before, after)
        self.assertFalse(marker.exists())

    def test_report_imports_create_no_bytecode_files(self):
        self.emit()
        isolated = self.root / "isolated_tools"
        isolated.mkdir()
        for name in ["report_receipt.py", "check_receipt.py"]:
            source = TOOLS / name
            self.assertTrue(source.is_file(), "reporter is not implemented")
            shutil.copyfile(source, isolated / name)
        before = {str(path): path.read_bytes() for path in isolated.rglob("*") if path.is_file()}
        report = subprocess.run([sys.executable, str(isolated / "report_receipt.py"),
                                 str(self.path), "--project", str(self.project)], capture_output=True, text=True)
        self.assert_state(report, "matches", 0)
        after = {str(path): path.read_bytes() for path in isolated.rglob("*") if path.is_file()}
        self.assertEqual(before, after)

    def test_receipt_replacement_after_load_cannot_mix_metadata_revisions(self):
        self.emit()
        self.data.update(started_at="2026-10-11T12:34:56+00:00")
        self.data["command"]["argv"] = ["OLD_ARGV_SNAPSHOT"]
        self.save()
        # A real file replacement at the parser boundary simulates concurrent
        # editing; comparison must use the exact metadata tuple already read.
        driver = "\n".join([
            "import json, sys",
            "sys.dont_write_bytecode = True",
            "sys.path.insert(0, " + repr(str(TOOLS)) + ")",
            "import report_receipt",
            "original = report_receipt.check_receipt.load_receipt",
            "def replaced(path):",
            "    loaded = original(path)",
            "    replacement = json.loads(path.read_text())",
            "    replacement['status'] = 'command_failed'",
            "    replacement['command'].update(status='command_failed', exit_code=7, argv=['NEW_ARGV_SNAPSHOT'])",
            "    replacement['wrapper_exit_code'] = 7",
            "    replacement['started_at'] = '2026-10-12T12:34:56+00:00'",
            "    path.write_text(json.dumps(replacement))",
            "    return loaded",
            "report_receipt.check_receipt.load_receipt = replaced",
            "raise SystemExit(report_receipt.main(" + repr([str(self.path), "--project", str(self.project), "--include-command"]) + "))",
        ])
        report = subprocess.run([sys.executable, "-c", driver], capture_output=True, text=True)
        self.assert_state(report, "matches", 0)
        self.assertIn("2026-10-11T12:34:56+00:00", report.stdout)
        self.assertIn("OLD_ARGV_SNAPSHOT", report.stdout)
        self.assertNotIn("NEW_ARGV_SNAPSHOT", report.stdout)
        self.assertNotIn("2026-10-12", report.stdout)

    def test_dates_accept_only_strict_calendar_timestamps(self):
        self.emit()
        self.data.update(started_at="2026-10-11T12:34:56.123456+00:00", finished_at="2026-02-30T12:34:56+00:00")
        self.save()
        report = self.report()
        self.assertIn("2026-10-11T12:34:56.123456+00:00", report.stdout)
        self.assertNotIn("2026-02-30", report.stdout)
        for date in ["20261011", "2026-10-11T12:34:56\n<script>", None, {}, "2026-10-11T12:34:56", "2026-10-11T12:34:56+24:00"]:
            with self.subTest(date=date):
                self.data["started_at"] = date
                self.save()
                report = self.report()
                self.assert_state(report, "matches", 0)
                self.assertNotIn("<script>", report.stdout)

    def test_fractional_timestamp_displays_preserve_original_precision(self):
        self.emit()
        for fraction in ["1", "12", "123", "1234", "12345", "123456"]:
            with self.subTest(fraction=fraction):
                stamp = "2026-10-11T12:34:56." + fraction + "+00:00"
                self.data.update(started_at=stamp, finished_at="2026-02-30T12:34:56." + fraction + "Z")
                self.save()
                report = self.report()
                self.assert_state(report, "matches", 0)
                self.assertIn("| Recorded start | " + stamp + " |", report.stdout)
                self.assertIn("| Recorded finish | unavailable |", report.stdout)

    def test_timestamp_validation_handles_python310_fraction_parser(self):
        stamps = ["2026-10-11T12:34:56." + digits + "Z" for digits in ["1", "12", "1234", "12345"]]
        # This host uses a newer Python. Keep calendar validation real while
        # emulating the older parser's only relevant boundary: 3/6 digits.
        driver = "\n".join([
            "import re, sys",
            "from datetime import datetime",
            "sys.dont_write_bytecode = True",
            "sys.path.insert(0, " + repr(str(TOOLS)) + ")",
            "import report_receipt",
            "class Datetime310:",
            "    @staticmethod",
            "    def fromisoformat(value):",
            "        fraction = re.search(r'\\.([0-9]+)', value)",
            "        if fraction and len(fraction.group(1)) not in (3, 6):",
            "            raise ValueError('older parser fraction boundary')",
            "        return datetime.fromisoformat(value)",
            "report_receipt.datetime = Datetime310",
            "for value in " + repr(stamps + ["2026-02-30T12:34:56.1Z"]) + ":",
            "    print(report_receipt.safe_timestamp(value))",
        ])
        result = subprocess.run([sys.executable, "-c", driver], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(), stamps + ["unavailable"])

    @unittest.skipUnless(shutil.which("git"), "Git unavailable")
    def test_changed_head_reports_both_hashes_and_nonzero(self):
        def git(*args):
            return subprocess.run(["git", "-C", str(self.project), *args], capture_output=True, text=True, check=True).stdout.strip()
        git("init")
        git("config", "user.name", "Receipt fixture")
        git("config", "user.email", "fixture@example.invalid")
        git("add", self.input.name)
        git("commit", "-m", "initial")
        self.emit()
        before = git("rev-parse", "HEAD")
        self.assert_state(self.report(), "matches", 0)
        git("commit", "--allow-empty", "-m", "next")
        after = git("rev-parse", "HEAD")
        report = self.report()
        self.assert_state(report, "different", 1)
        self.assertIn(before, report.stdout)
        self.assertIn(after, report.stdout)


if __name__ == "__main__":
    unittest.main()
