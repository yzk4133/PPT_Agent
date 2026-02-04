#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Setup script for test environment

This script helps set up the test environment by:
1. Checking Python version
2. Installing test dependencies
3. Creating necessary directories
4. Verifying installation
"""

import sys
import os
import subprocess

def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 80)
    print(f" {text}")
    print("=" * 80)

def check_python_version():
    """Check Python version"""
    print_header("Checking Python Version")

    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")

    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Error: Python 3.8+ is required")
        return False

    print("✅ Python version is compatible")
    return True

def install_dependencies():
    """Install test dependencies"""
    print_header("Installing Test Dependencies")

    requirements_file = os.path.join(os.path.dirname(__file__), "requirements.txt")

    if not os.path.exists(requirements_file):
        print(f"❌ Error: requirements.txt not found at {requirements_file}")
        return False

    try:
        print(f"Installing from {requirements_file}...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install",
            "-r", requirements_file
        ])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return False

def verify_installation():
    """Verify that test dependencies are installed"""
    print_header("Verifying Installation")

    required_packages = [
        "pytest",
        "pytest_cov",
        "pytest_mock",
        "requests_mock",
    ]

    all_installed = True
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"✅ {package} is installed")
        except ImportError:
            print(f"❌ {package} is NOT installed")
            all_installed = False

    return all_installed

def verify_source_files():
    """Verify that source files exist"""
    print_header("Verifying Source Files")

    # Check parent directory structure
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    required_files = [
        "context_compressor.py",
        os.path.join("save_ppt", "ppt_generator.py"),
        os.path.join("save_ppt", "main_api.py"),
    ]

    all_exist = True
    for file_path in required_files:
        full_path = os.path.join(parent_dir, file_path)
        if os.path.exists(full_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} NOT found")
            all_exist = False

    return all_exist

def run_quick_test():
    """Run a quick test to verify setup"""
    print_header("Running Quick Test")

    try:
        result = subprocess.call([
            sys.executable, "-m", "pytest",
            "--collect-only",
            "-q"
        ])

        if result == 0:
            print("✅ Test collection successful")
            print(f"   Tests are ready to run!")
            return True
        else:
            print("❌ Test collection failed")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def print_usage_examples():
    """Print usage examples"""
    print_header("Usage Examples")

    print("\nRun all tests:")
    print("  pytest")
    print("  python run_tests.py")

    print("\nRun specific test file:")
    print("  pytest test_context_compressor.py")

    print("\nRun with coverage:")
    print("  pytest --cov=.. --cov-report=html")

    print("\nRun only unit tests:")
    print("  pytest -m 'not integration'")

    print("\nRun with verbose output:")
    print("  pytest -v")

    print("\nFor more options:")
    print("  pytest --help")

def main():
    """Main setup function"""
    print("\n" + "=" * 80)
    print(" Backend/Utils Test Environment Setup")
    print("=" * 80)

    # Step 1: Check Python version
    if not check_python_version():
        return 1

    # Step 2: Verify source files
    if not verify_source_files():
        print("\n⚠️  Warning: Some source files are missing")
        print("   Make sure you're in the correct directory")

    # Step 3: Install dependencies
    print("\n⚠️  About to install test dependencies...")
    response = input("Continue? (y/n): ").strip().lower()

    if response == 'y':
        if not install_dependencies():
            print("\n❌ Failed to install dependencies")
            return 1
    else:
        print("Skipped dependency installation")

    # Step 4: Verify installation
    if not verify_installation():
        print("\n❌ Some dependencies are missing")
        print("   Please run: pip install -r requirements.txt")
        return 1

    # Step 5: Run quick test
    if not run_quick_test():
        print("\n❌ Quick test failed")
        return 1

    # Step 6: Print usage
    print_usage_examples()

    print("\n" + "=" * 80)
    print("✅ Setup complete! You can now run the tests.")
    print("=" * 80 + "\n")

    return 0

if __name__ == "__main__":
    sys.exit(main())
