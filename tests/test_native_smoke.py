"""Offline smoke fixture acceptance: bad controls fail, correct CSV passes."""

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "native_smoke.py"
GOOD_REPORT = '''import csv
import io

def render_csv(rows, columns):
    stream = io.StringIO(newline="")
    writer = csv.writer(stream)
    writer.writerow(columns)
    for row in rows:
        writer.writerow([row[column] for column in columns])
    return stream.getvalue()
'''


class NativeSmokeTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        # Resolve the OS temporary root before composing paths (Windows aliases).
        self.parent = Path(temporary.name).resolve()
        self.project = self.parent / "exercise"

    def cli(self, *arguments):
        return subprocess.run(
            [sys.executable, "-B", str(TOOL), *map(str, arguments)],
            capture_output=True, text=True, encoding="utf-8", timeout=15,
            check=False,
        )

    def create(self):
        result = self.cli("create", "--project", self.project)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def verify(self, expected_exit, *arguments):
        result = self.cli("verify", "--project", self.project, "--json", *arguments)
        self.assertEqual(result.returncode, expected_exit, result.stdout + result.stderr)
        observation = json.loads(result.stdout)
        self.assertEqual(observation["schema"], 1)
        return observation

    def correct_report(self, prefix=""):
        (self.project / "report.py").write_text(prefix + GOOD_REPORT, encoding="utf-8")

    def snapshot(self, directory):
        return {str(path.relative_to(directory)): path.read_bytes()
                for path in directory.rglob("*") if path.is_file()}

    def test_starter_passes_two_visible_checks_but_fails_independent_acceptance(self):
        self.create()
        self.assertEqual(set(self.snapshot(self.project)),
                         {"report.py", "test_report.py", "TASK.md"})
        basic = subprocess.run(
            [sys.executable, "-B", "-m", "unittest", "test_report"],
            cwd=self.project, capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(basic.returncode, 0, basic.stdout + basic.stderr)
        self.assertIn("Ran 2 tests", basic.stderr)
        observed = self.verify(1)
        self.assertEqual(observed["state"], "failed")
        self.assertTrue(observed["protected"]["matched"])
        self.assertGreater(observed["checks"]["failed"], 0)
        self.assertEqual(observed["checks"]["executed"], len(observed["cases"]))
        self.assertEqual(observed["child"]["exit_code"], 1)

    def test_correct_csv_passes_with_exact_check_count_and_leaves_inputs_unchanged(self):
        self.create()
        self.correct_report()
        before = self.snapshot(self.project)
        observed = self.verify(0)
        self.assertIn("scratch", observed)
        self.assertEqual(observed["state"], "passed")
        self.assertEqual(observed["checks"]["failed"], 0)
        self.assertGreaterEqual(observed["checks"]["executed"], 7)
        self.assertTrue(all(case["passed"] for case in observed["cases"]))
        self.assertEqual(observed["child"]["exit_code"], 0)
        self.assertFalse(observed["inputs_changed"])
        self.assertEqual(len(observed["candidate_sha256"]), 64)
        self.assertEqual(before, self.snapshot(self.project))

    def test_result_directory_is_inside_accessible_project_and_removed_after_pass(self):
        self.create()
        self.correct_report(
            "import sys\nfrom pathlib import Path\n"
            "scratch = Path(sys.argv[-1]).parent\n"
            "if scratch.parent != Path(__file__).parent:\n"
            "    raise RuntimeError('result channel outside project write scope')\n")
        before = self.snapshot(self.project)
        observed = self.verify(0)
        self.assertEqual(Path(observed["scratch"]["path"]).parent, self.project)
        self.assertTrue(observed["scratch"]["removed"])
        self.assertIsNone(observed["scratch"]["retained_path"])
        self.assertEqual(before, self.snapshot(self.project))
        self.assertEqual(set(path.name for path in self.project.iterdir()),
                         {"report.py", "test_report.py", "TASK.md"})

    def test_scratch_is_removed_after_failed_crashed_and_timed_out_candidates(self):
        self.create()
        for source, expected_exit, arguments in (
            ('def render_csv(rows, columns): return "bad"\n', 1, ()),
            ('import os\nos._exit(9)\n', 2, ()),
            ('import time\ntime.sleep(10)\n', 3, ("--timeout", "0.2")),
        ):
            with self.subTest(source=source):
                (self.project / "report.py").write_text(source, encoding="utf-8")
                before = self.snapshot(self.project)
                observed = self.verify(expected_exit, *arguments)
                self.assertIn("scratch", observed)
                self.assertTrue(observed["scratch"]["removed"])
                self.assertFalse(Path(observed["scratch"]["path"]).exists())
                self.assertEqual(before, self.snapshot(self.project))

    def test_unexpected_scratch_contents_are_retained_and_cannot_report_success(self):
        self.create()
        self.correct_report(
            "import sys\nfrom pathlib import Path\n"
            "(Path(sys.argv[-1]).parent / 'keep.txt').write_text('preserve', encoding='utf-8')\n")
        observed = self.verify(2)
        self.assertEqual(observed["state"], "invalid")
        self.assertEqual(observed["checks"]["passed"], 8)
        self.assertEqual(observed["child"]["exit_code"], 0)
        scratch = Path(observed["scratch"]["retained_path"])
        self.assertEqual(scratch.parent, self.project)
        self.assertFalse(observed["scratch"]["removed"])
        self.assertEqual((scratch / "keep.txt").read_text(encoding="utf-8"), "preserve")
        self.assertTrue(any("scratch" in message for message in observed["diagnostics"]))

    def test_cleanup_error_retains_scratch_and_invalidates_otherwise_passing_check(self):
        self.create()
        self.correct_report()
        spec = importlib.util.spec_from_file_location("native_smoke_cleanup_test", TOOL)
        tool = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(tool)
        original_rmdir = Path.rmdir

        def refuse_scratch_removal(path):
            if path.name.startswith(".claim-smoke-result-"):
                raise PermissionError("synthetic cleanup denial")
            return original_rmdir(path)

        with patch.object(Path, "rmdir", refuse_scratch_removal):
            observed, exit_code = tool.verify_project(self.project)
        self.assertEqual(exit_code, 2)
        self.assertEqual(observed["state"], "invalid")
        self.assertEqual(observed["checks"]["passed"], 8)
        self.assertTrue(Path(observed["scratch"]["retained_path"]).is_dir())
        self.assertIn("synthetic cleanup denial", observed["scratch"]["error"])

    def test_scratch_replaced_by_link_or_junction_does_not_delete_external_contents(self):
        self.create()
        outside = self.parent / "outside-scratch"
        outside.mkdir()
        (outside / "keep.txt").write_text("preserve", encoding="utf-8")

        def remove_fixture_links():
            for path in self.project.glob(".claim-smoke-result-*"):
                if path.is_symlink():
                    path.unlink()
                elif os.name == "nt" and path.lstat().st_file_attributes & 0x400:
                    os.rmdir(path)

        self.addCleanup(remove_fixture_links)
        self.correct_report(
            "import os, subprocess, sys\nfrom pathlib import Path\n"
            "scratch = Path(sys.argv[-1]).parent\n"
            "scratch.rmdir()\n"
            f"outside = Path({str(outside)!r})\n"
            "if os.name == 'nt':\n"
            "    subprocess.run(['cmd', '/c', 'mklink', '/J', str(scratch), str(outside)],\n"
            "                   check=True, capture_output=True, timeout=5)\n"
            "else:\n"
            "    scratch.symlink_to(outside, target_is_directory=True)\n")
        observed = self.verify(2)
        self.assertEqual(observed["state"], "invalid")
        self.assertIn("link or reparse", observed["scratch"]["error"])
        self.assertIsNotNone(observed["scratch"]["retained_path"])
        self.assertEqual((outside / "keep.txt").read_text(encoding="utf-8"), "preserve")
        # Child output followed its own substituted link; parent must not remove it.
        self.assertTrue((outside / "result.json").is_file())

    def test_candidate_stdout_cannot_replace_structured_results(self):
        self.create()
        self.correct_report('print(\'{"state": "passed"}\')\n')
        observed = self.verify(0)
        self.assertIn('"state": "passed"', observed["child"]["stdout"])
        (self.project / "report.py").write_text(
            'print(\'{"state": "passed"}\')\ndef render_csv(rows, columns): return "pass"\n',
            encoding="utf-8",
        )
        self.assertEqual(self.verify(1)["state"], "failed")

    def test_existing_target_is_refused_without_writes(self):
        self.project.mkdir()
        (self.project / "sentinel").write_text("keep", encoding="utf-8")
        before = self.snapshot(self.project)
        result = self.cli("create", "--project", self.project)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertEqual(before, self.snapshot(self.project))

    def test_second_create_preserves_fixture(self):
        self.create()
        before = self.snapshot(self.project)
        self.assertEqual(self.cli("create", "--project", self.project).returncode, 2)
        self.assertEqual(before, self.snapshot(self.project))

    def test_missing_parent_is_refused_without_creating_it(self):
        missing = self.parent / "missing"
        self.assertEqual(self.cli("create", "--project", missing / "new").returncode, 2)
        self.assertFalse(missing.exists())

    def test_toolkit_descendant_and_ancestor_are_refused_without_writes(self):
        target = ROOT / ("smoke-refused-" + self.parent.name)
        result = self.cli("create", "--project", target)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertFalse(target.exists())
        self.assertEqual(self.cli("create", "--project", ROOT.parent).returncode, 2)

    def test_traversal_through_missing_directory_and_alias_names_are_refused(self):
        traversal = str(self.parent / "unused" / ".." / "exercise")
        for target in (traversal, str(self.parent / "exercise."),
                       str(self.parent / "exercise ")):
            with self.subTest(target=target):
                self.assertEqual(self.cli("create", "--project", target).returncode, 2)
                self.assertFalse(self.project.exists())

    def test_ordinary_parent_traversal_to_new_sibling_is_supported(self):
        inner = self.parent / "inner"
        inner.mkdir()
        target = str(inner / ".." / "exercise")
        result = self.cli("create", "--project", target)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        result = self.cli("verify", "--project", target, "--json")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)

    def test_altered_protected_files_are_refused_before_candidate_executes(self):
        self.create()
        marker = self.parent / "executed"
        (self.project / "report.py").write_text(
            "from pathlib import Path\nPath(" + repr(str(marker)) + ").touch()\n" + GOOD_REPORT,
            encoding="utf-8",
        )
        for name in ("TASK.md", "test_report.py"):
            with self.subTest(name=name):
                path = self.project / name
                baseline = path.read_bytes()
                path.write_bytes(baseline + b"\n# changed\n")
                observation = self.verify(2)
                self.assertEqual(observation["state"], "invalid")
                self.assertFalse(observation["protected"]["matched"])
                self.assertIsNone(observation["child"]["exit_code"])
                self.assertFalse(marker.exists())
                path.write_bytes(baseline)

    def test_missing_protected_file_is_invalid(self):
        self.create()
        (self.project / "TASK.md").unlink()
        self.assertEqual(self.verify(2)["state"], "invalid")

    def test_missing_or_directory_candidate_is_invalid(self):
        self.create()
        candidate = self.project / "report.py"
        candidate.unlink()
        self.assertEqual(self.verify(2)["state"], "invalid")
        candidate.mkdir()
        self.assertEqual(self.verify(2)["state"], "invalid")

    def test_exception_wrong_type_empty_constant_and_missing_function_cannot_pass(self):
        self.create()
        for source, expected_exit in (
            ('raise RuntimeError("import failed")\n', 2),
            ('def render_csv(rows, columns): raise RuntimeError("call failed")\n', 1),
            ('def render_csv(rows, columns): return None\n', 1),
            ('def render_csv(rows, columns): return ""\n', 1),
            ('def render_csv(rows, columns): return "pass"\n', 1),
            ('# no export function\n', 2),
        ):
            with self.subTest(source=source):
                (self.project / "report.py").write_text(source, encoding="utf-8")
                self.assertNotEqual(self.verify(expected_exit)["state"], "passed")

    def test_crash_exit_is_retained_and_no_result_is_invalid(self):
        self.create()
        for code in (0, 9):
            with self.subTest(code=code):
                (self.project / "report.py").write_text(
                    f"import os\nos._exit({code})\n", encoding="utf-8")
                observed = self.verify(2)
                self.assertEqual(observed["state"], "invalid")
                self.assertEqual(observed["child"]["exit_code"], code)
                self.assertEqual(observed["checks"]["executed"], 0)

    def test_malformed_child_result_is_invalid(self):
        self.create()
        # This is a protocol failure control, not an adversarial sandbox guarantee.
        for payload in ("not-json", "{}", '{"cases": []}', '{"schema": 1, "state": "passed"}'):
            with self.subTest(payload=payload):
                (self.project / "report.py").write_text(
                    "import os, sys\nfrom pathlib import Path\n"
                    f"Path(sys.argv[-1]).write_text({payload!r}, encoding='utf-8')\n"
                    "os._exit(0)\n", encoding="utf-8")
                self.assertEqual(self.verify(2)["state"], "invalid")

    def test_incomplete_or_wrong_schema_packets_cannot_reuse_good_values(self):
        self.create()
        self.correct_report()
        good = self.verify(0)
        records = [{key: case[key] for key in ("name", "actual", "error")}
                   for case in good["cases"]]
        good_packet = {"schema": 1, "cases": records, "import_error": None}
        packets = (
            json.dumps({"schema": 1, "cases": records}),
            json.dumps({**good_packet, "schema": True}),
            json.dumps({**good_packet, "unexpected": True}),
            '{"schema": 0, ' + json.dumps(good_packet)[1:],
            '{"import_error": NaN, ' + json.dumps(good_packet)[1:],
        )
        for index, packet in enumerate(packets):
            with self.subTest(packet=index):
                (self.project / "report.py").write_text(
                    "import os, sys\nfrom pathlib import Path\n"
                    f"Path(sys.argv[-1]).write_text({packet!r}, encoding='utf-8')\n"
                    "os._exit(0)\n", encoding="utf-8")
                self.assertEqual(self.verify(2)["state"], "invalid")

    def test_partial_creation_failure_reports_retained_project(self):
        spec = importlib.util.spec_from_file_location("native_smoke_test", TOOL)
        tool = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(tool)
        original_open = Path.open

        def fail_task_open(path, *arguments, **keywords):
            if path.name == "TASK.md":
                raise OSError("synthetic write failure")
            return original_open(path, *arguments, **keywords)

        with patch.object(Path, "open", fail_task_open):
            with self.assertRaises((OSError, ValueError)) as raised:
                tool.create_project(self.project)
        self.assertRegex(str(raised.exception), "partial.*retained")
        self.assertIn(str(self.project), str(raised.exception))
        self.assertEqual(set(self.snapshot(self.project)), {"report.py"})

    def test_timeout_is_bounded_and_nonpassing(self):
        self.create()
        (self.project / "report.py").write_text(
            "import time\ntime.sleep(10)\n", encoding="utf-8")
        observed = self.verify(3, "--timeout", "0.2")
        self.assertEqual(observed["state"], "timed_out")
        self.assertIsNone(observed["child"]["exit_code"])

    def test_nonfinite_nonpositive_or_excessive_deadlines_are_refused(self):
        self.create()
        for value in ("0", "-1", "nan", "inf", "61"):
            with self.subTest(value=value):
                self.assertEqual(self.cli("verify", "--project", self.project,
                                          "--timeout", value).returncode, 2)

    def test_candidate_mutation_during_acceptance_is_invalid(self):
        self.create()
        self.correct_report("from pathlib import Path\n"
                            "with Path(__file__).open('a', encoding='utf-8') as changed:\n"
                            "    changed.write('\\n# mutation\\n')\n")
        observed = self.verify(2)
        self.assertEqual(observed["state"], "invalid")
        self.assertTrue(observed["inputs_changed"])
        self.assertEqual(observed["child"]["exit_code"], 0)

    def test_fixture_identity_distinguishes_locations_and_is_stable(self):
        self.create()
        first = self.verify(1)["fixture_identity"]
        self.assertEqual(first, self.verify(1)["fixture_identity"])
        self.project = self.parent / "second"
        self.create()
        self.assertNotEqual(first, self.verify(1)["fixture_identity"])

    def make_directory_link(self, link, target):
        if os.name == "nt":
            result = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)],
                                    capture_output=True, text=True, timeout=10)
            if result.returncode:
                self.skipTest("Windows junction creation unavailable: " + result.stderr)
            self.addCleanup(lambda: os.rmdir(link) if link.exists() else None)
        else:
            link.symlink_to(target, target_is_directory=True)
            self.addCleanup(lambda: link.unlink(missing_ok=True))

    def test_link_or_junction_parent_refuses_creation_and_verification(self):
        self.create()
        self.correct_report()
        link = self.parent / "alias"
        self.make_directory_link(link, self.parent)
        before = self.snapshot(self.project)
        created = self.cli("create", "--project", link / "new")
        self.assertEqual(created.returncode, 2, created.stdout + created.stderr)
        self.assertFalse((self.parent / "new").exists())
        hidden = self.cli("create", "--project", link / ".." / "hidden-new")
        self.assertEqual(hidden.returncode, 2, hidden.stdout + hidden.stderr)
        self.assertFalse((self.parent.parent / "hidden-new").exists())
        observed = self.cli("verify", "--project", link / "exercise", "--json")
        self.assertEqual(observed.returncode, 2, observed.stdout + observed.stderr)
        self.assertEqual(before, self.snapshot(self.project))

    def test_symlink_candidate_escape_is_refused_without_execution(self):
        self.create()
        candidate = self.project / "report.py"
        candidate.unlink()
        outside = self.parent / "outside.py"
        outside.write_text(GOOD_REPORT, encoding="utf-8")
        try:
            candidate.symlink_to(outside)
        except OSError as error:
            self.skipTest("File symlink creation unavailable: " + str(error))
        before = outside.read_bytes()
        self.assertEqual(self.verify(2)["state"], "invalid")
        self.assertEqual(before, outside.read_bytes())

    def test_report_directory_junction_is_refused(self):
        self.create()
        candidate = self.project / "report.py"
        candidate.unlink()
        outside = self.parent / "outside"
        outside.mkdir()
        self.make_directory_link(candidate, outside)
        self.assertEqual(self.verify(2)["state"], "invalid")


if __name__ == "__main__":
    unittest.main()
