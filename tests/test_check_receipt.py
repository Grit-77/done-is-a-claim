"""Read-only consistency checks against real emitted receipts and local Git."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


TOOLS = Path(__file__).resolve().parents[1] / "tools"


class CheckReceiptTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.project = self.root / "project"
        self.project.mkdir()
        (self.project / "input.txt").write_bytes(b"selected\x00\xff\n")
        self.output = self.root / "evidence"

    def emit(self, code="import os; os.write(1,b'log\\x00\\xff')", inputs=("input.txt",)):
        argv = [sys.executable, str(TOOLS / "receipt.py"), "--cwd", str(self.project), "--output-dir", str(self.output)]
        for selected in inputs:
            argv += ["--input", selected]
        result = subprocess.run(argv + ["--", sys.executable, "-c", code], capture_output=True, text=True)
        self.receipt_path = next(self.output.glob("*/receipt.json"))
        self.data = json.loads(self.receipt_path.read_text())
        self.assertEqual(self.data["command"]["exit_code"], 7 if "SystemExit(7)" in code else 0, result.stderr)
        return self.receipt_path

    def save(self):
        self.receipt_path.write_text(json.dumps(self.data), encoding="utf-8")

    def check(self, root=None):
        result = subprocess.run([sys.executable, str(TOOLS / "check_receipt.py"), str(self.receipt_path), "--project", str(root or self.project), "--json"], capture_output=True, text=True)
        self.assertTrue(result.stdout.strip(), result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        return result.returncode, json.loads(result.stdout)

    def test_unchanged_emitted_control_matches_binary_bytes_without_writes(self):
        self.emit()
        before = {str(p): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        code, report = self.check()
        self.assertEqual(code, 0)
        self.assertEqual(report["state"], "matches")
        self.assertEqual(report["log"]["state"], "matches")
        self.assertEqual(report["inputs"]["input.txt"]["state"], "matches")
        self.assertEqual(report["git"]["state"], "outside_scope")
        self.assertEqual(before, {str(p): p.read_bytes() for p in self.root.rglob("*") if p.is_file()})

    def test_current_file_mutation_or_deletion_cannot_match(self):
        self.emit()
        (self.project / "input.txt").write_bytes(b"different")
        self.assertEqual(self.check()[1]["inputs"]["input.txt"]["state"], "different")
        (self.project / "input.txt").unlink()
        code, report = self.check()
        self.assertEqual(code, 1)
        self.assertEqual(report["inputs"]["input.txt"]["state"], "missing")

    def test_mapping_to_moved_same_content_ignores_historical_absolute_paths(self):
        self.emit()
        moved = self.root / "moved"
        self.project.rename(moved)
        self.assertEqual(self.check(moved)[0], 0)

    def test_appended_and_truncated_log_are_different(self):
        self.emit()
        log = self.receipt_path.with_name("command.log")
        original = log.read_bytes()
        for content in [original + b"append", original[:1]]:
            with self.subTest(content=content):
                log.write_bytes(content)
                code, report = self.check()
                self.assertEqual(code, 1)
                self.assertEqual(report["log"]["state"], "different")

    def test_missing_log_is_explicit_non_success(self):
        self.emit()
        self.receipt_path.with_name("command.log").unlink()
        code, report = self.check()
        self.assertEqual(code, 1)
        self.assertEqual(report["log"]["state"], "missing")

    def test_legacy_missing_digest_and_no_inputs_are_incomplete(self):
        self.emit()
        del self.data["log_sha256"]
        self.save()
        code, report = self.check()
        self.assertEqual(code, 4)
        self.assertEqual(report["log"]["state"], "unbound")
        self.data["log_sha256"] = hashlib.sha256(self.receipt_path.with_name("command.log").read_bytes()).hexdigest()
        self.data["inputs_before"] = {}
        self.data["inputs_after"] = {}
        self.data["input_scope"] = "no_inputs_selected"
        self.save()
        self.assertEqual(self.check()[0], 4)

    def test_real_no_input_capture_is_incomplete(self):
        self.emit(inputs=())
        code, report = self.check()
        self.assertEqual(code, 4)
        self.assertEqual(report["inputs"], {})

    def test_nonregular_log_and_input_are_invalid(self):
        self.emit()
        selected = self.project / "input.txt"
        selected.unlink()
        selected.mkdir()
        self.assertEqual(self.check()[0], 2)
        selected.rmdir()
        selected.write_bytes(b"selected\x00\xff\n")
        log = self.receipt_path.with_name("command.log")
        log.unlink()
        log.mkdir()
        self.assertEqual(self.check()[0], 2)

    def test_preserved_failed_command_is_non_success_with_matching_components(self):
        self.emit("print('failed'); raise SystemExit(7)")
        code, report = self.check()
        self.assertEqual(code, 3)
        self.assertEqual(report["state"], "recorded_failure")
        self.assertEqual(report["recorded"]["exit_code"], 7)
        self.assertEqual(report["log"]["state"], "matches")
        self.assertEqual(report["inputs"]["input.txt"]["state"], "matches")

    def test_preserved_input_mutation_is_non_success_despite_current_match(self):
        self.emit("from pathlib import Path; Path('input.txt').write_bytes(b'changed')")
        code, report = self.check()
        self.assertEqual(code, 3)
        self.assertEqual(report["recorded"]["status"], "inputs_changed")
        self.assertEqual(report["inputs"]["input.txt"]["state"], "matches")

    def test_hostile_argv_is_never_executed_and_old_roots_never_followed(self):
        self.emit()
        marker = self.root / "executed"
        self.data["command"]["argv"] = [sys.executable, "-c", "from pathlib import Path; Path(" + repr(str(marker)) + ").touch()"]
        self.data["command"]["cwd"] = str(self.root / "nonexistent")
        self.data["inputs_after"]["input.txt"]["resolved_path"] = str(self.root / "not-followed")
        self.save()
        self.assertEqual(self.check()[0], 0)
        self.assertFalse(marker.exists())

    def test_required_explicit_existing_project(self):
        self.emit()
        for options in [[], ["--project", str(self.root / "missing")], ["--project", str(self.project / "input.txt")]]:
            result = subprocess.run([sys.executable, str(TOOLS / "check_receipt.py"), str(self.receipt_path), *options], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertNotIn("Traceback", result.stderr)

    def test_malformed_unsupported_duplicate_nan_and_deep_json_are_invalid(self):
        self.emit()
        valid = json.dumps(self.data)
        payloads = ["{", "[]", valid.replace('"schema_version": 1', '"schema_version": 2'), valid.replace('"schema_version": 1', '"schema_version": true'), valid[:-1] + ',"schema_version":1}', valid[:-1] + ',"unknown":NaN}', valid[:-1] + ',"unknown":1e9999}', valid[:-1] + ',"unknown":' + '[' * 100 + '0' + ']' * 100 + '}', '[' * 2000 + '0' + ']' * 2000, '{"padding":"' + 'x' * (1024 * 1024) + '"}']
        for payload in payloads:
            with self.subTest(prefix=payload[:60]):
                self.receipt_path.write_text(payload)
                code, report = self.check()
                self.assertEqual(code, 2)
                self.assertEqual(report["state"], "invalid")

    def test_required_types_and_digests_are_validated(self):
        self.emit()
        original = json.loads(json.dumps(self.data))
        mutations = [lambda d: d["command"].update(exit_code=True), lambda d: d.update(changed_inputs="input.txt"), lambda d: d.update(evidence_incomplete=0), lambda d: d.update(log_sha256="z" * 64), lambda d: d["inputs_after"]["input.txt"].update(sha256="abcd"), lambda d: d.update(git_after={"available": True, "head": "bad", "dirty": False}), lambda d: d.update(wrapper_exit_code=False), lambda d: d.update(status=[]), lambda d: d["command"].update(status={}), lambda d: d["inputs_after"]["input.txt"].update(status=[]), lambda d: d.update(input_scope={})]
        for mutation in mutations:
            self.data = json.loads(json.dumps(original))
            mutation(self.data)
            self.save()
            with self.subTest(data=self.data):
                self.assertEqual(self.check()[0], 2)

    def test_portable_windows_separators_are_normalized(self):
        (self.project / "nested").mkdir()
        (self.project / "nested/file.txt").write_bytes(b"nested")
        self.emit(inputs=("nested/file.txt",))
        for field in ["inputs_before", "inputs_after"]:
            self.data[field]["nested\\file.txt"] = self.data[field].pop("nested/file.txt")
        self.save()
        self.assertEqual(self.check()[0], 0)

    def test_input_traversal_absolute_drive_unc_ads_and_aliases_are_invalid(self):
        self.emit()
        original = json.loads(json.dumps(self.data))
        for name in ["../input.txt", "..\\input.txt", "/input.txt", "C:input.txt", "C:\\input.txt", "\\\\server\\share", "input.txt:stream", "./input.txt", "input.txt.", "NUL", "a//b"]:
            self.data = json.loads(json.dumps(original))
            for field in ["inputs_before", "inputs_after"]:
                self.data[field][name] = self.data[field].pop("input.txt")
            self.save()
            with self.subTest(name=name):
                self.assertEqual(self.check()[0], 2)
        self.data = original
        for field in ["inputs_before", "inputs_after"]:
            self.data[field]["INPUT.TXT"] = self.data[field]["input.txt"]
        self.save()
        self.assertEqual(self.check()[0], 2)

    def test_log_file_metadata_cannot_redirect_reads(self):
        self.emit()
        for name in ["../command.log", str(self.receipt_path.with_name("command.log")), "nested/command.log", "COMMAND.LOG"]:
            self.data["log_file"] = name
            self.save()
            with self.subTest(name=name):
                self.assertEqual(self.check()[0], 2)

    def test_symlink_log_and_escaping_input_are_rejected(self):
        self.emit()
        outside = self.root / "outside"
        outside.write_bytes(b"selected\x00\xff\n")
        probe = self.root / "probe"
        try:
            probe.symlink_to(outside)
        except OSError as error:
            self.skipTest("symlink creation unavailable: " + str(error))
        probe.unlink()
        (self.project / "input.txt").unlink()
        (self.project / "input.txt").symlink_to(outside)
        self.assertEqual(self.check()[0], 2)
        (self.project / "input.txt").unlink()
        (self.project / "input.txt").write_bytes(outside.read_bytes())
        log = self.receipt_path.with_name("command.log")
        log.unlink()
        log.symlink_to(outside)
        self.assertEqual(self.check()[0], 2)

    def git(self, *arguments):
        return subprocess.run(["git", "-C", str(self.project), *arguments], capture_output=True, text=True, check=True).stdout.strip()

    def init_git(self):
        self.git("init")
        self.git("config", "user.name", "Receipt fixture")
        self.git("config", "user.email", "fixture@example.invalid")
        self.git("add", "input.txt")
        self.git("commit", "-m", "initial")

    @unittest.skipUnless(shutil.which("git"), "Git unavailable")
    def test_changed_head_and_unavailable_expected_git_are_non_success(self):
        self.init_git()
        self.emit()
        self.assertEqual(self.check()[0], 0)
        self.git("commit", "--allow-empty", "-m", "next")
        code, report = self.check()
        self.assertEqual(code, 1)
        self.assertEqual(report["git"]["state"], "different")
        (self.project / ".git").rename(self.project / "old-git")
        code, report = self.check()
        self.assertEqual(code, 4)
        self.assertEqual(report["git"]["state"], "unavailable")

    @unittest.skipUnless(shutil.which("git"), "Git unavailable")
    def test_recorded_lost_git_and_unborn_head_remain_incomplete(self):
        self.git("init")
        self.emit()
        self.assertEqual(self.check()[0], 4)
        self.data["git_before"]["head"] = "a" * 40
        self.data["git_after"]["available"] = False
        self.data["evidence_incomplete"] = True
        self.save()
        self.assertEqual(self.check()[0], 4)

    @unittest.skipUnless(shutil.which("git"), "Git unavailable")
    def test_unavailable_historical_head_or_dirty_is_not_silently_matches(self):
        self.init_git()
        self.emit()
        original = json.loads(json.dumps(self.data))
        for field, side in [("head", "git_before"), ("dirty", "git_before"), ("dirty", "git_after")]:
            self.data = json.loads(json.dumps(original))
            self.data[side][field] = None
            self.save()
            with self.subTest(field=field, side=side):
                code, report = self.check()
                self.assertEqual(code, 4)
                self.assertEqual(report["git"]["state"], "matches")

    @unittest.skipUnless(shutil.which("git"), "Git unavailable")
    def test_recorded_head_mutation_remains_failure_even_if_flag_was_cleared(self):
        self.init_git()
        self.emit("import subprocess; subprocess.run(['git','commit','--allow-empty','-m','child'],check=True)")
        code, report = self.check()
        self.assertEqual(code, 3)
        self.assertEqual(report["git"]["state"], "matches")
        self.data.update(status="command_succeeded", head_changed=False, wrapper_exit_code=0)
        self.save()
        self.assertEqual(self.check()[0], 3)

    @unittest.skipUnless(os.name == "nt", "Windows junction confinement")
    def test_escaping_directory_junction_is_invalid(self):
        self.emit()
        outside = self.root / "outside-dir"
        outside.mkdir()
        (outside / "input.txt").write_bytes(b"selected\x00\xff\n")
        link = self.project / "escape"
        self.addCleanup(lambda: os.rmdir(link) if link.exists() else None)
        result = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(outside)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for field in ["inputs_before", "inputs_after"]:
            self.data[field]["escape/input.txt"] = self.data[field].pop("input.txt")
        self.save()
        self.assertEqual(self.check()[0], 2)

    @unittest.skipUnless(shutil.which("git"), "Git unavailable")
    def test_inherited_git_dir_cannot_redirect_current_head_comparison(self):
        self.init_git()
        self.emit()
        environment = os.environ.copy()
        environment["GIT_DIR"] = str(self.root / "not-the-project")
        result = subprocess.run([sys.executable, str(TOOLS / "check_receipt.py"), str(self.receipt_path), "--project", str(self.project), "--json"], capture_output=True, text=True, env=environment)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
