"""CLI checks using real child processes, including replay of reported argv."""

import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "examples" / "false_green.py"


class FalseGreenTests(unittest.TestCase):
    def run_demo(self, *args):
        return subprocess.run(
            [sys.executable, str(DEMO), *args],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=10,
        )

    def json_demo(self):
        result = self.run_demo("--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        return json.loads(result.stdout)

    def test_json_reports_verifier_failure_and_summarizer_success(self):
        # Catches treating the final process's status as the verifier's status.
        data = self.json_demo()
        self.assertTrue(data["synthetic"])
        self.assertIn("not incident raw log", data["label"])
        self.assertEqual(data["case"], "synthetic_false_green")
        self.assertEqual(data["verifier"]["exit_code"], 1)
        self.assertEqual(data["summarizer"]["exit_code"], 0)
        self.assertEqual(data["verdict"]["state"], "FAIL")
        self.assertEqual(data["verdict"]["command"], data["verifier"]["command"])
        self.assertEqual(data["verdict"]["exit_code"], 1)
        self.assertIn("summarizer", data["verdict"]["reason"])

    def test_reported_argv_reproduces_exact_output_and_exit_status(self):
        # Catches invented outputs/statuses or failing to forward verifier output.
        data = self.json_demo()
        verifier = data["verifier"]
        summarizer = data["summarizer"]
        self.assertEqual(verifier["command"][0], sys.executable)
        self.assertEqual(summarizer["command"][0], sys.executable)
        actual_verifier = subprocess.run(
            verifier["command"], stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True, timeout=10,
        )
        self.assertEqual(actual_verifier.returncode, verifier["exit_code"])
        self.assertEqual(actual_verifier.stdout, verifier["output"])
        self.assertIn("FAIL", actual_verifier.stdout)
        self.assertIn("expected 2, got 3", actual_verifier.stdout)
        actual_summary = subprocess.run(
            summarizer["command"], input=actual_verifier.stdout,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, timeout=10,
        )
        self.assertEqual(actual_summary.returncode, summarizer["exit_code"])
        self.assertEqual(actual_summary.stdout, summarizer["output"])
        self.assertIn(actual_verifier.stdout.strip(), actual_summary.stdout)

    def test_json_explains_successful_demo_is_not_fixture_success(self):
        # Catches the example making the same false-green claim it illustrates.
        data = self.json_demo()
        self.assertEqual(data["demo_exit_code"], 0)
        self.assertIn("expected mismatch demonstrated", data["demo_exit_meaning"])
        self.assertIn("not fixture success", data["demo_exit_meaning"])

    def test_text_and_help_disclose_demo_and_command_status_meaning(self):
        # Catches hiding the receipt or allowing exit 0 to imply fixture success.
        result = self.run_demo()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        for text in (
            "Synthetic demo, not incident raw log", "Verifier exit: 1",
            "Summarizer exit: 0", "Receipt state: FAIL", "Command exit: 1",
            "Reason:", "Demo exit: 0", "expected mismatch demonstrated",
            "not fixture success",
        ):
            self.assertIn(text, result.stdout)
        help_result = self.run_demo("--help")
        self.assertEqual(help_result.returncode, 0, help_result.stderr)
        help_text = " ".join(help_result.stdout.split())
        for text in ("synthetic", "--json", "expected mismatch", "fixture success"):
            self.assertIn(text, help_text)


if __name__ == "__main__":
    unittest.main()
