"""Test runner script for the backend."""

import subprocess
import sys
import os

def run_tests():
    """Run all tests with coverage."""
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # Run unit tests
    print("=" * 50)
    print("Running Unit Tests...")
    print("=" * 50)
    result = subprocess.run([
        sys.executable, "-m", "pytest",
        "tests/unit/",
        "-v",
        "--tb=short",
        "-m", "unit or not integration",
    ])

    if result.returncode != 0:
        print("\n❌ Unit tests failed!")
        return False

    print("\n✅ Unit tests passed!")

    # Run integration tests
    print("\n" + "=" * 50)
    print("Running Integration Tests...")
    print("=" * 50)
    result = subprocess.run([
        sys.executable, "-m", "pytest",
        "tests/integration/",
        "-v",
        "--tb=short",
    ])

    if result.returncode != 0:
        print("\n❌ Integration tests failed!")
        return False

    print("\n✅ Integration tests passed!")
    return True


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
