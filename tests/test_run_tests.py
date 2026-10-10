"""The test command must report failure when verification does not execute."""

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


RUNNER = Path(__file__).resolve().parents[1] / "tools" / "run_tests.py"


class TestRunnerTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.tests = Path(temporary.name)

    def run_fixture(self, content=None):
        if content is not None:
            (self.tests / "test_fixture.py").write_text(content, encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(RUNNER), "--start-directory", str(self.tests)],
            capture_output=True, text=True, check=False,
        )

    def test_empty_discovery_is_nonzero(self):
        result = self.run_fixture()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("no tests", (result.stdout + result.stderr).lower())

    def test_test_file_without_cases_is_nonzero(self):
        result = self.run_fixture("import unittest\nclass Empty(unittest.TestCase):\n    pass\n")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("no tests", (result.stdout + result.stderr).lower())

    def test_real_passing_suite_exits_zero(self):
        result = self.run_fixture("import unittest\nclass Check(unittest.TestCase):\n    def test_pass(self):\n        self.assertEqual(2 + 2, 4)\n")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Ran 1 test", result.stderr)

    def test_real_failing_suite_exits_nonzero(self):
        result = self.run_fixture("import unittest\nclass Check(unittest.TestCase):\n    def test_fail(self):\n        self.fail('fixture failure')\n")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("fixture failure", result.stderr)

    def test_entirely_skipped_suite_is_nonzero(self):
        result = self.run_fixture("import unittest\n@unittest.skip('fixture skip')\nclass Check(unittest.TestCase):\n    def test_skip(self):\n        self.fail('must not run')\n")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("no tests executed", (result.stdout + result.stderr).lower())

    def test_partially_skipped_suite_passes_and_reports_skip_count(self):
        result = self.run_fixture("import unittest\nclass Check(unittest.TestCase):\n    def test_pass(self):\n        self.assertTrue(True)\n    @unittest.skip('fixture skip')\n    def test_skip(self):\n        self.fail('must not run')\n")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("skipped=1", result.stderr)


if __name__ == "__main__":
    unittest.main()
