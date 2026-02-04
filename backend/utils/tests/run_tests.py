#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test runner script for backend/utils tests

Usage:
    python run_tests.py                  # Run all tests
    python run_tests.py --unit           # Run only unit tests
    python run_tests.py --integration     # Run only integration tests
    python run_tests.py --coverage       # Run with coverage report
    python run_tests.py --file test_context_compressor.py  # Run specific file
"""

import sys
import os
import argparse
import subprocess

# Change to the script's directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

def run_tests(args):
    """Run tests based on command line arguments"""

    # Build pytest command
    pytest_args = ["pytest", "-v"]

    # Add coverage if requested
    if args.coverage:
        pytest_args.extend([
            "--cov=..",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov",
            "--cov-fail-under=60"
        ])

    # Add test markers
    if args.unit:
        pytest_args.extend(["-m", "not integration"])
    elif args.integration:
        pytest_args.extend(["-m", "integration"])

    # Add specific file
    if args.file:
        pytest_args.append(args.file)

    # Add extra arguments
    if args.verbose:
        pytest_args.append("-vv")
    if args.silent:
        pytest_args.append("--tb=no")

    # Print command
    print(f"Running: {' '.join(pytest_args)}")
    print("-" * 80)

    # Run pytest
    result = subprocess.call(pytest_args)

    # Print coverage summary if generated
    if args.coverage and os.path.exists("htmlcov/index.html"):
        print("-" * 80)
        print("Coverage report generated: htmlcov/index.html")

    return result

def main():
    parser = argparse.ArgumentParser(
        description="Run tests for backend/utils package",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py                    Run all tests
  python run_tests.py --unit             Run only unit tests
  python run_tests.py --integration       Run only integration tests
  python run_tests.py --coverage         Run with coverage report
  python run_tests.py --file test_context_compressor.py
        """
    )

    parser.add_argument(
        "--unit",
        action="store_true",
        help="Run only unit tests (skip integration tests)"
    )

    parser.add_argument(
        "--integration",
        action="store_true",
        help="Run only integration tests"
    )

    parser.add_argument(
        "--coverage",
        "-c",
        action="store_true",
        help="Generate coverage report"
    )

    parser.add_argument(
        "--file",
        "-f",
        type=str,
        help="Run specific test file"
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="More verbose output"
    )

    parser.add_argument(
        "--silent",
        "-s",
        action="store_true",
        help="Suppress tracebacks"
    )

    args = parser.parse_args()

    # Ensure we're not running unit and integration together
    if args.unit and args.integration:
        print("Error: Cannot specify both --unit and --integration")
        return 1

    # Run tests
    return run_tests(args)

if __name__ == "__main__":
    sys.exit(main())
