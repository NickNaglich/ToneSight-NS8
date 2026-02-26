"""Deterministic benchmark harness for OSS evidence artifacts."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from .benchmark_killer_stability import run_killer_stability_benchmark
from .coding_agent_adapter import adapt_coding_agent_event
from .ns8 import compute_A


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def _clamp01(value: float) -> float:
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return value


def _to_u(value_1_to_8: int) -> float:
    return float(value_1_to_8 - 1) / 7.0


def _to_bin_1_to_8(value_0_to_1: float) -> int:
    return max(1, min(8, int(math.floor(value_0_to_1 * 8.0)) + 1))


def _to_scalar(u_v: float, u_a: float, u_d: float) -> float:
    return (u_v + u_a + u_d) / 3.0


def _quantile_thresholds(values: list[float], bins: int = 8) -> list[float]:
    if not values:
        return [0.0] * (bins - 1)
    sorted_values = sorted(values)
    n = len(sorted_values)
    thresholds: list[float] = []
    for i in range(1, bins):
        pos = (i / bins) * (n - 1)
        lo = int(math.floor(pos))
        hi = min(lo + 1, n - 1)
        frac = pos - lo
        value = sorted_values[lo] + (sorted_values[hi] - sorted_values[lo]) * frac
        thresholds.append(float(value))
    return thresholds


def _quantile_bin(value: float, thresholds: list[float]) -> int:
    for i, threshold in enumerate(thresholds, start=1):
        if value <= threshold:
            return i
    return len(thresholds) + 1


def _histogram(states: list[int], bins: int = 8) -> list[float]:
    counts = [0.0] * bins
    if not states:
        return counts
    for state in states:
        idx = max(1, min(bins, int(state))) - 1
        counts[idx] += 1.0
    total = float(len(states))
    return [count / total for count in counts]


def _jsd(p: list[float], q: list[float], epsilon: float = 1e-12) -> float:
    m = [(pi + qi) / 2.0 for pi, qi in zip(p, q)]

    def _kld(a: list[float], b: list[float]) -> float:
        value = 0.0
        for ai, bi in zip(a, b):
            a_eps = max(epsilon, ai)
            b_eps = max(epsilon, bi)
            value += a_eps * math.log2(a_eps / b_eps)
        return value

    return 0.5 * _kld(p, m) + 0.5 * _kld(q, m)


def _psi(p: list[float], q: list[float], epsilon: float = 1e-12) -> float:
    value = 0.0
    for pi, qi in zip(p, q):
        p_eps = max(epsilon, pi)
        q_eps = max(epsilon, qi)
        value += (p_eps - q_eps) * math.log(p_eps / q_eps)
    return value


def _circle_distance_8(a: int, b: int) -> float:
    delta = abs(int(a) - int(b))
    return float(min(delta, 8 - delta))


def _p95(values: list[float]) -> float:
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    idx = int(round(0.95 * (len(sorted_vals) - 1)))
    return float(sorted_vals[idx])


def _load_target_vad(goldset_path: str) -> list[tuple[int, int, int]]:
    rows = _read_jsonl(Path(goldset_path))
    out: list[tuple[int, int, int]] = []
    for row in rows:
        target = row.get("target_vad")
        if not isinstance(target, dict):
            continue
        out.append((int(target["V"]), int(target["A"]), int(target["D"])))
    return out


def _scalar_states(vads: list[tuple[int, int, int]]) -> tuple[list[float], list[int], list[int]]:
    scalars = [_to_scalar(_to_u(v), _to_u(a), _to_u(d)) for v, a, d in vads]
    quantile_thresholds = _quantile_thresholds(scalars, bins=8)
    equal_width = [_to_bin_1_to_8(s) for s in scalars]
    quantile = [_quantile_bin(s, quantile_thresholds) for s in scalars]
    return scalars, equal_width, quantile


def _ns8_states(vads: list[tuple[int, int, int]]) -> list[int]:
    return [compute_A("TLF", v, a, d, 8) for v, a, d in vads]


def _state_methods(vads: list[tuple[int, int, int]], *, quantile_thresholds: list[float] | None = None) -> dict[str, list[int]]:
    scalars = [_to_scalar(_to_u(v), _to_u(a), _to_u(d)) for v, a, d in vads]
    thresholds = quantile_thresholds if quantile_thresholds is not None else _quantile_thresholds(scalars, bins=8)
    return {
        "ns8": _ns8_states(vads),
        "equal_width": [_to_bin_1_to_8(value) for value in scalars],
        "quantile": [_quantile_bin(value, thresholds) for value in scalars],
    }


def _transition_metrics(states: list[int]) -> dict[str, float]:
    if len(states) < 2:
        return {
            "count_transitions": 0.0,
            "mean_step_distance": 0.0,
            "p95_step_distance": 0.0,
            "max_step_distance": 0.0,
            "local_step_ratio": 0.0,
            "jump_rate_ge_2": 0.0,
            "coherence_score": 1.0,
        }

    distances = [_circle_distance_8(states[i - 1], states[i]) for i in range(1, len(states))]
    count = float(len(distances))
    local_count = sum(1 for d in distances if d <= 1.0)
    jump_count = sum(1 for d in distances if d >= 2.0)
    mean_step = sum(distances) / count
    # Ring distance max on 8-state circle is 4; lower average implies stronger locality.
    coherence_score = 1.0 - min(1.0, (mean_step / 4.0))
    return {
        "count_transitions": count,
        "mean_step_distance": mean_step,
        "p95_step_distance": _p95(distances),
        "max_step_distance": max(distances),
        "local_step_ratio": local_count / count,
        "jump_rate_ge_2": jump_count / count,
        "coherence_score": coherence_score,
    }


def _drifted_vads(base_vads: list[tuple[int, int, int]], mode: str) -> list[tuple[int, int, int]]:
    out: list[tuple[int, int, int]] = []
    for i, (v, a, d) in enumerate(base_vads):
        u_v, u_a, u_d = _to_u(v), _to_u(a), _to_u(d)
        if mode == "valence_shift_plus_0.1":
            u_v = _clamp01(u_v + 0.1)
        elif mode == "arousal_variance_x1.3":
            u_a = _clamp01(((u_a - 0.5) * 1.3) + 0.5)
        elif mode == "periodic_arousal_spikes":
            if i % 10 == 0:
                u_a = _clamp01(u_a + 0.25)
        out.append((_to_bin_1_to_8(u_v), _to_bin_1_to_8(u_a), _to_bin_1_to_8(u_d)))
    return out


def _flip_metrics(base: list[int], perturbed: list[int]) -> dict[str, float]:
    n = max(1, len(base))
    flips = 0
    distances: list[float] = []
    for left, right in zip(base, perturbed):
        if int(left) != int(right):
            flips += 1
            distances.append(_circle_distance_8(int(left), int(right)))
    return {
        "flip_rate": flips / n,
        "flip_count": float(flips),
        "avg_flip_distance": (sum(distances) / len(distances)) if distances else 0.0,
    }


def run_noise_tolerance_benchmark(goldset_path: str) -> dict[str, Any]:
    base_vads = _load_target_vad(goldset_path)
    base_ns8 = _ns8_states(base_vads)
    base_scalars, base_equal, base_quantile = _scalar_states(base_vads)
    quantile_thresholds = _quantile_thresholds(base_scalars, bins=8)

    patterns = ((-1, -1, -1), (1, 1, 1), (-1, 1, -1), (1, -1, 1))
    amplitudes = (1e-6, 1e-4, 1e-3)
    result: dict[str, Any] = {"sample_count": len(base_vads), "amplitudes": {}}

    for amplitude in amplitudes:
        perturbed_vads: list[tuple[int, int, int]] = []
        perturbed_scalars: list[float] = []
        for i, (v, a, d) in enumerate(base_vads):
            pv, pa, pd = patterns[i % len(patterns)]
            u_v = _clamp01(_to_u(v) + amplitude * pv)
            u_a = _clamp01(_to_u(a) + amplitude * pa)
            u_d = _clamp01(_to_u(d) + amplitude * pd)
            perturbed_vads.append((_to_bin_1_to_8(u_v), _to_bin_1_to_8(u_a), _to_bin_1_to_8(u_d)))
            perturbed_scalars.append(_to_scalar(u_v, u_a, u_d))

        perturbed_ns8 = _ns8_states(perturbed_vads)
        perturbed_equal = [_to_bin_1_to_8(value) for value in perturbed_scalars]
        perturbed_quantile = [_quantile_bin(value, quantile_thresholds) for value in perturbed_scalars]

        key = f"{amplitude:.0e}"
        result["amplitudes"][key] = {
            "ns8": _flip_metrics(base_ns8, perturbed_ns8),
            "equal_width": _flip_metrics(base_equal, perturbed_equal),
            "quantile": _flip_metrics(base_quantile, perturbed_quantile),
        }
    return result


def run_drift_injection_benchmark(goldset_path: str) -> dict[str, Any]:
    base_vads = _load_target_vad(goldset_path)
    base_scalars, _, _ = _scalar_states(base_vads)
    quantile_thresholds = _quantile_thresholds(base_scalars, bins=8)
    base_states = _state_methods(base_vads, quantile_thresholds=quantile_thresholds)
    scenarios = ("valence_shift_plus_0.1", "arousal_variance_x1.3", "periodic_arousal_spikes")
    out: dict[str, Any] = {"sample_count": len(base_vads), "scenarios": {}}
    base_dists = {
        "ns8": _histogram(base_states["ns8"]),
        "equal_width": _histogram(base_states["equal_width"]),
        "quantile": _histogram(base_states["quantile"]),
    }
    for scenario in scenarios:
        drift_vads = _drifted_vads(base_vads, scenario)
        drift_states = _state_methods(drift_vads, quantile_thresholds=quantile_thresholds)
        out["scenarios"][scenario] = {}
        for key in ("ns8", "equal_width", "quantile"):
            base_hist = base_dists[key]
            drift_hist = _histogram(drift_states[key])
            out["scenarios"][scenario][key] = {
                "jsd": _jsd(base_hist, drift_hist),
                "psi": _psi(base_hist, drift_hist),
                "unused_states_rate": float(sum(1 for p in drift_hist if p == 0.0)) / 8.0,
            }
    return out


def run_model_swap_robustness_benchmark(goldset_path: str) -> dict[str, Any]:
    base_vads = _load_target_vad(goldset_path)

    def _apply_model(model_id: str) -> list[tuple[int, int, int]]:
        out: list[tuple[int, int, int]] = []
        for i, (v, a, d) in enumerate(base_vads):
            nv, na, nd = v, a, d
            if model_id == "model_b":
                if i % 5 == 0:
                    nv += 1
                if i % 7 == 0:
                    na -= 1
                if i % 11 == 0:
                    nd += 1
            elif model_id == "model_a_seed_alt":
                if i % 6 == 0:
                    nv -= 1
                if i % 9 == 0:
                    na += 1
                if i % 13 == 0:
                    nd -= 1
            out.append((max(1, min(8, nv)), max(1, min(8, na)), max(1, min(8, nd))))
        return out

    models = {
        "model_a": _apply_model("model_a"),
        "model_b": _apply_model("model_b"),
        "model_a_seed_alt": _apply_model("model_a_seed_alt"),
    }
    scalar_model_a = [_to_scalar(_to_u(v), _to_u(a), _to_u(d)) for v, a, d in models["model_a"]]
    quantile_thresholds = _quantile_thresholds(scalar_model_a, bins=8)

    states: dict[str, dict[str, list[int]]] = {}
    for model_id, vads in models.items():
        scalars = [_to_scalar(_to_u(v), _to_u(a), _to_u(d)) for v, a, d in vads]
        states[model_id] = {
            "ns8": _ns8_states(vads),
            "equal_width": [_to_bin_1_to_8(value) for value in scalars],
            "quantile": [_quantile_bin(value, quantile_thresholds) for value in scalars],
        }

    def _compare(left: list[int], right: list[int]) -> dict[str, float]:
        n = max(1, len(left))
        mismatch = 0
        dist_sum = 0.0
        for a_state, b_state in zip(left, right):
            if int(a_state) != int(b_state):
                mismatch += 1
            dist_sum += _circle_distance_8(int(a_state), int(b_state))
        return {
            "mismatch_rate": mismatch / n,
            "avg_distance": dist_sum / n,
        }

    pairs = (("model_a", "model_b"), ("model_a", "model_a_seed_alt"))
    out: dict[str, Any] = {"sample_count": len(base_vads), "pairs": {}}
    for left, right in pairs:
        key = f"{left}__vs__{right}"
        out["pairs"][key] = {
            "ns8": _compare(states[left]["ns8"], states[right]["ns8"]),
            "equal_width": _compare(states[left]["equal_width"], states[right]["equal_width"]),
            "quantile": _compare(states[left]["quantile"], states[right]["quantile"]),
        }
    return out


def run_baselines_benchmark(goldset_path: str) -> dict[str, Any]:
    base_vads = _load_target_vad(goldset_path)
    base_scalars, equal_width, quantile = _scalar_states(base_vads)
    quantile_thresholds = _quantile_thresholds(base_scalars, bins=8)
    ns8 = _ns8_states(base_vads)

    def _occupancy(states: list[int]) -> dict[str, float]:
        hist = _histogram(states)
        entropy = 0.0
        for prob in hist:
            if prob > 0:
                entropy -= prob * math.log2(prob)
        return {
            "unused_states_rate": float(sum(1 for prob in hist if prob == 0.0)) / 8.0,
            "entropy_bits": entropy,
        }

    return {
        "sample_count": len(base_vads),
        "quantile_thresholds": quantile_thresholds,
        "ns8": _occupancy(ns8),
        "equal_width": _occupancy(equal_width),
        "quantile": _occupancy(quantile),
        "distance_between_baselines": {
            "jsd_equal_vs_quantile": _jsd(_histogram(equal_width), _histogram(quantile)),
            "psi_equal_vs_quantile": _psi(_histogram(equal_width), _histogram(quantile)),
        },
    }


def run_transition_coherence_benchmark(goldset_path: str) -> dict[str, Any]:
    base_vads = _load_target_vad(goldset_path)
    base_scalars, _, _ = _scalar_states(base_vads)
    quantile_thresholds = _quantile_thresholds(base_scalars, bins=8)
    base_states = _state_methods(base_vads, quantile_thresholds=quantile_thresholds)
    base_metrics = {key: _transition_metrics(states) for key, states in base_states.items()}

    scenarios = ("valence_shift_plus_0.1", "arousal_variance_x1.3", "periodic_arousal_spikes")
    out: dict[str, Any] = {
        "sample_count": len(base_vads),
        "base": base_metrics,
        "scenarios": {},
    }
    for scenario in scenarios:
        drift_vads = _drifted_vads(base_vads, scenario)
        drift_states = _state_methods(drift_vads, quantile_thresholds=quantile_thresholds)
        out["scenarios"][scenario] = {}
        for key in ("ns8", "equal_width", "quantile"):
            metrics = _transition_metrics(drift_states[key])
            baseline = base_metrics[key]
            out["scenarios"][scenario][key] = {
                "metrics": metrics,
                "delta_vs_base": {
                    "mean_step_distance_delta": metrics["mean_step_distance"] - baseline["mean_step_distance"],
                    "local_step_ratio_delta": metrics["local_step_ratio"] - baseline["local_step_ratio"],
                    "coherence_score_delta": metrics["coherence_score"] - baseline["coherence_score"],
                },
            }
    return out


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return float(sum(values) / len(values))


def _coding_agent_summary(events: list[dict[str, Any]]) -> dict[str, Any]:
    feature_rows: list[dict[str, Any]] = []
    for event in events:
        payload = adapt_coding_agent_event(event)
        features = payload["features"]
        bins = payload["bins"]
        feature_rows.append(
            {
                "event_id": str(event.get("event_id", "")),
                "lang_detected": str(features.get("lang_detected", "")),
                "lang_expected": str(features.get("lang_expected", "")),
                "lang_mismatch": int(features.get("lang_mismatch", 0)),
                "response_lines": int(features.get("response_lines", 0)),
                "test_markers": int(features.get("test_markers", 0)),
                "tool_call_count": int(features.get("tool_call_count", 0)),
                "verbosity_bin": int(bins.get("verbosity_bin", 1)),
                "tests_bin": int(bins.get("tests_bin", 1)),
                "tool_call_bin": int(bins.get("tool_call_bin", 1)),
                "lang_mismatch_bin": int(bins.get("lang_mismatch_bin", 1)),
            }
        )
    feature_rows = sorted(feature_rows, key=lambda row: (row["event_id"], row["lang_detected"], row["lang_expected"]))

    mismatch_rate = _mean([float(row["lang_mismatch"]) for row in feature_rows])
    verbosity_bin_mean = _mean([float(row["verbosity_bin"]) for row in feature_rows])
    tests_presence_rate = _mean([1.0 if int(row["test_markers"]) > 0 else 0.0 for row in feature_rows])
    tool_call_rate = _mean([1.0 if int(row["tool_call_count"]) > 0 else 0.0 for row in feature_rows])

    return {
        "count_events": len(feature_rows),
        "metrics": {
            "language_mismatch_rate": mismatch_rate,
            "verbosity_bin_mean": verbosity_bin_mean,
            "tests_presence_rate": tests_presence_rate,
            "tool_call_rate": tool_call_rate,
        },
        "rows": feature_rows,
    }


def _metric_deltas(baseline: dict[str, float], candidate: dict[str, float]) -> dict[str, float]:
    keys = sorted(set(baseline).intersection(candidate))
    return {key: float(candidate[key]) - float(baseline[key]) for key in keys}


def _coding_gate_ready_summary(
    baseline_metrics: dict[str, float],
    candidate_summaries: dict[str, Any],
) -> dict[str, Any]:
    deltas_by_candidate: dict[str, dict[str, float]] = {}
    mismatch_deltas: list[float] = []
    verbosity_deltas: list[float] = []
    tests_deltas: list[float] = []
    tool_call_deltas: list[float] = []

    for path in sorted(candidate_summaries.keys()):
        summary = candidate_summaries[path]
        deltas = _metric_deltas(baseline_metrics, summary["metrics"])
        canonical = {
            "language_mismatch_rate_delta": float(deltas.get("language_mismatch_rate", 0.0)),
            "verbosity_bin_mean_delta": float(deltas.get("verbosity_bin_mean", 0.0)),
            "tests_presence_rate_delta": float(deltas.get("tests_presence_rate", 0.0)),
            "tool_call_rate_delta": float(deltas.get("tool_call_rate", 0.0)),
        }
        deltas_by_candidate[path] = canonical
        mismatch_deltas.append(canonical["language_mismatch_rate_delta"])
        verbosity_deltas.append(canonical["verbosity_bin_mean_delta"])
        tests_deltas.append(canonical["tests_presence_rate_delta"])
        tool_call_deltas.append(canonical["tool_call_rate_delta"])

    return {
        "candidate_deltas": deltas_by_candidate,
        "aggregate_deltas": {
            "max_language_mismatch_rate_delta": max(mismatch_deltas) if mismatch_deltas else 0.0,
            "max_verbosity_bin_mean_delta": max(verbosity_deltas) if verbosity_deltas else 0.0,
            "min_tests_presence_rate_delta": min(tests_deltas) if tests_deltas else 0.0,
            "min_tool_call_rate_delta": min(tool_call_deltas) if tool_call_deltas else 0.0,
        },
        "profile_field_mapping": {
            "max_language_mismatch_rate_delta": "max_language_mismatch_rate_delta",
            "max_verbosity_bin_mean_delta": "max_verbosity_bin_mean_delta",
            "min_tests_presence_rate_delta": "min_tests_presence_rate_delta",
            "min_tool_call_rate_delta": "min_tool_call_rate_delta",
        },
    }


def run_coding_agent_drift_benchmark(
    *,
    out_root: str = "runs",
    baseline_events_path: str = "tests/fixtures/live_event.coding_agent.python.jsonl",
    candidate_events_paths: list[str] | None = None,
) -> dict[str, Any]:
    if candidate_events_paths is None:
        candidate_events_paths = [
            "tests/fixtures/live_event.coding_agent.typescript.jsonl",
            "tests/fixtures/live_event.coding_agent.mismatch.jsonl",
        ]
    candidates = [str(path) for path in candidate_events_paths if str(path).strip()]
    if not candidates:
        raise ValueError("coding_agent_drift benchmark requires at least one candidate events path")

    baseline_path = Path(baseline_events_path)
    baseline_events = _read_jsonl(baseline_path)
    baseline_summary = _coding_agent_summary(baseline_events)
    baseline_metrics = baseline_summary["metrics"]

    candidate_summaries: dict[str, Any] = {}
    for candidate_path_raw in sorted(candidates):
        candidate_path = Path(candidate_path_raw)
        candidate_events = _read_jsonl(candidate_path)
        summary = _coding_agent_summary(candidate_events)
        summary["metric_deltas_vs_baseline"] = _metric_deltas(baseline_metrics, summary["metrics"])
        candidate_summaries[str(candidate_path)] = summary

    gate_ready = _coding_gate_ready_summary(baseline_metrics, candidate_summaries)

    base_dir = Path(out_root) / "benchmarks" / "coding_agent_drift"
    artifacts = {
        "evidence": str(base_dir / "evidence.json"),
        "report": str(base_dir / "report.json"),
    }
    evidence = {
        "spec_version": "1.0",
        "benchmark_schema_version": "1.0",
        "suite": "coding_agent_drift",
        "fixtures": {
            "baseline_events_path": str(baseline_path),
            "candidate_events_paths": sorted(candidate_summaries.keys()),
        },
        "baseline": baseline_summary,
        "candidates": candidate_summaries,
        "gate_ready": gate_ready,
        "artifacts": artifacts,
    }
    report = {
        "spec_version": "1.0",
        "suite": "coding_agent_drift",
        "out_root": out_root,
        "baseline_events_path": str(baseline_path),
        "candidate_count": len(candidate_summaries),
        "artifacts": artifacts,
        "results": {
            "baseline_metrics": baseline_metrics,
            "candidate_metric_deltas": {
                path: summary["metric_deltas_vs_baseline"] for path, summary in sorted(candidate_summaries.items())
            },
            "gate_ready": gate_ready,
        },
    }
    _write_json(Path(artifacts["evidence"]), evidence)
    _write_json(Path(artifacts["report"]), report)
    return report


def run_benchmark_suite(
    *,
    suite: str = "core",
    out_root: str = "runs",
    goldset_path: str = "data/goldset.jsonl",
    killer_profiles: list[str] | None = None,
    killer_seeds: list[int] | None = None,
    killer_primary_strength: float = 0.20,
    killer_sweep_strengths: list[float] | None = None,
    killer_sample_multiplier: int = 1,
    coding_baseline_events: str = "tests/fixtures/live_event.coding_agent.python.jsonl",
    coding_candidate_events: list[str] | None = None,
) -> dict[str, Any]:
    """Run deterministic benchmark suite and write JSON artifacts."""
    if suite == "killer_stability":
        return run_killer_stability_benchmark(
            goldset_path=goldset_path,
            out_root=out_root,
            profiles=killer_profiles,
            seeds=killer_seeds,
            primary_drift_strength=killer_primary_strength,
            drift_sweep_strengths=killer_sweep_strengths,
            sample_multiplier=killer_sample_multiplier,
        )
    if suite == "coding_agent_drift":
        return run_coding_agent_drift_benchmark(
            out_root=out_root,
            baseline_events_path=coding_baseline_events,
            candidate_events_paths=coding_candidate_events,
        )
    if suite != "core":
        raise ValueError(f"Unknown benchmark suite: {suite}")

    base_dir = Path(out_root) / "benchmarks" / suite
    base_dir.mkdir(parents=True, exist_ok=True)

    noise = run_noise_tolerance_benchmark(goldset_path)
    drift = run_drift_injection_benchmark(goldset_path)
    model_swap = run_model_swap_robustness_benchmark(goldset_path)
    baselines = run_baselines_benchmark(goldset_path)
    transition_coherence = run_transition_coherence_benchmark(goldset_path)

    artifacts = {
        "noise_tolerance": str(base_dir / "noise_tolerance.json"),
        "drift_injection": str(base_dir / "drift_injection.json"),
        "model_swap_robustness": str(base_dir / "model_swap_robustness.json"),
        "baselines": str(base_dir / "baselines.json"),
        "transition_coherence": str(base_dir / "transition_coherence.json"),
        "report": str(base_dir / "report.json"),
    }
    _write_json(Path(artifacts["noise_tolerance"]), noise)
    _write_json(Path(artifacts["drift_injection"]), drift)
    _write_json(Path(artifacts["model_swap_robustness"]), model_swap)
    _write_json(Path(artifacts["baselines"]), baselines)
    _write_json(Path(artifacts["transition_coherence"]), transition_coherence)

    report = {
        "spec_version": "1.0",
        "suite": suite,
        "out_root": out_root,
        "goldset_path": goldset_path,
        "sample_count": noise["sample_count"],
        "artifacts": artifacts,
        "results": {
            "noise_tolerance": noise,
            "drift_injection": drift,
            "model_swap_robustness": model_swap,
            "baselines": baselines,
            "transition_coherence": transition_coherence,
        },
    }
    _write_json(Path(artifacts["report"]), report)
    return report
