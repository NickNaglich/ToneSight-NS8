import json
import shutil
from pathlib import Path
from uuid import uuid4

import pytest

import tonesight_ns8.live_runner as live_runner_module
from tonesight_ns8.live_runner import run_live_capture, run_live_replay, run_live_verify


def _temp_dir(prefix: str) -> Path:
    base = Path(".agent") / "test_tmp"
    base.mkdir(parents=True, exist_ok=True)
    for stale in base.glob(f"{prefix}_*"):
        shutil.rmtree(stale, ignore_errors=True)
    root = base / f"{prefix}_{uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    return root


def test_live_capture_and_replay_create_standard_artifacts():
    out_root = _temp_dir("tmp_live_capture_replay")
    capture = run_live_capture("tests/fixtures/live_capture.small.jsonl", out_root=str(out_root))
    assert capture["event_count"] == 2

    replay = run_live_replay(
        capture["capture_dir"],
        out_root=str(out_root),
        taxonomy_path="taxonomy/tone_taxonomy.v1.json",
        threshold_l1=3,
        shadow_strict="quarantine",
    )
    run_dir = Path(replay["out_dir"])
    assert run_dir.exists()
    assert (run_dir / "out.jsonl").exists()
    assert (run_dir / "eval_summary.json").exists()
    assert (run_dir / "report.html").exists()
    assert (run_dir / "receipt.json").exists()
    assert isinstance(replay["summary"]["summary_schema_version"], str)
    assert replay["summary"]["summary_schema_version"] != ""
    assert isinstance(replay["receipt"]["receipt_schema_version"], str)
    assert replay["receipt"]["receipt_schema_version"] != ""
    assert replay["summary"]["count_rows"] == 2
    assert replay["summary"]["invalid_count"] == 0


def test_live_verify_reports_stable_hashes():
    out_root = _temp_dir("tmp_live_verify")
    capture = run_live_capture("tests/fixtures/live_capture.small.jsonl", out_root=str(out_root))
    verify = run_live_verify(
        capture["capture_dir"],
        out_root=str(out_root),
        taxonomy_path="taxonomy/tone_taxonomy.v1.json",
        threshold_l1=3,
        shadow_strict="quarantine",
    )
    assert verify["stable"] is True
    assert verify["mismatched_artifacts"] == []
    assert verify["hashes_first"] == verify["hashes_second"]
    assert verify["exit_code"] == 0


