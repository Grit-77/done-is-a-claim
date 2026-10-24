"""Actual files and CLI artifacts for the agreed fixed-contract fixture."""

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


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "examples" / "fixed_delivery.py"
SPECS = ROOT / "examples" / "fixed-delivery"


class FixedDeliveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("fixed_delivery_fixture", SCRIPT)
        cls.module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = cls.module
        spec.loader.exec_module(cls.module)

    def cli(self, output):
        return subprocess.run(
            [sys.executable, "-B", str(SCRIPT), "--output", str(output)],
            cwd=ROOT, stdin=subprocess.DEVNULL, capture_output=True,
            text=True, encoding="utf-8", timeout=20,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )

    def assert_no_output_path(self, value, output):
        if isinstance(value, str):
            self.assertNotIn(str(output), value)
            self.assertNotIn(output.as_posix(), value)
        elif isinstance(value, dict):
            for key, item in value.items():
                self.assert_no_output_path(key, output)
                self.assert_no_output_path(item, output)
        elif isinstance(value, list):
            for item in value:
                self.assert_no_output_path(item, output)

    def test_cli_persists_frozen_specs_and_actual_observations(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "new-run"
            result = self.cli(output)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stderr, "")
            report = json.loads(result.stdout)
            self.assertEqual(report, json.loads((output / "observations.json").read_text(encoding="utf-8")))
            for name in ("task-spec.json", "format-control-spec.json"):
                self.assertEqual((output / name).read_bytes(), (SPECS / name).read_bytes())
            self.assertTrue(report["synthetic"])
            self.assertTrue(report["specs_unchanged"])
            self.assertTrue(report["suite_exercised_as_expected"])
            self.assert_no_output_path(report, output)
            self.assertIn("not", report["runner_exit_meaning"].lower())
            self.assertIn("accept", report["runner_exit_meaning"].lower())
            main = report["main"]
            spec_data = json.loads((output / "task-spec.json").read_text(encoding="utf-8"))
            self.assertEqual(main["task_spec_sha256"], hashlib.sha256((output / "task-spec.json").read_bytes()).hexdigest())
            expected = [(True, True, True), (False, True, False), (False, False, False)]
            for attempt, outcome in zip(main["attempts"], expected):
                self.assertTrue(attempt["copy_completed"])
                self.assertTrue(attempt["destination_exists"])
                self.assertEqual(attempt["approved_sha256"], spec_data["approved_sha256"])
                self.assertEqual(attempt["destination"], spec_data["destination"])
                self.assertEqual(attempt["task_spec_sha256"], main["task_spec_sha256"])
                self.assertEqual((attempt["sha256_matches_approved"], attempt["json_parse_ok"], attempt["accepted"]), outcome)
            self.assertEqual(len(main["attempts"]), 3)
            current = (output / spec_data["destination"]).read_bytes()
            self.assertEqual(main["attempts"][-1]["destination_sha256"], hashlib.sha256(current).hexdigest())
            with self.assertRaises(ValueError):
                json.loads(current)
            control = report["format_control"]
            self.assertNotEqual(control["task_id"], main["task_id"])
            self.assertNotEqual(control["approved_sha256"], main["approved_sha256"])
            self.assertEqual(control["approved_sha256"], hashlib.sha256((output / "inputs/invalid/artifact.json").read_bytes()).hexdigest())
            self.assertNotEqual(control["destination"], main["destination"])
            observed = control["observation"]
            self.assertTrue(observed["sha256_matches_approved"])
            self.assertFalse(observed["json_parse_ok"])
            self.assertFalse(observed["accepted"])

    def test_main_contract_is_identical_before_every_copy(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "run"
            original_copy = shutil.copyfile
            snapshots = []

            def inspected_copy(source, destination):
                snapshots.append(((output / "task-spec.json").read_bytes(), Path(destination)))
                return original_copy(source, destination)

            with patch.object(self.module.shutil, "copyfile", side_effect=inspected_copy):
                report = self.module.run_fixture(output)
            self.assertTrue(report["suite_exercised_as_expected"])
            self.assertEqual(len(snapshots), 4)
            self.assertEqual({data for data, _ in snapshots}, {(SPECS / "task-spec.json").read_bytes()})
            self.assertEqual(len({destination for _, destination in snapshots[:3]}), 1)
            self.assertNotEqual(snapshots[0][1], snapshots[-1][1])

    def test_observer_uses_frozen_approval_not_mutable_source(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            contract = self.module.freeze_contract(SPECS / "task-spec.json")
            source = root / contract.approved_artifact
            destination = root / contract.destination
            source.parent.mkdir(parents=True)
            destination.parent.mkdir(parents=True)
            source.write_bytes(b'{"version":2,"reviewed":true}\n')
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), contract.approved_sha256)
            source.write_bytes(b'{"version":1,"reviewed":false}\n')
            shutil.copyfile(source, destination)
            observed = self.module.observe_destination(contract, root, copy_completed=True)
            self.assertTrue(observed["json_parse_ok"])
            self.assertFalse(observed["sha256_matches_approved"])
            self.assertFalse(observed["accepted"])

    def test_observer_reads_changed_and_missing_destination(self):
        contract = self.module.freeze_contract(SPECS / "task-spec.json")
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            destination = root / contract.destination
            absent = self.module.observe_destination(contract, root)
            self.assertFalse(absent["accepted"])
            self.assertFalse(absent["destination_exists"])
            self.assertEqual(absent["readback_error"], "FileNotFoundError")
            destination.parent.mkdir()
            destination.write_bytes(b'{"version":2,"reviewed":true}\n')
            self.assertTrue(self.module.observe_destination(contract, root)["accepted"])
            changed = b'{"unexpected":"different valid JSON"}\n'
            destination.write_bytes(changed)
            observed = self.module.observe_destination(contract, root)
            self.assertEqual(observed["destination_sha256"], hashlib.sha256(changed).hexdigest())
            self.assertTrue(observed["json_parse_ok"])
            self.assertFalse(observed["accepted"])

    def test_freeze_keeps_original_spec_when_file_changes(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "task-spec.json"
            initial = (SPECS / "task-spec.json").read_bytes()
            path.write_bytes(initial)
            contract = self.module.freeze_contract(path)
            path.write_bytes((SPECS / "format-control-spec.json").read_bytes())
            self.assertEqual(contract.spec_bytes, initial)
            self.assertEqual(contract.spec_sha256, hashlib.sha256(initial).hexdigest())
            with self.assertRaises((AttributeError, TypeError)):
                contract.approved_sha256 = "changed"

    def test_repeated_fresh_runs_have_same_contract_and_contrasts(self):
        with tempfile.TemporaryDirectory() as folder:
            reports = [self.module.run_fixture(Path(folder) / str(i)) for i in range(2)]
            self.assertEqual(reports[0], reports[1])

    def test_existing_output_is_refused_without_modification(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            sentinel = root / "keep.txt"
            sentinel.write_bytes(b"caller-owned")
            result = self.cli(root)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(sentinel.read_bytes(), b"caller-owned")
            self.assertEqual(set(root.iterdir()), {sentinel})
            self.assertEqual(result.stdout, "")
            error = json.loads(result.stderr)
            self.assertEqual(error, {"error": "FileExistsError"})
            self.assert_no_output_path(error, root)

    def test_path_privacy_assertion_detects_decoded_json_leaks(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for representation in (str(root), root.as_posix()):
                leaked = json.loads(json.dumps({"nested": [{"destination": representation}]}))
                with self.assertRaises(AssertionError):
                    self.assert_no_output_path(leaked, root)

    def test_traversing_contract_destination_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            data = json.loads((SPECS / "task-spec.json").read_text(encoding="utf-8"))
            data["destination"] = "../outside.json"
            path = Path(folder) / "bad-spec.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(ValueError):
                self.module.freeze_contract(path)


if __name__ == "__main__":
    unittest.main()
