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
                               capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=120,
                               creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        self.assertEqual(child.returncode, expected_exit, child.stderr)
        self.path = next(self.output.glob("*/receipt.json"))
        self.data = json.loads(self.path.read_text(encoding="utf-8"))

    def save(self):
        self.path.write_text(json.dumps(self.data), encoding="utf-8")

    def report(self, *options, project=None):
        result = subprocess.run([sys.executable, str(TOOLS / "report_receipt.py"),
                                 str(self.path), "--project", str(project or self.project),
                                 *options], capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=120,
                               creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
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

    def json_report(self, expected_state, expected_exit, expected_reason, result=None):
        result = self.report("--format", "json") if result is None else result
        self.assertEqual(result.returncode, expected_exit, result.stdout + result.stderr)
        self.assertEqual(result.stderr, "")
        data = json.loads(result.stdout)
        self.assertEqual(set(data), {
            "schema_version", "historical_command_status", "historical_child_exit",
            "recheck_state", "freshness", "reason_code",
        })
        self.assertIs(type(data["schema_version"]), int)
        self.assertEqual(data["schema_version"], 1)
        self.assertEqual(data["recheck_state"], expected_state)
        self.assertEqual(data["reason_code"], expected_reason)
        self.assertIn(data["historical_command_status"], {
            "command_succeeded", "command_failed", "not_run", None,
        })
        self.assertTrue(data["historical_child_exit"] is None
                        or type(data["historical_child_exit"]) is int)
        if data["historical_child_exit"] is not None:
            self.assertGreaterEqual(data["historical_child_exit"], -(2 ** 31))
            self.assertLessEqual(data["historical_child_exit"], 2 ** 32 - 1)
        self.assertIn(data["reason_code"], {
            "observations_match", "observations_differ", "selected_input_missing",
            "invalid_evidence_or_context", "observation_unavailable",
            "historical_failure", "evidence_incomplete",
        })
        expected_freshness = "changed" if expected_state == "different" else (
            "unverifiable" if expected_state in {"invalid", "incomplete"} else "matches")
        self.assertEqual(data["freshness"], expected_freshness)
        return data

    def json_driver(self, body):
        driver = "\n".join([
            "import sys",
            "sys.dont_write_bytecode = True",
            "sys.path.insert(0, sys.argv[1])",
            "import report_receipt",
            body,
            "raise SystemExit(report_receipt.main(sys.argv[2:]))",
        ])
        return subprocess.run(
            [sys.executable, "-c", driver, str(TOOLS), str(self.path),
             "--project", str(self.project), "--format", "json"],
            stdin=subprocess.DEVNULL, capture_output=True, text=True,
            timeout=120, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )

    def json_unavailable_log(self):
        return self.json_driver("\n".join([
            "original = report_receipt.check_receipt.hash_regular",
            "def unavailable(path, *args, **kwargs):",
            "    if path.name == 'command.log':",
            "        raise PermissionError('PRIVATE_IO_SENTINEL')",
            "    return original(path, *args, **kwargs)",
            "report_receipt.check_receipt.hash_regular = unavailable",
        ]))

    def test_json_success_and_default_markdown_preservation(self):
        self.emit()
        default = self.report()
        explicit = self.report("--format", "markdown")
        self.assertEqual(default.returncode, explicit.returncode)
        self.assertEqual(default.stdout, explicit.stdout)
        self.assertEqual(default.stderr, explicit.stderr)
        data = self.json_report("matches", 0, "observations_match")
        self.assertEqual(data["historical_command_status"], "command_succeeded")
        self.assertEqual(data["historical_child_exit"], 0)

    def test_json_historical_failure_and_not_run_remain_distinct(self):
        self.emit("print('PRIVATE_LOG_SENTINEL'); raise SystemExit(7)", expected_exit=7)
        failed = self.json_report("recorded_failure", 3, "historical_failure")
        self.assertEqual(failed["historical_command_status"], "command_failed")
        self.assertEqual(failed["historical_child_exit"], 7)
        self.data["status"] = "not_run"
        self.data["command"].update(status="not_run", exit_code=None)
        self.save()
        not_run = self.json_report("recorded_failure", 3, "historical_failure")
        self.assertEqual(not_run["historical_command_status"], "not_run")
        self.assertIsNone(not_run["historical_child_exit"])

    def test_json_changed_missing_inputs_and_log_keep_historical_zero(self):
        self.emit()
        self.input.write_bytes(b"changed")
        changed = self.json_report("different", 1, "observations_differ")
        self.assertEqual(changed["historical_child_exit"], 0)
        self.input.unlink()
        missing = self.json_report("different", 1, "selected_input_missing")
        self.assertEqual(missing["historical_command_status"], "command_succeeded")
        self.input.write_bytes(b"selected\x00\xff\n")
        log = self.path.with_name("command.log")
        log.write_bytes(b"changed")
        self.json_report("different", 1, "observations_differ")
        log.unlink()
        self.json_report("different", 1, "observations_differ")

    def test_json_invalid_evidence_and_project_withhold_history(self):
        self.emit()
        valid = json.dumps(self.data)
        hostile_command = json.loads(valid)
        hostile_command["command"]["status"] = "PRIVATE_STATUS_SENTINEL"
        hostile_receipt = json.loads(valid)
        hostile_receipt["status"] = "PRIVATE_RECEIPT_STATUS_SENTINEL"
        payloads = [
            json.dumps(hostile_command), json.dumps(hostile_receipt),
            "{PRIVATE_INVALID_SENTINEL", "[]",
            valid[:-1] + ',"PRIVATE_DUPLICATE_SENTINEL":0,"PRIVATE_DUPLICATE_SENTINEL":1}',
            valid.replace('"schema_version": 1', '"schema_version": 2'),
            valid[:-1] + ',"unknown":NaN}',
        ]
        for payload in payloads:
            with self.subTest(payload_kind=payload[:20]):
                self.path.write_text(payload, encoding="utf-8")
                result = self.report("--format", "json")
                data = self.json_report("invalid", 2, "invalid_evidence_or_context", result)
                self.assertIsNone(data["historical_command_status"])
                self.assertIsNone(data["historical_child_exit"])
                self.assertNotIn("PRIVATE_", result.stdout + result.stderr)
        self.path.write_text(valid, encoding="utf-8")
        result = self.report("--format", "json", project=self.root / "PRIVATE_MISSING_SENTINEL")
        self.json_report("invalid", 2, "invalid_evidence_or_context", result)
        self.assertNotIn("PRIVATE_", result.stdout + result.stderr)

    def test_json_incomplete_binding_and_scope_are_not_success(self):
        self.emit()
        del self.data["log_sha256"]
        self.save()
        data = self.json_report("incomplete", 4, "evidence_incomplete")
        self.assertEqual(data["historical_child_exit"], 0)
        self.data["log_sha256"] = hashlib.sha256(self.path.with_name("command.log").read_bytes()).hexdigest()
        self.data.update(inputs_before={}, inputs_after={}, input_scope="no_inputs_selected")
        self.save()
        self.json_report("incomplete", 4, "evidence_incomplete")

    def test_json_unavailable_observation_and_difference_precedence(self):
        self.emit()
        unavailable = self.json_unavailable_log()
        data = self.json_report("incomplete", 4, "observation_unavailable", unavailable)
        self.assertEqual(data["historical_child_exit"], 0)
        self.assertNotIn("PRIVATE_IO_SENTINEL", unavailable.stdout + unavailable.stderr)
        self.input.write_bytes(b"changed")
        self.json_report("different", 1, "observations_differ", self.json_unavailable_log())
        self.input.unlink()
        self.json_report("different", 1, "selected_input_missing", self.json_unavailable_log())

    def test_json_failure_and_incomplete_mixed_conditions(self):
        self.emit("raise SystemExit(7)", expected_exit=7)
        del self.data["log_sha256"]
        self.save()
        self.input.write_bytes(b"changed")
        changed = self.json_report("different", 1, "observations_differ")
        self.assertEqual(changed["historical_child_exit"], 7)
        self.input.write_bytes(b"selected\x00\xff\n")
        incomplete = self.json_report("incomplete", 4, "evidence_incomplete")
        self.assertEqual(incomplete["historical_command_status"], "command_failed")

    def test_json_recorded_mutation_is_not_a_successful_recheck(self):
        self.emit("from pathlib import Path; Path('PRIVATE_INPUT_SENTINEL.txt').write_text('changed')", expected_exit=3)
        data = self.json_report("recorded_failure", 3, "historical_failure")
        self.assertEqual(data["historical_command_status"], "command_succeeded")
        self.assertEqual(data["historical_child_exit"], 0)

    def test_json_omits_private_metadata_and_digests(self):
        self.emit()
        self.data["command"]["argv"] = ["PRIVATE_ARGV_SENTINEL", "<script>private</script>"]
        self.data["command"]["cwd"] = "PRIVATE_CWD_SENTINEL"
        self.data["error"] = "PRIVATE_ERROR_SENTINEL"
        self.data.update(started_at="PRIVATE_DATE_SENTINEL", finished_at="<img src=x>")
        for side in ["git_before", "git_after"]:
            self.data[side].update(root="PRIVATE_ROOT_SENTINEL", porcelain="PRIVATE_DIRTY_SENTINEL")
        for side in ["inputs_before", "inputs_after"]:
            self.data[side][self.input.name].update(resolved_path="PRIVATE_RESOLVED_SENTINEL")
        self.save()
        result = self.report("--format", "json")
        self.json_report("recorded_failure", 3, "historical_failure", result)
        for secret in ["PRIVATE_", "<script>", "<img", str(self.root),
                       json.dumps(str(self.root))[1:-1], self.data["log_sha256"],
                       self.data["inputs_after"][self.input.name]["sha256"]]:
            self.assertNotIn(secret, result.stdout + result.stderr)

    def test_json_private_cli_errors_and_include_command_conflict(self):
        self.emit()
        options = [
            ("--format", "json", "--include-command"),
            ("--format", "PRIVATE_FORMAT_SENTINEL"),
            ("--format", "json", "--PRIVATE_ARG_SENTINEL"),
        ]
        for args in options:
            with self.subTest(options=args):
                result = self.report(*args)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")
                self.assertNotIn("PRIVATE_", result.stderr)
                self.assertNotIn(str(self.root), result.stderr)
                self.assertNotIn("Traceback", result.stderr)

    def test_json_child_exit_uses_existing_portable_disclosure_range(self):
        self.emit("raise SystemExit(7)", expected_exit=7)
        for value, expected in [(-(2 ** 31), -(2 ** 31)),
                                (2 ** 32 - 1, 2 ** 32 - 1),
                                (-(2 ** 31) - 1, None), (2 ** 32, None)]:
            with self.subTest(child_exit=value):
                self.data["command"]["exit_code"] = value
                self.save()
                data = self.json_report("recorded_failure", 3, "historical_failure")
                self.assertEqual(data["historical_child_exit"], expected)

    def test_json_report_is_read_only_and_never_replays_command(self):
        self.emit()
        marker = self.root / "PRIVATE_EXECUTED_SENTINEL"
        self.data["command"]["argv"] = [
            sys.executable, "-c", "from pathlib import Path; Path(" + repr(str(marker)) + ").touch()",
        ]
        self.save()
        before = {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in self.root.rglob("*") if p.is_file()}
        self.json_report("matches", 0, "observations_match")
        after = {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(before, after)
        self.assertFalse(marker.exists())

    def test_json_uses_single_loaded_metadata_snapshot(self):
        self.emit()
        result = self.json_driver("\n".join([
            "import json",
            "original = report_receipt.check_receipt.load_receipt",
            "def replaced(path):",
            "    loaded = original(path)",
            "    replacement = json.loads(path.read_text())",
            "    replacement['status'] = 'command_failed'",
            "    replacement['command'].update(status='command_failed', exit_code=7)",
            "    replacement['wrapper_exit_code'] = 7",
            "    path.write_text(json.dumps(replacement))",
            "    return loaded",
            "report_receipt.check_receipt.load_receipt = replaced",
        ]))
        data = self.json_report("matches", 0, "observations_match", result)
        self.assertEqual(data["historical_command_status"], "command_succeeded")
        self.assertEqual(data["historical_child_exit"], 0)
        self.assertEqual(json.loads(self.path.read_text())["command"]["exit_code"], 7)



if __name__ == "__main__":
    unittest.main()
