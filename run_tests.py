#!/usr/bin/env python3
"""
Simple test runner for the Gemini MCP Server.
"""

import subprocess
import sys
from pathlib import Path


def main():
    """Run tests with proper configuration."""
    # Ensure we're in the right directory
    project_root = Path(__file__).parent

    # Run pytest with our configuration
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        str(project_root / "src"),
        "-v",
        "--tb=short",
        "--color=yes",
    ]

    # Add coverage if requested
    if "--coverage" in sys.argv:
        cmd.extend(["--cov=src", "--cov-report=term-missing", "--cov-report=html"])

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=project_root)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