def test_live_replay_quarantine_for_missing_upstream_signal():
    out_root = _temp_dir("tmp_live_quarantine")
    events_path = out_root / "events.invalid_signal.jsonl"
    rows = [
        {
            "event_id": "evt_valid",
            "source": "chat",
            "timestamp_received": "2026-02-20T12:00:00Z",
            "text": "Thanks for your help.",
            "upstream_label": "empathetic",
            "meta": {"session_id": "s1"},
            "privacy_flags": {"contains_pii": False, "allow_store_raw": True},
        },
        {
            "event_id": "evt_missing",
            "source": "chat",
            "timestamp_received": "2026-02-20T12:00:01Z",
            "text": "No upstream signal attached.",
            "meta": {"session_id": "s1"},
            "privacy_flags": {"contains_pii": False, "allow_store_raw": True},
        },
    ]
    events_path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    capture = run_live_capture(str(events_path), out_root=str(out_root))
    replay = run_live_replay(
        capture["capture_dir"],
        out_root=str(out_root),
        taxonomy_path="taxonomy/tone_taxonomy.v1.json",
        threshold_l1=3,
        shadow_strict="quarantine",
    )
    assert replay["summary"]["count_rows"] == 1
    assert replay["summary"]["invalid_count"] == 1
    quarantine_path = Path(replay["shadow_policy"]["quarantine_path"])
    assert quarantine_path.exists()
    quarantine_rows = [json.loads(line) for line in quarantine_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(quarantine_rows) == 1
    assert quarantine_rows[0]["error"]["code"] == "missing_upstream_signal"


def test_live_replay_applies_redaction_and_receipt_summary():
    out_root = _temp_dir("tmp_live_redaction")
    events_path = out_root / "events.redact.jsonl"
    rows = [
        {
            "event_id": "evt_redact",
            "source": "chat",
            "timestamp_received": "2026-02-20T12:00:00Z",
            "text": "Email me at user@example.com or call 555-123-4567",
            "upstream_label": "empathetic",
            "meta": {"session_id": "s1"},
            "privacy_flags": {"contains_pii": True, "allow_store_raw": False},
        }
    ]
    events_path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    capture = run_live_capture(str(events_path), out_root=str(out_root))
    replay = run_live_replay(
        capture["capture_dir"],
        out_root=str(out_root),
        taxonomy_path="taxonomy/tone_taxonomy.v1.json",
        threshold_l1=3,
        shadow_strict="quarantine",
    )
    out_rows = [json.loads(line) for line in (Path(replay["out_dir"]) / "out.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    assert out_rows[0]["text"] == "Email me at [EMAIL] or call [PHONE]"
    assert replay["summary"]["redaction_summary"] == {"EMAIL": 1, "PHONE": 1, "SSN": 0}
    assert replay["receipt"]["redaction_summary"] == {"EMAIL": 1, "PHONE": 1, "SSN": 0}


def test_live_replay_receipt_code_revision_optional_semantics(monkeypatch):
    out_root = _temp_dir("tmp_live_code_revision")
    capture = run_live_capture("tests/fixtures/live_capture.small.jsonl", out_root=str(out_root))

    monkeypatch.setattr(live_runner_module, "get_code_revision", lambda: "cafebabefeed")
    replay_with = run_live_replay(
        capture["capture_dir"],
        out_root=str(out_root),
        taxonomy_path="taxonomy/tone_taxonomy.v1.json",
        threshold_l1=3,
        shadow_strict="quarantine",
    )
    assert replay_with["receipt"]["code_revision"] == "cafebabefeed"

    monkeypatch.setattr(live_runner_module, "get_code_revision", lambda: None)
    replay_without = run_live_replay(
        capture["capture_dir"],
        out_root=str(out_root),
        taxonomy_path="taxonomy/tone_taxonomy.v1.json",
        threshold_l1=3,
        shadow_strict="quarantine",
    )
    assert "code_revision" not in replay_without["receipt"]


def test_live_replay_coding_agent_adapter_emits_bins_and_adapter_receipt():
    out_root = _temp_dir("tmp_live_coding_agent")
    events_path = out_root / "events.coding_agent.jsonl"
    rows = [
        {
            "event_id": "evt_coding_1",
            "source": "coding_agent",
            "timestamp_received": "2026-02-25T12:00:00Z",
            "text": "import os\n\ndef solve(x):\n    try:\n        return x\n    except Exception:\n        raise\n",
            "meta": {
                "session_id": "s1",
                "agent_id": "coder",
                "expected_language": "python",
                "tool_calls": 1,
                "provider": "ollama",
                "model_tag": "qwen3-coder:latest",
                "model_digest": "sha256:abc123",
                "generation_settings": {"temperature": 0, "top_p": 1, "seed": 1},
            },
            "privacy_flags": {"contains_pii": False, "allow_store_raw": False},
        }
    ]
    events_path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    capture = run_live_capture(str(events_path), out_root=str(out_root))
    replay = run_live_replay(
        capture["capture_dir"],
        out_root=str(out_root),
        taxonomy_path="taxonomy/tone_taxonomy.v1.json",
        threshold_l1=3,
        shadow_strict="quarantine",
        adapter="coding_agent",
    )
    out_rows = [json.loads(line) for line in (Path(replay["out_dir"]) / "out.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    assert replay["summary"]["count_rows"] == 1
    assert out_rows[0]["adapter_id"] == "coding_agent"
    assert "coding_agent_features" in out_rows[0]
    assert "coding_agent_bins" in out_rows[0]
    assert replay["receipt"]["adapter_id"] == "coding_agent"
    assert replay["receipt"]["config"]["adapter"] == "coding_agent"
    assert replay["receipt"]["provider"] == "ollama"
    assert replay["receipt"]["model_tag"] == "qwen3-coder:latest"
    assert replay["receipt"]["model_digest"] == "sha256:abc123"
    assert replay["receipt"]["generation_settings"] == {"seed": 1, "temperature": 0, "top_p": 1}
    assert replay["receipt"]["capture_schema_version"] == "1.0"


def test_live_verify_coding_agent_adapter_stable():
    out_root = _temp_dir("tmp_live_verify_coding_agent")
    events_path = out_root / "events.coding_agent.verify.jsonl"
    rows = [
        {
            "event_id": "evt_coding_2",
            "source": "coding_agent",
            "timestamp_received": "2026-02-25T12:00:00Z",
            "text": "const x: string = 'ok';\ntry { return x; } catch (e) { throw e; }",
            "meta": {"session_id": "s2", "agent_id": "coder", "expected_language": "typescript"},
            "privacy_flags": {"contains_pii": False, "allow_store_raw": False},
        }
    ]
    events_path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    capture = run_live_capture(str(events_path), out_root=str(out_root))
    verify = run_live_verify(
        capture["capture_dir"],
        out_root=str(out_root),
        taxonomy_path="taxonomy/tone_taxonomy.v1.json",
        threshold_l1=3,
        shadow_strict="quarantine",
        adapter="coding_agent",
    )
    assert verify["stable"] is True
    assert verify["mismatched_artifacts"] == []


def test_live_replay_unknown_adapter_rejected():
    out_root = _temp_dir("tmp_live_unknown_adapter")
    capture = run_live_capture("tests/fixtures/live_capture.small.jsonl", out_root=str(out_root))
    with pytest.raises(ValueError, match="unknown live adapter"):
        run_live_replay(
            capture["capture_dir"],
            out_root=str(out_root),
            taxonomy_path="taxonomy/tone_taxonomy.v1.json",
            threshold_l1=3,
            shadow_strict="quarantine",
            adapter="not_supported",
        )


def test_live_replay_require_pinned_identity_passes_for_coding_agent():
    out_root = _temp_dir("tmp_live_require_pinned_ok")
    events_path = out_root / "events.coding_agent.pinned_ok.jsonl"
    rows = [
        {
            "event_id": "evt_coding_pinned_ok",
            "source": "coding_agent",
            "timestamp_received": "2026-02-25T12:00:00Z",
            "text": "def solve(x):\n    return x\n",
            "meta": {
                "session_id": "s1",
                "agent_id": "coder",
                "expected_language": "python",
                "provider": "ollama",
                "model_tag": "qwen3-coder:latest",
                "model_digest": "sha256:abc123",
                "generation_settings": {"temperature": 0, "top_p": 1, "seed": 1},
            },
            "privacy_flags": {"contains_pii": False, "allow_store_raw": False},
        }
    ]
    events_path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    capture = run_live_capture(str(events_path), out_root=str(out_root))
    replay = run_live_replay(
        capture["capture_dir"],
        out_root=str(out_root),
        taxonomy_path="taxonomy/tone_taxonomy.v1.json",
        threshold_l1=3,
        shadow_strict="quarantine",
        adapter="coding_agent",
        require_pinned_model_identity=True,
    )
    assert replay["receipt"]["provider"] == "ollama"
    assert replay["receipt"]["model_tag"] == "qwen3-coder:latest"
    assert replay["receipt"]["model_digest"] == "sha256:abc123"
    assert replay["receipt"]["config"]["require_pinned_model_identity"] is True


def test_live_replay_require_pinned_identity_fails_when_missing_fields():
    out_root = _temp_dir("tmp_live_require_pinned_missing")
    events_path = out_root / "events.coding_agent.pinned_missing.jsonl"
    rows = [
        {
            "event_id": "evt_coding_pinned_missing",
            "source": "coding_agent",
            "timestamp_received": "2026-02-25T12:00:00Z",
            "text": "def solve(x):\n    return x\n",
            "meta": {
                "session_id": "s1",
                "agent_id": "coder",
                "expected_language": "python",
            },
            "privacy_flags": {"contains_pii": False, "allow_store_raw": False},
        }
    ]
    events_path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    capture = run_live_capture(str(events_path), out_root=str(out_root))
    with pytest.raises(ValueError, match="pinned model identity missing required fields"):
        run_live_replay(
            capture["capture_dir"],
            out_root=str(out_root),
            taxonomy_path="taxonomy/tone_taxonomy.v1.json",
            threshold_l1=3,
            shadow_strict="quarantine",
            adapter="coding_agent",
            require_pinned_model_identity=True,
        )


def test_live_replay_require_pinned_identity_rejected_for_non_coding_adapter():
    out_root = _temp_dir("tmp_live_require_pinned_non_coding")
    capture = run_live_capture("tests/fixtures/live_capture.small.jsonl", out_root=str(out_root))
    with pytest.raises(ValueError, match="only supported with adapter='coding_agent'"):
        run_live_replay(
            capture["capture_dir"],
            out_root=str(out_root),
            taxonomy_path="taxonomy/tone_taxonomy.v1.json",
            threshold_l1=3,
            shadow_strict="quarantine",
            adapter="upstream_signal",
            require_pinned_model_identity=True,
        )
