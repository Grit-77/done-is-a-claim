"""Exercise command receipts using real subprocesses and temporary files."""

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


RUNNER = Path(__file__).resolve().parents[1] / "tools" / "receipt.py"


class ReceiptTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.cwd = self.root / "work"
        self.cwd.mkdir()
        self.input = self.cwd / "input.txt"
        self.input.write_bytes(b"before\n")

    def run_receipt(self, code=None, inputs=(), command=None, options=(), default_cwd=False):
        argv = [sys.executable, str(RUNNER)]
        if not default_cwd:
            argv += ["--cwd", str(self.cwd)]
        for selected in inputs:
            argv += ["--input", selected]
        argv += list(options) + ["--"]
        argv += command if command is not None else [sys.executable, "-c", code]
        return subprocess.run(argv, cwd=self.cwd, capture_output=True, text=True)

    def receipt(self, result, output=None):
        folders = list((output or self.cwd / ".local" / "receipts").glob("*/receipt.json"))
        self.assertEqual(len(folders), 1, result.stdout + result.stderr)
        return json.loads(folders[0].read_text(encoding="utf-8")), folders[0].parent

    def test_success_records_selected_hashes_times_cwd_and_own_exit(self):
        result = self.run_receipt("print('ordinary command')", inputs=["input.txt"])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        receipt, folder = self.receipt(result)
        self.assertEqual(receipt["status"], "command_succeeded")
        self.assertEqual(receipt["command"]["exit_code"], 0)
        self.assertEqual(receipt["command"]["cwd"], str(self.cwd.resolve()))
        self.assertTrue(receipt["started_at"].endswith("+00:00"))
        self.assertGreaterEqual(receipt["finished_at"], receipt["started_at"])
        digest = hashlib.sha256(b"before\n").hexdigest()
        self.assertEqual(receipt["inputs_before"]["input.txt"]["sha256"], digest)
        self.assertEqual(receipt["inputs_after"]["input.txt"]["sha256"], digest)
        self.assertEqual(receipt["input_scope"], "selected_files_only")
        self.assertIn("ordinary command", (folder / "command.log").read_text())
        self.assertNotIn("verified", receipt)

    def test_failure_retains_child_exit_and_merged_raw_output(self):
        result = self.run_receipt("import os; os.write(1,b'out\\x00\\xff'); os.write(2,b'err'); raise SystemExit(7)")
        self.assertEqual(result.returncode, 7, result.stdout + result.stderr)
        receipt, folder = self.receipt(result)
        self.assertEqual(receipt["status"], "command_failed")
        self.assertEqual(receipt["command"]["exit_code"], 7)
        self.assertEqual((folder / "command.log").read_bytes(), b"out\x00\xfferr")
        self.assertEqual(receipt["log_sha256"], hashlib.sha256(b"out\x00\xfferr").hexdigest())

    def test_log_digest_read_failure_is_explicit_write_failure(self):
        # Windows prevents unlinking an open log; inject only the post-close read
        # failure while preserving real command execution and evidence writes.
        spec = importlib.util.spec_from_file_location("receipt_under_test", RUNNER)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        real_open = Path.open

        def fail_log_read(path, mode="r", *args, **kwargs):
            if path.name == "command.log" and mode == "rb":
                raise OSError("fixture digest read failure")
            return real_open(path, mode, *args, **kwargs)

        with patch.object(Path, "open", fail_log_read):
            result = module.main(["--cwd", str(self.cwd), "--", sys.executable, "-c", "pass"])
        self.assertEqual(result, 2)
        self.assertFalse(list((self.cwd / '.local/receipts').glob('*/receipt.json')))

    def test_argv_shell_characters_and_command_options_are_literal(self):
        arguments = ["$(echo BAD)", "a;b", "x & y", "`echo BAD`", "--input", "space value", 'a"b']
        command = [sys.executable, "-c", "import sys,json; print(json.dumps(sys.argv[1:]))"] + arguments
        result = self.run_receipt(command=command)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        receipt, folder = self.receipt(result)
        self.assertEqual(receipt["command"]["argv"], command)
        self.assertEqual(json.loads((folder / "command.log").read_text()), arguments)

    def test_default_cwd_and_empty_input_scope_are_explicit(self):
        result = self.run_receipt("pass", default_cwd=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        receipt, _ = self.receipt(result)
        self.assertEqual(receipt["input_scope"], "no_inputs_selected")
        self.assertEqual(receipt["inputs_before"], {})
        self.assertEqual(receipt["inputs_after"], {})
        self.assertIn("intermediate", " ".join(receipt["limitations"]))

    def test_changed_input_with_success_returns_three(self):
        result = self.run_receipt("from pathlib import Path; Path('input.txt').write_text('after')", inputs=["input.txt"])
        self.assertEqual(result.returncode, 3, result.stdout + result.stderr)
        receipt, _ = self.receipt(result)
        self.assertEqual(receipt["status"], "inputs_changed")
        self.assertEqual(receipt["command"]["status"], "command_succeeded")
        self.assertEqual(receipt["command"]["exit_code"], 0)
        self.assertEqual(receipt["changed_inputs"], ["input.txt"])

    def test_deleted_input_is_recorded_as_missing_after(self):
        result = self.run_receipt("from pathlib import Path; Path('input.txt').unlink()", inputs=["input.txt"])
        self.assertEqual(result.returncode, 3, result.stdout + result.stderr)
        receipt, _ = self.receipt(result)
        self.assertEqual(receipt["inputs_after"]["input.txt"]["status"], "missing")
        self.assertEqual(receipt["changed_inputs"], ["input.txt"])

    def test_invalid_inputs_refuse_execution(self):
        (self.root / "outside.txt").write_text("outside")
        for selected in ["missing.txt", "../outside.txt", ".", str(self.input.resolve())]:
            with self.subTest(selected=selected):
                output = self.root / ("receipts" + str(len(list(self.root.glob("receipts*")))))
                result = self.run_receipt("from pathlib import Path; Path('executed').touch()", inputs=[selected], options=["--output-dir", str(output)])
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse((self.cwd / "executed").exists())
                receipt, _ = self.receipt(result, output)
                self.assertEqual(receipt["status"], "not_run")
                self.assertIsNone(receipt["command"]["exit_code"])
                self.assertTrue(receipt["error"])

    def test_missing_executable_is_not_run(self):
        result = self.run_receipt(command=[str(self.cwd / "does-not-exist")])
        self.assertNotEqual(result.returncode, 0)
        receipt, _ = self.receipt(result)
        self.assertEqual(receipt["status"], "not_run")
        self.assertIsNone(receipt["command"]["exit_code"])
        self.assertTrue(receipt["error"])

    @unittest.skipUnless(shutil.which("git"), "Git unavailable")
    def test_known_git_observation_loss_is_nonzero_and_unknown_head_change(self):
        for child_exit in [0, 9]:
            with self.subTest(child_exit=child_exit):
                self.cwd = self.root / ("git-work" + str(child_exit))
                self.cwd.mkdir()
                subprocess.run(["git", "init", str(self.cwd)], check=True, capture_output=True)
                output = self.root / ("git-loss" + str(child_exit))
                code = "from pathlib import Path; Path('.git').rename('git-old'); raise SystemExit(" + str(child_exit) + ")"
                result = self.run_receipt(code, options=["--output-dir", str(output)])
                self.assertEqual(result.returncode, 4 if child_exit == 0 else 9, result.stdout + result.stderr)
                receipt, _ = self.receipt(result, output)
                self.assertEqual(receipt["command"]["exit_code"], child_exit)
                self.assertEqual(receipt["status"], "evidence_incomplete" if child_exit == 0 else "command_failed")
                self.assertTrue(receipt.get("evidence_incomplete"))
                self.assertTrue(receipt["git_before"]["available"])
                self.assertFalse(receipt["git_after"]["available"])
                self.assertIsNone(receipt["head_changed"])
                self.assertIn("Git observation", receipt["error"])

    def test_help_without_command_exits_zero_and_writes_nothing(self):
        result = subprocess.run([sys.executable, str(RUNNER), "--help"], cwd=self.cwd, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("--input", result.stdout)
        self.assertIn("--output-dir", result.stdout)
        self.assertFalse((self.cwd / ".local").exists())

    def test_missing_command_fails_without_writing_evidence(self):
        for arguments in [[], ["--"]]:
            with self.subTest(arguments=arguments):
                result = subprocess.run([sys.executable, str(RUNNER), *arguments], cwd=self.cwd, capture_output=True, text=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse((self.cwd / ".local").exists())

    @unittest.skipUnless(os.name == "nt", "Windows implicit batch execution only")
    def test_windows_batch_commands_are_refused_without_shell_side_effects(self):
        for extension in [".cmd", ".bat"]:
            with self.subTest(extension=extension):
                script = self.cwd / ("argv" + extension)
                script.write_text("@echo off\necho %1\necho executed>executed.txt\n")
                output = self.root / ("batch" + extension)
                result = self.run_receipt(command=[str(script), "hello&echo.INJECTED>marker.txt"], options=["--output-dir", str(output)])
                self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertFalse((self.cwd / "marker.txt").exists())
                self.assertFalse((self.cwd / "executed.txt").exists())
                receipt, _ = self.receipt(result, output)
                self.assertEqual(receipt["status"], "not_run")
                self.assertIsNone(receipt["command"]["exit_code"])
                self.assertIn("batch", receipt["error"].lower())

    @unittest.skipUnless(os.name == "nt", "Windows PATHEXT resolution only")
    def test_windows_suffixless_batch_on_path_is_refused(self):
        binary = self.root / "bin"
        binary.mkdir()
        (binary / "receipt-fixture.CMD").write_text("@echo off\necho %1\necho executed>executed.txt\n")
        environment = os.environ.copy()
        environment["PATH"] = str(binary) + os.pathsep + environment.get("PATH", "")
        environment["PATHEXT"] = ".COM;.EXE;.BAT;.CMD"
        result = subprocess.run([sys.executable, str(RUNNER), "--cwd", str(self.cwd), "--", "receipt-fixture", "hello&echo.INJECTED>marker.txt"], cwd=self.cwd, env=environment, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse((self.cwd / "marker.txt").exists())
        self.assertFalse((self.cwd / "executed.txt").exists())
        receipt, _ = self.receipt(result)
        self.assertEqual(receipt["status"], "not_run")
        self.assertIsNone(receipt["command"]["exit_code"])
        self.assertIn("batch", receipt["error"].lower())

    def test_repeated_runs_use_unique_folders_and_preserve_previous_bytes(self):
        output = self.root / "evidence"
        first = self.run_receipt("print('first')", options=["--output-dir", str(output)])
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        _, folder = self.receipt(first, output)
        previous = {path: path.read_bytes() for path in folder.iterdir()}
        second = self.run_receipt("print('second')", options=["--output-dir", str(output)])
        self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
        self.assertEqual(len(list(output.glob("*/receipt.json"))), 2)
        for path, content in previous.items():
            self.assertEqual(path.read_bytes(), content)

    @unittest.skipUnless(shutil.which("git"), "Git unavailable")
    def test_head_change_is_detected_and_dirty_scope_is_named(self):
        def git(*arguments):
            return subprocess.run(["git", "-C", str(self.cwd), *arguments], capture_output=True, text=True, check=True).stdout.strip()
        git("init")
        git("config", "user.email", "fixture@example.invalid")
        git("config", "user.name", "Receipt fixture")
        git("add", "input.txt")
        git("commit", "-m", "initial")
        initial = git("rev-parse", "HEAD")
        (self.cwd / "untracked.txt").write_text("dirty")
        code = "import subprocess; subprocess.run(['git','commit','--allow-empty','-m','changed'],check=True)"
        result = self.run_receipt(code, inputs=["input.txt"])
        self.assertEqual(result.returncode, 3, result.stdout + result.stderr)
        receipt, _ = self.receipt(result)
        self.assertEqual(receipt["git_before"]["head"], initial)
        self.assertNotEqual(receipt["git_after"]["head"], initial)
        self.assertTrue(receipt["git_before"]["dirty"])
        self.assertTrue(receipt["head_changed"])
        self.assertEqual(receipt["git_before"]["dirty_scope"], "whole_worktree_tracked_and_untracked")

    def test_failed_command_keeps_exit_even_when_input_changes(self):
        result = self.run_receipt("from pathlib import Path; Path('input.txt').unlink(); raise SystemExit(9)", inputs=["input.txt"])
        self.assertEqual(result.returncode, 9, result.stdout + result.stderr)
        receipt, _ = self.receipt(result)
        self.assertEqual(receipt["status"], "command_failed")
        self.assertEqual(receipt["changed_inputs"], ["input.txt"])


if __name__ == "__main__":
    unittest.main()
