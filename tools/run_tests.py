#!/usr/bin/env python3
"""Run the unittest suite, rejecting empty discovery or entirely skipped suites."""

import argparse
from pathlib import Path
import unittest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-directory", type=Path, default=Path(__file__).resolve().parents[1] / "tests", help="test discovery directory (defaults to this repository's tests)")
    args = parser.parse_args()
    try:
        suite = unittest.TestLoader().discover(str(args.start_directory.resolve()))
    except (ImportError, OSError) as error:
        print(f"Test discovery failed: {error}")
        return 1
    if suite.countTestCases() == 0:
        print("Test verification failed: no tests discovered.")
        return 1
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.testsRun == len(result.skipped):
        print("Test verification failed: no tests executed; all discovered tests were skipped.")
        return 1
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
