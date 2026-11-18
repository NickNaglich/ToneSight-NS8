"""Portable-example boundaries; no capture/replay workflow or model execution."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from tonesight_ns8.coding_agent_adapter import adapt_coding_agent_event

FILE = Path(__file__).parents[1] / "examples/paired_coding_agent_gate.py"
SPEC = importlib.util.spec_from_file_location("paired_example", FILE)
example = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(example)


@pytest.mark.parametrize("kind", ["file", "directory"])
def test_existing_output_is_untouched_and_refused_before_capture(tmp_path, monkeypatch, kind):
    output = tmp_path / "existing"
    if kind == "file":
        output.write_bytes(b"keep")
    else:
        output.mkdir()
        (output / "keep").write_bytes(b"keep")
    def forbidden(*args, **kwargs):
        raise AssertionError("capture started before existing-output rejection")
    monkeypatch.setattr(example, "run_live_capture", forbidden)
    with pytest.raises(FileExistsError):
        example.run_example(output)
    assert (output if kind == "file" else output / "keep").read_bytes() == b"keep"


def test_authored_fixture_identity_content_and_controlled_telemetry():
    rows = {name: [json.loads(x) for x in (example.FIXTURES/f"{name}.jsonl").read_text().splitlines()]
            for name in example.TRACES}
    baseline = rows["baseline"]
    for trace, records in rows.items():
        assert len(records) == 2
        assert [r["event_id"] for r in records] == [r["event_id"] for r in baseline]
        assert all(r["meta"] == baseline[i]["meta"] for i, r in enumerate(records))
        for i, record in enumerate(records):
            telemetry = adapt_coding_agent_event(record)
            assert telemetry["features"]["lang_mismatch"] == int(trace == "negative")
            assert telemetry["features"]["test_markers"] == 0
            assert telemetry["features"]["tool_call_count"] == 1
            assert telemetry["bins"]["verbosity_bin"] == 1
            assert all(1 <= x <= 8 for x in telemetry["bins"].values())
            assert telemetry["vad"] == ({"V": 1, "A": 1, "D": 1} if trace == "negative" else {"V": 3, "A": 1, "D": 3})
            same_hash = example.stable_event_hash(record) == example.stable_event_hash(baseline[i])
            assert same_hash is (trace != "negative")


@pytest.mark.parametrize("stdout", [b'{"decision":"incompatible"}', b'not JSON'])
def test_native_gate_exit_and_raw_streams_are_preserved(tmp_path, monkeypatch, stdout):
    def fake(args, **kwargs):
        assert "--allow-dataset-mismatch" in args and "coding_agent_drift" in args
        assert not any(arg.startswith("--min-") or arg.startswith("--max-") for arg in args)
        return SimpleNamespace(returncode=3, stdout=stdout, stderr=b"native diagnostic")
    monkeypatch.setattr(example.subprocess, "run", fake)
    code, payload = example._gate(tmp_path, "positive", "baseline", "candidate")
    assert code == 3
    assert payload == ({"decision": "incompatible"} if stdout.startswith(b"{") else None)
    assert (tmp_path/"positive.gate.stdout.bin").read_bytes() == stdout
    assert (tmp_path/"positive.gate.stderr.bin").read_bytes() == b"native diagnostic"
    assert json.loads((tmp_path/"positive.gate.command.json").read_text())["exit"] == 3


def test_capture_exception_keeps_partial_inputs_and_failure(tmp_path, monkeypatch):
    def broken(*args, **kwargs):
        raise RuntimeError("fixture capture failed")
    monkeypatch.setattr(example, "run_live_capture", broken)
    output = tmp_path/"new"
    result = example.run_example(output)
    assert result["status"] == "failed" and result["example_exit_code"] == 1
    assert result["stage"] == "baseline capture" and result["native_gate_exit"] is None
    assert result["error"] == {"type": "RuntimeError", "message": "fixture capture failed"}
    assert (output/"inputs/baseline.jsonl").exists() and (output/"inputs.json").exists()
    assert json.loads((output/"failure.json").read_text()) == result


def test_incompatible_native_gate_remains_exit3_and_stops_before_negative(tmp_path, monkeypatch):
    monkeypatch.setattr(example, "run_live_capture", lambda *a, **k: {"capture_dir": "fake", "event_count": 2})
    monkeypatch.setattr(example, "run_live_replay", lambda *a, **k: {
        "out_dir": "fake", "summary": {"count_rows": 2, "accepted_count": 2, "invalid_count": 0, "quarantined_count": 0}})
    monkeypatch.setattr(example, "run_compare", lambda *a, **k: {})
    seen = []
    def gate(*args):
        seen.append(args[1])
        return 3, {"decision": "incompatible", "incompatibilities": [{"reason": "model_identity_mismatch"}]}
    monkeypatch.setattr(example, "_gate", gate)
    result = example.run_example(tmp_path/"new")
    assert result["status"] == "failed" and result["example_exit_code"] == result["native_gate_exit"] == 3
    assert seen == ["positive"]  # no forced behavioral failure or negative retry


def test_dangling_symlink_is_refused_without_creating_its_target(tmp_path, monkeypatch):
    target = tmp_path / "must_not_create"
    output = tmp_path / "dangling"
    try:
        output.symlink_to(target, target_is_directory=True)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"Platform cannot create this symlink: {exc}")
    assert output.is_symlink() and not output.exists()
    def forbidden(*args, **kwargs):
        raise AssertionError("capture started for an existing dangling symlink")
    monkeypatch.setattr(example, "run_live_capture", forbidden)
    with pytest.raises(FileExistsError):
        example.run_example(output)
    assert output.is_symlink() and not target.exists()


def test_lexical_symlink_is_rejected_before_resolution_or_capture(tmp_path, monkeypatch):
    requested = tmp_path / "pretend_symlink"
    original_link, original_resolve = Path.is_symlink, Path.resolve
    monkeypatch.setattr(Path, "is_symlink", lambda path: True if path == requested else original_link(path))
    def resolve(path, *args, **kwargs):
        if path == requested:
            raise AssertionError("existing requested symlink was resolved")
        return original_resolve(path, *args, **kwargs)
    monkeypatch.setattr(Path, "resolve", resolve)
    def forbidden(*args, **kwargs):
        raise AssertionError("capture started for a requested symlink")
    monkeypatch.setattr(example, "run_live_capture", forbidden)
    with pytest.raises(FileExistsError):
        example.run_example(requested)
    assert not requested.exists()
