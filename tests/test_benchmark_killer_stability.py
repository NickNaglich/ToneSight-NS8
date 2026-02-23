import json
import shutil
from pathlib import Path
from uuid import uuid4

from tonesight_ns8.benchmark_killer_stability import run_killer_stability_benchmark


def _temp_dir(prefix: str) -> Path:
    base = Path(".agent") / "test_tmp"
    base.mkdir(parents=True, exist_ok=True)
    for stale in base.glob(f"{prefix}_*"):
        shutil.rmtree(stale, ignore_errors=True)
    root = base / f"{prefix}_{uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    return root


def test_killer_stability_benchmark_contract_and_fields():
    out_root = _temp_dir("tmp_killer_stability_runner")
    payload = run_killer_stability_benchmark(out_root=str(out_root), goldset_path="data/goldset.jsonl")
    assert payload["suite"] == "killer_stability"
    evidence_path = Path(payload["artifacts"]["evidence"])
    assert evidence_path.exists()

    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    assert evidence["benchmark_schema_version"] == "1.0"
    assert evidence["dataset_hash"]
    assert set(evidence["conditions"]) == {"C1", "C2", "C3", "C4"}
    assert set(evidence["distances"]) >= {"tonesight", "equal_width", "quantile", "raw_jsd_hist16"}

    for method, row in evidence["distances"].items():
        assert "d_c1_c2" in row
        assert "d_c1_c3" in row
        assert "d_c2_c4" in row
        assert "separation_ratio_c12_over_c13" in row
        assert isinstance(evidence["separation_ratios"][method], float)


def test_killer_stability_benchmark_is_repeatable():
    out_root = _temp_dir("tmp_killer_stability_repeatable")
    first = run_killer_stability_benchmark(out_root=str(out_root), goldset_path="data/goldset.jsonl")
    first_bytes = Path(first["artifacts"]["evidence"]).read_bytes()

    second = run_killer_stability_benchmark(out_root=str(out_root), goldset_path="data/goldset.jsonl")
    second_bytes = Path(second["artifacts"]["evidence"]).read_bytes()

    assert first["artifacts"]["evidence"] == second["artifacts"]["evidence"]
    assert first_bytes == second_bytes
