"""Module gate test: run ALL processor tests to verify the processor module is solid."""
import subprocess
import sys
import os


def test_processor_module_gate():
    """All processor component tests must pass (excluding embedder which requires GPU model load)."""
    cwd = os.path.join(os.path.dirname(__file__), "..", "..", "pipeline")
    result = subprocess.run(
        [sys.executable, "-m", "pytest",
         os.path.join("..", ".test", "pipeline", "processor"),
         "-v", "--tb=short",
         "--ignore=" + os.path.join("..", ".test", "pipeline", "processor", "test_embedder.py")],
        capture_output=True, text=True, cwd=cwd
    )
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)
    assert result.returncode == 0, f"Processor module tests failed:\n{result.stdout}\n{result.stderr}"
