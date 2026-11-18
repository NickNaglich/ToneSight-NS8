import json
import shutil

import pytest
from pathlib import Path
from uuid import uuid4

from tonesight_ns8.canary_runner import run_canary


def _temp_dir(prefix: str) -> Path:
    base = Path(".agent") / "test_tmp"
    base.mkdir(parents=True, exist_ok=True)
    for stale in base.glob(f"{prefix}_*"):
        shutil.rmtree(stale, ignore_errors=True)
    root = base / f"{prefix}_{uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    return root


def test_run_canary_replays_same_capture_and_gates():
    root = _temp_dir("tmp_canary")
    baseline_root = root / "baseline"
    candidate_root = root / "candidate"

    payload = run_canary(
        "tests/fixtures/live_capture.small.jsonl",
        baseline_out_root=str(baseline_root),
        candidate_out_root=str(candidate_root),
        baseline_taxonomy_path="taxonomy/tone_taxonomy.v1.json",
        candidate_taxonomy_path="taxonomy/tone_taxonomy.v1.json",
        shadow_strict="quarantine",
        top_n=5,
    )

    assert payload["capture"]["same_capture_id"] is True
    assert Path(payload["baseline"]["out_dir"]).exists()
    assert Path(payload["candidate"]["out_dir"]).exists()
    assert payload["compare_summary"]["run_a"]["run_id"] == payload["baseline"]["run_id"]
    assert payload["compare_summary"]["run_b"]["run_id"] == payload["candidate"]["run_id"]
    assert payload["gate_result"]["decision"] in {"passed", "regressed", "incompatible"}
    assert payload["exit_code"] == payload["gate_result"]["exit_code"]


@pytest.mark.parametrize(
    "adapter,profile,explicit_pin,allow_dataset,effective_pin",
    [
        ("upstream_signal", None, False, False, False),
        ("coding_agent", None, True, True, True),
        ("coding_agent", "coding_agent_drift", False, True, True),
        ("coding_agent", None, False, False, False),
    ],
)
def test_canary_routes_adapter_identity_and_dataset_policy(
    monkeypatch, adapter, profile, explicit_pin, allow_dataset, effective_pin
):
    from tonesight_ns8 import canary_runner

    calls = {"replay": [], "gate": [], "compare": []}

    def replay(capture, **kwargs):
        calls["replay"].append((capture, kwargs))
        return {"out_dir": kwargs["out_root"], "capture_id": "synthetic"}

    def gate(a, b, **kwargs):
        calls["gate"].append((a, b, kwargs))
        return {"decision": "regressed", "exit_code": 2}

    def compare(a, b, **kwargs):
        calls["compare"].append((a, b, kwargs))
        return {"compare_summary": {"matched_count": 2}}

    monkeypatch.setattr(canary_runner, "run_live_replay", replay)
    monkeypatch.setattr(canary_runner, "run_gate", gate)
    monkeypatch.setattr(canary_runner, "run_compare", compare)
    result = run_canary(
        "authored.jsonl", baseline_out_root="base", candidate_out_root="candidate",
        adapter=adapter, profile=profile, require_pinned_model_identity=explicit_pin,
        allow_dataset_mismatch=allow_dataset,
    )
    assert len(calls["replay"]) == 2
    for capture, kwargs in calls["replay"]:
        assert capture == "authored.jsonl"
        assert kwargs["adapter"] == adapter
        assert kwargs["require_pinned_model_identity"] is effective_pin
    assert [k["out_root"] for _, k in calls["replay"]] == ["base", "candidate"]
    assert len(calls["gate"]) == len(calls["compare"]) == 1
    for stage in ("gate", "compare"):
        a, b, kwargs = calls[stage][0]
        assert (a, b) == ("base", "candidate")
        assert kwargs["require_dataset_match"] is (not allow_dataset)
    assert calls["gate"][0][2]["profile"] == profile
    assert calls["gate"][0][2]["require_pinned_model_identity"] is (True if explicit_pin else None)
    assert calls["compare"][0][2]["require_pinned_model_identity"] is effective_pin
    assert result["exit_code"] == 2  # Native decision is preserved, not coerced to success.
    # The emitted policy describes enforcement, not execution/identity attestation.
    assert result["replay_policy"] == {
        "adapter": adapter, "require_pinned_model_identity": effective_pin,
    }
    assert result["evidence_scope"] == {
        "operation": "recorded_capture_replay",
        "live_model_execution": "not_performed_by_canary",
        "model_identity_attestation": "not_performed_by_canary",
    }


@pytest.mark.parametrize("flags,adapter,pinned", [
    ([], "upstream_signal", False),
    (["--adapter", "coding_agent", "--require-pinned-model-identity"], "coding_agent", True),
])
def test_canary_cli_forwards_options(monkeypatch, capsys, flags, adapter, pinned):
    from tonesight_ns8 import cli

    calls = []
    def fake(capture, **kwargs):
        calls.append((capture, kwargs))
        return {"exit_code": 3, "gate_result": {"decision": "incompatible"}}

    monkeypatch.setattr(cli, "run_canary", fake)
    assert cli.main(["canary", "--capture", "synthetic.jsonl", "--allow-dataset-mismatch", *flags]) == 3
    assert calls[0][0] == "synthetic.jsonl"
    assert calls[0][1]["adapter"] == adapter
    assert calls[0][1]["require_pinned_model_identity"] is pinned
    assert calls[0][1]["allow_dataset_mismatch"] is True
    assert json.loads(capsys.readouterr().out)["gate_result"]["decision"] == "incompatible"


