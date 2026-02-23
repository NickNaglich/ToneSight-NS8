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
    robustness_path = Path(payload["artifacts"]["robustness_summary"])
    robustness_html_path = Path(payload["artifacts"]["robustness_report_html"])
    assert evidence_path.exists()
    assert robustness_path.exists()
    assert robustness_html_path.exists()

    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    assert evidence["benchmark_schema_version"] == "1.0"
    assert evidence["dataset_hash"]
    assert set(evidence["conditions"]) == {"C1", "C2", "C3", "C4"}
    assert set(evidence["distances"]) >= {"tonesight", "equal_width", "quantile", "raw_jsd_hist16"}
    assert evidence["config"]["drift_sweep_strengths"] == [0.05, 0.1, 0.15, 0.2, 0.3]
    assert set(evidence["drift_sweep"]["rows_by_method"]) >= {"tonesight", "equal_width", "quantile", "raw_jsd_hist16"}
    assert set(evidence["drift_sweep"]["monotonic_non_decreasing"]) >= {"tonesight", "equal_width", "quantile", "raw_jsd_hist16"}
    assert "robustness_sweep" in evidence
    assert "summary" in evidence["robustness_sweep"]
    assert "by_profile" in evidence["robustness_sweep"]["summary"]
    assert set(evidence["robustness_sweep"]["summary"]["by_profile"]) >= {
        "default",
        "oscillation_path",
        "temporal_ramp",
        "subgroup_mixture",
    }
    assert set(evidence["robustness_sweep"]["summary"]["ratio_stats_by_method"]) >= {
        "tonesight",
        "equal_width",
        "quantile",
        "raw_jsd_hist16",
    }
    for method in ("tonesight", "equal_width", "quantile", "raw_jsd_hist16"):
        ratio_stats = evidence["robustness_sweep"]["summary"]["ratio_stats_by_method"][method]
        assert set(ratio_stats) >= {"mean", "std", "min", "max", "p10", "p50", "p90"}
    profile_summary = evidence["robustness_sweep"]["summary"]["by_profile"]["default"]
    assert "wins_by_method" in profile_summary
    assert "ratio_stats_by_method" in profile_summary
    assert "absolute_criteria_pass_rate" in profile_summary
    assert "tonesight_loss_tag_counts" in profile_summary
    pass_rate = evidence["robustness_sweep"]["summary"]["absolute_criteria_pass_rate"]
    assert set(pass_rate) >= {"tonesight", "equal_width", "quantile", "raw_jsd_hist16"}
    for method in ("tonesight", "equal_width", "quantile", "raw_jsd_hist16"):
        assert set(pass_rate[method]) == {
            "separation_ratio_lt_1",
            "true_drift_gt_false_drift",
            "both_ratio_and_true_gt_false",
            "monotonic_drift_sweep_primary",
        }
    assert "tonesight_loss_tag_counts" in evidence["robustness_sweep"]["summary"]
    for row in evidence["robustness_sweep"]["runs"]:
        assert "tonesight_loss_tags" in row
        assert isinstance(row["tonesight_loss_tags"], list)

    for method, row in evidence["distances"].items():
        assert "d_c1_c2" in row
        assert "d_c1_c3" in row
        assert "d_c2_c4" in row
        assert "separation_ratio_c12_over_c13" in row
        assert isinstance(evidence["separation_ratios"][method], float)
        assert method in evidence["summary"]["absolute_criteria"]
        criteria = evidence["summary"]["absolute_criteria"][method]
        assert set(criteria) == {
            "true_drift_gt_false_drift",
            "separation_ratio_lt_1",
            "monotonic_drift_sweep",
        }
        assert isinstance(criteria["true_drift_gt_false_drift"], bool)
        assert isinstance(criteria["separation_ratio_lt_1"], bool)
        assert isinstance(criteria["monotonic_drift_sweep"], bool)


def test_killer_stability_benchmark_is_repeatable():
    out_root = _temp_dir("tmp_killer_stability_repeatable")
    first = run_killer_stability_benchmark(out_root=str(out_root), goldset_path="data/goldset.jsonl")
    first_bytes = Path(first["artifacts"]["evidence"]).read_bytes()
    first_robustness = Path(first["artifacts"]["robustness_summary"]).read_bytes()
    first_html = Path(first["artifacts"]["robustness_report_html"]).read_bytes()

    second = run_killer_stability_benchmark(out_root=str(out_root), goldset_path="data/goldset.jsonl")
    second_bytes = Path(second["artifacts"]["evidence"]).read_bytes()
    second_robustness = Path(second["artifacts"]["robustness_summary"]).read_bytes()
    second_html = Path(second["artifacts"]["robustness_report_html"]).read_bytes()

    assert first["artifacts"]["evidence"] == second["artifacts"]["evidence"]
    assert first_bytes == second_bytes
    assert first["artifacts"]["robustness_summary"] == second["artifacts"]["robustness_summary"]
    assert first_robustness == second_robustness
    assert first["artifacts"]["robustness_report_html"] == second["artifacts"]["robustness_report_html"]
    assert first_html == second_html


def test_killer_stability_supports_phase_flip_cycle_and_pseudo_real_fixture():
    out_root = _temp_dir("tmp_killer_stability_phase_flip")
    payload = run_killer_stability_benchmark(
        out_root=str(out_root),
        goldset_path="data/pseudo_real_trace.jsonl",
        profiles=["default", "phase_flip_cycle"],
        seeds=[0, 1],
        primary_drift_strength=0.2,
        drift_sweep_strengths=[0.1, 0.2],
    )
    evidence = json.loads(Path(payload["artifacts"]["evidence"]).read_text(encoding="utf-8"))
    robustness = evidence["robustness_sweep"]["summary"]
    assert evidence["dataset_path"].replace("\\", "/").endswith("data/pseudo_real_trace.jsonl")
    assert "phase_flip_cycle" in evidence["config"]["robustness"]["available_profiles"]
    assert evidence["config"]["robustness"]["profiles"] == ["default", "phase_flip_cycle"]
    assert "phase_flip_cycle" in robustness["by_profile"]
    for method in ("tonesight", "equal_width", "quantile", "raw_jsd_hist16"):
        assert method in robustness["by_profile"]["phase_flip_cycle"]["ratio_stats_by_method"]
