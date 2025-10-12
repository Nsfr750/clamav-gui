#!/usr/bin/env python3
"""
Test runner script for ClamAV GUI.

This script provides an easy way to run tests with coverage reporting.
"""

import subprocess
import sys
import os
import argparse

def run_tests(test_type='all', coverage=True, verbose=False):
    """Run the test suite with various options."""

    # Change to the project root directory
    project_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_root)

    # Base pytest command
    cmd = [sys.executable, '-m', 'pytest']

    # Add test type filtering
    if test_type != 'all':
        if test_type == 'unit':
            cmd.append('-m unit')
        elif test_type == 'integration':
            cmd.append('-m integration')
        elif test_type == 'gui':
            cmd.append('-m gui')
        elif test_type == 'performance':
            cmd.append('-m "performance or benchmark"')
        elif test_type == 'isolation':
            cmd.append('-m "isolation or clamav_mock"')

    # Add coverage options if requested
    if coverage:
        cmd.extend([
            '--cov=clamav_gui',
            '--cov-report=term-missing',
            '--cov-report=html:htmlcov',
            '--cov-report=xml:coverage.xml',
            '--cov-branch'
        ])

    # Add verbose flag
    if verbose:
        cmd.append('-v')
    else:
        cmd.append('--tb=short')

    # Specify test directory
    cmd.append('tests/')

    print(f"Running ClamAV GUI {test_type} tests...")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 50)

    try:
        result = subprocess.run(cmd, check=True)
        print("-" * 50)
        print("✅ Tests completed successfully!")

        if coverage:
            print("\n📊 Coverage Reports Generated:")
            print("  - Terminal: Coverage shown above")
            print("  - HTML: htmlcov/index.html")
            print("  - XML: coverage.xml (for CI/CD)")

        return True

    except subprocess.CalledProcessError as e:
        print("-" * 50)
        print(f"❌ Tests failed with exit code: {e.returncode}")
        return False
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        return False

def run_specific_test(test_file=None, test_function=None):
    """Run a specific test file or function."""

    if not test_file:
        print("Usage: python run_tests.py --specific test_file.py [test_function]")
        return False

    cmd = [sys.executable, '-m', 'pytest', '-v']

    if test_function:
        cmd.append(f"{test_file}::{test_function}")
    else:
        cmd.append(test_file)

    print(f"Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Test failed with exit code: {e.returncode}")
        return False

def show_help():
    """Show help information."""
    print("ClamAV GUI Test Runner")
    print("=" * 30)
    print()
    print("Usage:")
    print("  python run_tests.py [options]")
    print()
    print("Options:")
    print("  --type TYPE       Test type to run (default: all)")
    print("                    Options: all, unit, integration, gui, performance, isolation")
    print("  --no-coverage     Skip coverage reporting")
    print("  --verbose         Enable verbose output")
    print("  --specific FILE   Run specific test file")
    print("  --function FUNC   Run specific test function (requires --specific)")
    print("  --help            Show this help message")
    print()
    print("Examples:")
    print("  python run_tests.py --type unit")
    print("  python run_tests.py --type performance --verbose")
    print("  python run_tests.py --specific tests/test_lang_manager.py")
    print("  python run_tests.py --specific tests/test_gui_integration.py --function TestMainWindowIntegration::test_main_window_creation")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ClamAV GUI Test Runner")
    parser.add_argument('--type', choices=['all', 'unit', 'integration', 'gui', 'performance', 'isolation'],
                       default='all', help='Test type to run')
    parser.add_argument('--no-coverage', action='store_true', help='Skip coverage reporting')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')
    parser.add_argument('--specific', help='Run specific test file')
    parser.add_argument('--function', help='Run specific test function (requires --specific)')

    args = parser.parse_args()

    if args.specific:
        success = run_specific_test(args.specific, args.function)
    else:
        success = run_tests(args.type, not args.no_coverage, args.verbose)

    sys.exit(0 if success else 1)
