#!/usr/bin/env python3
"""
Test script for Gemini CLI functionality.
"""

import subprocess
import sys


def run_command(cmd, description="", expect_success=True):
    """Run a CLI command and check the result."""
    print(f"\n🧪 Testing: {description}")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 60)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        if result.stdout:
            print("STDOUT:")
            print(result.stdout)

        if result.stderr:
            print("STDERR:")
            print(result.stderr)

        success = result.returncode == 0

        if expect_success and not success:
            print(f"❌ Command failed with exit code {result.returncode}")
            return False
        elif not expect_success and success:
            print("❌ Command succeeded when failure was expected")
            return False
        else:
            print(f"✅ Command {'succeeded' if success else 'failed as expected'}")
            return True

    except subprocess.TimeoutExpired:
        print("❌ Command timed out")
        return False
    except Exception as e:
        print(f"❌ Error running command: {e}")
        return False


def main():
    """Run CLI tests."""
    print("🚀 Testing Gemini MCP Server CLI")
    print("=" * 60)

    # Test basic CLI functionality (should work without Gemini CLI)
    tests = [
        # Basic help and info commands
        (["uv", "run", "gemini-cli", "--help"], "Basic help command"),
        (["uv", "run", "gemini-cli", "version"], "Version command"),
        (["uv", "run", "gemini-cli", "examples"], "Examples command"),
        # Status commands (configuration only, no Gemini calls)
        (["uv", "run", "gemini-cli", "status", "config"], "Status config command"),
        (
            ["uv", "run", "gemini-cli", "status", "templates"],
            "Status templates command",
        ),
        # Help for each command group
        (["uv", "run", "gemini-cli", "review", "--help"], "Review help"),
        (["uv", "run", "gemini-cli", "feature", "--help"], "Feature help"),
        (["uv", "run", "gemini-cli", "bug", "--help"], "Bug help"),
        (["uv", "run", "gemini-cli", "explain", "--help"], "Explain help"),
        (["uv", "run", "gemini-cli", "status", "--help"], "Status help"),
        # JSON output tests
        (
            ["uv", "run", "gemini-cli", "--json", "status", "config"],
            "JSON config output",
        ),
        (
            ["uv", "run", "gemini-cli", "--json", "status", "templates"],
            "JSON templates output",
        ),
        # Global options tests
        (
            ["uv", "run", "gemini-cli", "--verbose", "status", "config"],
            "Verbose config",
        ),
        (
            ["uv", "run", "gemini-cli", "--no-color", "status", "config"],
            "No color config",
        ),
    ]

    passed = 0
    failed = 0

    for cmd, description in tests:
        if run_command(cmd, description):
            passed += 1
        else:
            failed += 1

    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("🎉 All CLI tests passed!")
        print("\nThe CLI is ready for use. To test with actual Gemini:")
        print("1. Install and authenticate Gemini CLI")
        print("2. Run: gemini-cli status check")
        print("3. Test code review: gemini-cli review file --file test_code.py")
    else:
        print("❌ Some tests failed. Please check the implementation.")
        sys.exit(1)


if __name__ == "__main__":
    main()