def test_canary_cli_adapter_choices_follow_native_registry(monkeypatch):
    from tonesight_ns8 import cli, live_runner

    monkeypatch.setitem(live_runner._LIVE_ADAPTER_REGISTRY, "test_canary_adapter", lambda *_: None)
    assert cli.build_parser().parse_args(["canary", "--capture", "unused", "--adapter", "test_canary_adapter"]).adapter == "test_canary_adapter"
    with pytest.raises(SystemExit) as exc:
        cli.build_parser().parse_args(["canary", "--capture", "unused", "--adapter", "unsupported"])
    assert exc.value.code == 2


@pytest.mark.parametrize("kwargs,message", [
    ({"adapter": "unsupported"}, "unknown live adapter"),
    ({"require_pinned_model_identity": True}, "only supported with adapter='coding_agent'"),
    ({"profile": "coding_agent_drift"}, "only supported with adapter='coding_agent'"),
])
def test_canary_native_adapter_validation_before_capture(tmp_path, kwargs, message):
    out = tmp_path / "output"
    with pytest.raises(ValueError, match=message):
        run_canary(str(tmp_path / "absent.jsonl"), baseline_out_root=str(out), **kwargs)
    assert not out.exists()


@pytest.mark.parametrize("profile,explicit_pin,meta", [
    (None, True, {}),
    ("coding_agent_drift", False, {"provider": "synthetic", "model_tag": "fixture"}),
])
def test_canary_rejects_unpinned_coding_capture(tmp_path, profile, explicit_pin, meta):
    # A tiny validation fixture, not a new paired acceptance or model call.
    row = json.loads(Path("examples/paired_coding_agent_gate/baseline.jsonl").read_text().splitlines()[0])
    row["meta"] = meta
    capture = tmp_path / "unpinned.jsonl"
    capture.write_text(json.dumps(row) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="pinned model identity missing required fields"):
        run_canary(
            str(capture), adapter="coding_agent", profile=profile,
            require_pinned_model_identity=explicit_pin,
            baseline_out_root=str(tmp_path / "baseline"),
            candidate_out_root=str(tmp_path / "candidate"),
        )
    assert not (tmp_path / "candidate").exists()
    assert not list((tmp_path / "baseline").rglob("receipt.json"))


@pytest.mark.parametrize("baseline_identity,candidate_identity,expected_a,expected_b,same", [
    ({"summary": {"capture_id": "known"}}, {"summary": {"capture_id": "known"}}, "known", "known", True),
    ({"receipt": {"capture_id": "known"}}, {"receipt": {"capture_id": "other"}}, "known", "other", False),
    ({"summary": {"capture_id": "known"}}, {"receipt": {"capture_id": "known"}}, "known", "known", True),
    ({}, {}, None, None, False),
    ({"summary": {"capture_id": "known"}}, {}, "known", None, False),
    ({"summary": {"capture_id": ""}}, {"receipt": {"capture_id": "   "}}, None, None, False),
])
def test_canary_reports_only_known_capture_identity(
    monkeypatch, baseline_identity, candidate_identity, expected_a, expected_b, same
):
    from tonesight_ns8 import canary_runner

    replies = iter([
        {"out_dir": "baseline", **baseline_identity},
        {"out_dir": "candidate", **candidate_identity},
    ])
    monkeypatch.setattr(canary_runner, "run_live_replay", lambda *a, **k: next(replies))
    monkeypatch.setattr(canary_runner, "run_gate", lambda *a, **k: {"exit_code": 0})
    monkeypatch.setattr(canary_runner, "run_compare", lambda *a, **k: {"compare_summary": {}})
    capture = run_canary("unused.jsonl")["capture"]
    assert capture["baseline_capture_id"] == expected_a
    assert capture["candidate_capture_id"] == expected_b
    assert capture["same_capture_id"] is same



def test_canary_cli_reports_replay_scope_without_attesting_declared_identity(monkeypatch, capsys):
    from tonesight_ns8 import canary_runner, cli

    replays = []
    declared = {
        "capture_id": "offline_capture",
        "provider": "caller_claimed_provider",
        "model_tag": "caller_claimed:v1",
        "model_version": "caller_claimed_version",
        "generation_settings": {"temperature": 0},
    }

    def replay(capture, **kwargs):
        replays.append(kwargs)
        return {"out_dir": kwargs["out_root"], "receipt": dict(declared)}

    def gate(*args, **kwargs):
        assert kwargs["require_pinned_model_identity"] is None
        assert kwargs["require_dataset_match"] is False
        return {"decision": "passed", "exit_code": 0}

    def compare(*args, **kwargs):
        assert kwargs["require_pinned_model_identity"] is True
        assert kwargs["require_dataset_match"] is False
        return {"compare_summary": {"rows": {"count_common_ids": 2}}}

    monkeypatch.setattr(canary_runner, "run_live_replay", replay)
    monkeypatch.setattr(canary_runner, "run_gate", gate)
    monkeypatch.setattr(canary_runner, "run_compare", compare)
    code = cli.main([
        "canary", "--capture", "unused-offline-stub.jsonl", "--adapter", "coding_agent",
        "--profile", "coding_agent_drift", "--allow-dataset-mismatch",
    ])
    streams = capsys.readouterr()
    assert code == 0 and streams.err == ""
    report = json.loads(streams.out)
    assert len(replays) == 2 and all(k["require_pinned_model_identity"] is True for k in replays)
    assert report["replay_policy"] == {"adapter": "coding_agent", "require_pinned_model_identity": True}
    assert report["evidence_scope"] == {
        "operation": "recorded_capture_replay",
        "live_model_execution": "not_performed_by_canary",
        "model_identity_attestation": "not_performed_by_canary",
    }
    assert report["baseline"]["receipt"] == report["candidate"]["receipt"] == declared
    assert report["gate_result"] == {"decision": "passed", "exit_code": 0}
