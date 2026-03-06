"""Module gate test: run ALL store tests to verify the store module is solid."""
import subprocess
import sys
import os


def test_store_module_gate():
    """All store component tests must pass."""
    cwd = os.path.join(os.path.dirname(__file__), "..", "..", "pipeline")
    result = subprocess.run(
        [sys.executable, "-m", "pytest",
         os.path.join("..", ".test", "pipeline", "store"),
         "-v", "--tb=short"],
        capture_output=True, text=True, cwd=cwd
    )
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)
    assert result.returncode == 0, f"Store module tests failed:\n{result.stdout}\n{result.stderr}"
