import subprocess
import sys
from pathlib import Path


def test_validate_goldset_accepts_repo_goldset():
    proc = subprocess.run(
        [sys.executable, "tools/validate_goldset.py", "data/goldset.jsonl"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    assert "goldset valid" in (proc.stdout + proc.stderr)


def test_validate_goldset_rejects_invalid_fixture():
    bad_path = Path("tests/fixtures/goldset.invalid.jsonl")
    proc = subprocess.run(
        [sys.executable, "tools/validate_goldset.py", str(bad_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode != 0
    assert "boundary rows must include structured or anchor tag" in (proc.stdout + proc.stderr)
