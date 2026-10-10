"""Real temporary artifacts and CLI checks for the synthetic delivery trap."""

import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "examples" / "wrong_delivery.py"


class WrongDeliveryTests(unittest.TestCase):
    def run_cli(self, *args, cwd=ROOT, env=None):
        return subprocess.run(
            [sys.executable, "-B", str(DEMO), *args], cwd=cwd, env=env,
            capture_output=True, text=True, timeout=10,
        )

    def report(self):
        result = self.run_cli("--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        return json.loads(result.stdout)

    def module(self):
        self.assertTrue(DEMO.is_file(), "synthetic delivery demo is missing")
        spec = importlib.util.spec_from_file_location("wrong_delivery", DEMO)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def fixture(self, folder):
        root = Path(folder)
        expected = root / "reviewed.json"
        source = root / "source.json"
        destination = root / "delivered.json"
        expected.write_bytes(b'{"version":2}\n')
        source.write_bytes(expected.read_bytes())
        return expected, source, destination

    def test_successful_stale_same_named_copy_fails_reviewed_digest(self):
        # Catches reporting a completed stale copy as the reviewed artifact.
        case = self.report()["scenarios"]["stale_same_name"]
        self.assertTrue(case["copy_completed"])
        self.assertIsNone(case["copy_error"])
        self.assertEqual(Path(case["source"]).name, Path(case["expected_reviewed"]).name)
        checks = case["checks"]
        self.assertTrue(checks["destination_exists"])
        self.assertTrue(checks["bytes_match_source"])
        self.assertTrue(checks["json_parse_ok"])
        self.assertFalse(checks["digest_matches_reviewed"])
        self.assertNotEqual(checks["destination_sha256"], checks["expected_reviewed_sha256"])

    def test_positive_control_matches_reviewed_digest_and_parses(self):
        # Catches an always-failing detector and a missing actual read-back.
        case = self.report()["scenarios"]["correct_copy"]
        self.assertTrue(case["copy_completed"])
        checks = case["checks"]
        self.assertTrue(checks["bytes_match_source"])
        self.assertTrue(checks["digest_matches_reviewed"])
        self.assertTrue(checks["json_parse_ok"])
        self.assertIsNone(checks["json_error"])

    def test_identical_invalid_json_is_equal_but_does_not_parse(self):
        # Catches using byte identity as proof of artifact validity.
        case = self.report()["scenarios"]["matching_invalid_json"]
        self.assertTrue(case["copy_completed"])
        checks = case["checks"]
        self.assertTrue(checks["bytes_match_source"])
        self.assertTrue(checks["digest_matches_reviewed"])
        self.assertFalse(checks["json_parse_ok"])
        self.assertEqual(checks["json_error"], "JSONDecodeError")

    def test_missing_destination_is_explicit_and_fails_readback(self):
        # Catches silently approving a destination that was never delivered.
        module = self.module()
        with tempfile.TemporaryDirectory() as folder:
            expected, source, destination = self.fixture(folder)
            checks = module.inspect_delivery(expected, source, destination)
        self.assertFalse(checks["destination_exists"])
        self.assertIsNone(checks["destination_sha256"])
        self.assertFalse(checks["digest_matches_reviewed"])
        self.assertFalse(checks["bytes_match_source"])
        self.assertFalse(checks["json_parse_ok"])
        self.assertEqual(checks["readback_error"], "FileNotFoundError")

    def test_modified_destination_is_detected_by_actual_bytes(self):
        # Catches trusting copy completion after the destination changes.
        module = self.module()
        with tempfile.TemporaryDirectory() as folder:
            expected, source, destination = self.fixture(folder)
            shutil.copyfile(source, destination)
            good = module.inspect_delivery(expected, source, destination)
            self.assertTrue(good["digest_matches_reviewed"])
            altered = b'{"version":3}\n'
            destination.write_bytes(altered)
            bad = module.inspect_delivery(expected, source, destination)
            self.assertEqual(bad["destination_sha256"], hashlib.sha256(altered).hexdigest())
        self.assertFalse(bad["digest_matches_reviewed"])
        self.assertFalse(bad["bytes_match_source"])
        self.assertTrue(bad["json_parse_ok"])

    def test_missing_readback_cannot_satisfy_expected_contrasts(self):
        # Catches the demo declaring its contrasts observed unconditionally.
        module = self.module()
        report = module.run_demo()
        self.assertTrue(module.contrasts_observed(report["scenarios"]))
        with tempfile.TemporaryDirectory() as folder:
            expected, source, destination = self.fixture(folder)
            report["scenarios"]["correct_copy"]["checks"] = module.inspect_delivery(
                expected, source, destination,
            )
        self.assertFalse(module.contrasts_observed(report["scenarios"]))

    def test_json_reports_demo_success_as_expected_contrasts(self):
        # Catches confusing a successful demonstration with successful delivery.
        data = self.report()
        self.assertTrue(data["synthetic"])
        self.assertEqual(data["demo_exit_code"], 0)
        self.assertTrue(data["expected_contrasts_observed"])
        meaning = data["demo_exit_meaning"].lower()
        self.assertIn("contrast", meaning)
        self.assertIn("demonstrat", meaning)
        self.assertIn("not", meaning)
        self.assertIn("delivery success", meaning)
        self.assertNotIn(str(ROOT), json.dumps(data))
        for case in data["scenarios"].values():
            for key in ("expected_reviewed", "source", "destination"):
                self.assertFalse(Path(case[key]).is_absolute())
            self.assertNotIn("exit_code", case)

    def test_plain_cli_discloses_copy_checks_and_demo_exit_meaning(self):
        # Catches plain output hiding the operational/verification distinction.
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        text = result.stdout.lower()
        self.assertIn("synthetic", text)
        self.assertIn("copy_completed=true", text)
        self.assertIn("digest_matches_reviewed=false", text)
        self.assertIn("json_parse_ok=false", text)
        self.assertIn("demo exit: 0", text)
        self.assertIn("not delivery success", text)

    def test_cli_cleans_temp_fixtures_and_preserves_working_directory(self):
        # Catches fixture leakage or writing delivered files beside the caller.
        import os

        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            sentinel = root / "artifact.json"
            sentinel.write_bytes(b"caller-owned artifact")
            env = dict(os.environ, TEMP=folder, TMP=folder, TMPDIR=folder)
            for args in ((), ("--json",)):
                result = self.run_cli(*args, cwd=root, env=env)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(sentinel.read_bytes(), b"caller-owned artifact")
                self.assertEqual(set(root.iterdir()), {sentinel})


if __name__ == "__main__":
    unittest.main()
