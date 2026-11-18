"""Honest gate messaging for the admitted pinned-identity consumer boundary."""
import json
from pathlib import Path

import pytest

from tonesight_ns8.gate_runner import run_gate


ROOT = Path(__file__).parents[1]


def fixture_meta(name):
    path = ROOT / f"tests/fixtures/live_event.coding_agent.{name}.jsonl"
    return json.loads(path.read_text(encoding="utf-8").splitlines()[0])["meta"]


def receipt(meta, run_id):
    return {"run_id": run_id, "spec_version": "1.0", "mapping_id": "ns8",
            "mapping_version": "1.0", "taxonomy_hash": "authored-fixture-taxonomy",
            "defaults_spec_version": "1.0", "dataset_hash": "same-fixture-dataset",
            "config": {"calibration_path": ""}, "provider": meta["provider"],
            "model_tag": meta["model_tag"], "model_digest": meta["model_digest"],
            "generation_settings": meta["generation_settings"]}


@pytest.mark.parametrize("scenario,expected_reasons,require_dataset_match", [
    ("identity", {"model_identity_mismatch", "generation_identity_mismatch"}, False),
    ("dataset", {"dataset_hash_mismatch"}, True),
    ("spec", {"spec_version_mismatch"}, False),
])
def test_incompatibility_summary_does_not_misattribute_the_failure(
    tmp_path, scenario, expected_reasons, require_dataset_match
):
    a = receipt(fixture_meta("python"), "baseline")
    b = receipt(fixture_meta("mismatch" if scenario == "identity" else "python"), "candidate")
    if scenario == "dataset":
        b["dataset_hash"] = "different-fixture-dataset"
    elif scenario == "spec":
        b["spec_version"] = "2.0"
    paths = [tmp_path/"baseline", tmp_path/"candidate"]
    for path, payload in zip(paths, [a, b]):
        path.mkdir()
        (path/"receipt.json").write_text(json.dumps(payload), encoding="utf-8")
    # Receipt-only fixtures intentionally provide no metrics/out.jsonl: an
    # incompatible run must stop before behavioral thresholds or scoring.
    result = run_gate(str(paths[0]), str(paths[1]), profile="coding_agent_drift",
                      gate_profiles_path=str(ROOT/"config/gate_profiles.json"),
                      require_dataset_match=require_dataset_match)
    assert result["decision"] == "incompatible" and result["exit_code"] == 3
    assert {x["reason"] for x in result["incompatibilities"]} == expected_reasons
    assert result["thresholds"]["require_pinned_model_identity"] is True
    assert result["require_dataset_match"] is require_dataset_match
    assert result["violations"] == []
    # The generic human sentence must not name an unsupported cause; structured
    # incompatibilities above retain the exact actionable reasons and fields.
    text = result["human_summary"].lower()
    assert "incompatible" in text
    assert not any(cause in text for cause in {
        "identity": ["dataset", "spec"],
        "dataset": ["model", "generation", "spec"],
        "spec": ["dataset", "model", "generation"],
    }[scenario])
