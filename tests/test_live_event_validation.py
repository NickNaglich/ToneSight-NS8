import json
import subprocess
import sys
from pathlib import Path


def test_validate_live_event_accepts_valid_fixture():
    valid_path = Path("tests/fixtures/live_event.valid.jsonl")
    proc = subprocess.run(
        [sys.executable, "tools/validate_live_event.py", str(valid_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    payload = json.loads(proc.stdout.strip())
    assert payload["valid"] is True
    assert payload["path"] == str(valid_path)


def test_validate_live_event_rejects_invalid_fixture_with_reason_code():
    invalid_path = Path("tests/fixtures/live_event.invalid.jsonl")
    proc = subprocess.run(
        [sys.executable, "tools/validate_live_event.py", str(invalid_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode != 0
    payload = json.loads(proc.stderr.strip())
    assert payload["valid"] is False
    assert payload["error"]["code"] == "missing_required"
    assert "event_id" in payload["error"]["message"]

