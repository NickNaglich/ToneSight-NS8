"""Deterministic killer-stability benchmark (v0.2.1)."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

from .ns8 import compute_A
from .provenance import get_code_revision


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def _dataset_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


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


def _scalar(vad: tuple[int, int, int]) -> float:
    v, a, d = vad
    return (_to_u(v) + _to_u(a) + _to_u(d)) / 3.0


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
    for idx, threshold in enumerate(thresholds, start=1):
        if value <= threshold:
            return idx
    return len(thresholds) + 1


def _histogram(states: list[int], bins: int) -> list[float]:
    counts = [0.0] * bins
    if not states:
        return counts
    for state in states:
        idx = max(1, min(bins, int(state))) - 1
        counts[idx] += 1.0
    total = float(len(states))
    return [count / total for count in counts]


def _histogram_continuous(values: list[float], bins: int) -> list[float]:
    counts = [0.0] * bins
    if not values:
        return counts
    for value in values:
        clipped = _clamp01(float(value))
        idx = min(bins - 1, int(math.floor(clipped * bins)))
        counts[idx] += 1.0
    total = float(len(values))
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


def _ks(values_a: list[float], values_b: list[float]) -> float:
    if not values_a or not values_b:
        return 0.0
    a = sorted(_clamp01(v) for v in values_a)
    b = sorted(_clamp01(v) for v in values_b)
    n_a = len(a)
    n_b = len(b)
    i = 0
    j = 0
    cdf_a = 0.0
    cdf_b = 0.0
    max_delta = 0.0
    while i < n_a and j < n_b:
        if a[i] <= b[j]:
            i += 1
            cdf_a = i / n_a
        else:
            j += 1
            cdf_b = j / n_b
        max_delta = max(max_delta, abs(cdf_a - cdf_b))
    while i < n_a:
        i += 1
        cdf_a = i / n_a
        max_delta = max(max_delta, abs(cdf_a - cdf_b))
    while j < n_b:
        j += 1
        cdf_b = j / n_b
        max_delta = max(max_delta, abs(cdf_a - cdf_b))
    return max_delta


def _safe_ratio(numerator: float, denominator: float) -> float:
    if denominator == 0.0:
        return 0.0 if numerator == 0.0 else float("inf")
    return numerator / denominator


def _extract_base_vads(path: Path) -> list[tuple[int, int, int]]:
    rows = _read_jsonl(path)
    out: list[tuple[int, int, int]] = []
    for row in rows:
        target = row.get("target_vad")
        if not isinstance(target, dict):
            continue
        out.append((int(target["V"]), int(target["A"]), int(target["D"])))
    if not out:
        raise ValueError("benchmark dataset has no valid target_vad rows")
    return out


def _upstream_variant(vads: list[tuple[int, int, int]], variant: str) -> list[tuple[int, int, int]]:
    out: list[tuple[int, int, int]] = []
    for v, a, d in vads:
        u_v = _to_u(v)
        u_a = _to_u(a)
        u_d = _to_u(d)
        if variant == "A":
            pass
        elif variant == "B":
            # Deterministic mild calibration shift for model-swap simulation.
            u_v = _clamp01((u_v * 1.03) + 0.02)
            u_a = _clamp01((u_a * 0.98) - 0.01)
            u_d = _clamp01((u_d * 1.01) + 0.00)
        else:
            raise ValueError(f"unknown upstream variant: {variant}")
        out.append((_to_bin_1_to_8(u_v), _to_bin_1_to_8(u_a), _to_bin_1_to_8(u_d)))
    return out


def _inject_drift(vads: list[tuple[int, int, int]]) -> list[tuple[int, int, int]]:
    out: list[tuple[int, int, int]] = []
    for i, (v, a, d) in enumerate(vads):
        u_v = _to_u(v)
        u_a = _to_u(a)
        u_d = _to_u(d)

        # Regime shift on deterministic subset.
        if i % 5 == 0:
            u_v = _clamp01(u_v - 0.14)
            u_a = _clamp01(u_a + 0.14)

        # Occasional deterministic spikes.
        if i % 50 == 0:
            u_a = _clamp01(u_a + 0.24)
            u_d = _clamp01(u_d + 0.08)

        out.append((_to_bin_1_to_8(u_v), _to_bin_1_to_8(u_a), _to_bin_1_to_8(u_d)))
    return out


def _condition_vads(base_vads: list[tuple[int, int, int]]) -> dict[str, list[tuple[int, int, int]]]:
    c1 = _upstream_variant(base_vads, "A")
    c2 = _upstream_variant(base_vads, "B")
    c3 = _inject_drift(_upstream_variant(base_vads, "A"))
    c4 = _inject_drift(_upstream_variant(base_vads, "B"))
    return {"C1": c1, "C2": c2, "C3": c3, "C4": c4}


def run_killer_stability_benchmark(
    *,
    goldset_path: str = "data/goldset.jsonl",
    out_root: str = "runs",
) -> dict[str, Any]:
    dataset_path = Path(goldset_path)
    base_vads = _extract_base_vads(dataset_path)
    conditions = _condition_vads(base_vads)

    scalars_by_condition = {key: [_scalar(vad) for vad in rows] for key, rows in conditions.items()}
    quantile_thresholds = _quantile_thresholds(scalars_by_condition["C1"], bins=8)

    states_by_condition = {
        key: {
            "tonesight": [compute_A("TLF", v, a, d, 8) for v, a, d in rows],
            "equal_width": [_to_bin_1_to_8(value) for value in scalars_by_condition[key]],
            "quantile": [_quantile_bin(value, quantile_thresholds) for value in scalars_by_condition[key]],
        }
        for key, rows in conditions.items()
    }

    def _pair_distance(method: str, left: str, right: str) -> float:
        bins = 8
        p = _histogram(states_by_condition[left][method], bins=bins)
        q = _histogram(states_by_condition[right][method], bins=bins)
        return _jsd(p, q)

    distances: dict[str, dict[str, float]] = {}
    for method in ("tonesight", "equal_width", "quantile"):
        d_c1_c2 = _pair_distance(method, "C1", "C2")
        d_c1_c3 = _pair_distance(method, "C1", "C3")
        d_c2_c4 = _pair_distance(method, "C2", "C4")
        distances[method] = {
            "d_c1_c2": d_c1_c2,
            "d_c1_c3": d_c1_c3,
            "d_c2_c4": d_c2_c4,
            "separation_ratio_c12_over_c13": _safe_ratio(d_c1_c2, d_c1_c3),
        }

    raw_hist_c1 = _histogram_continuous(scalars_by_condition["C1"], bins=16)
    raw_hist_c2 = _histogram_continuous(scalars_by_condition["C2"], bins=16)
    raw_hist_c3 = _histogram_continuous(scalars_by_condition["C3"], bins=16)
    raw_hist_c4 = _histogram_continuous(scalars_by_condition["C4"], bins=16)
    raw_d_c1_c2 = _jsd(raw_hist_c1, raw_hist_c2)
    raw_d_c1_c3 = _jsd(raw_hist_c1, raw_hist_c3)
    raw_d_c2_c4 = _jsd(raw_hist_c2, raw_hist_c4)
    distances["raw_jsd_hist16"] = {
        "d_c1_c2": raw_d_c1_c2,
        "d_c1_c3": raw_d_c1_c3,
        "d_c2_c4": raw_d_c2_c4,
        "separation_ratio_c12_over_c13": _safe_ratio(raw_d_c1_c2, raw_d_c1_c3),
        "psi_c1_c2": _psi(raw_hist_c1, raw_hist_c2),
        "psi_c1_c3": _psi(raw_hist_c1, raw_hist_c3),
        "ks_c1_c2": _ks(scalars_by_condition["C1"], scalars_by_condition["C2"]),
        "ks_c1_c3": _ks(scalars_by_condition["C1"], scalars_by_condition["C3"]),
    }

    separation_ratios = {
        method: float(payload["separation_ratio_c12_over_c13"])
        for method, payload in sorted(distances.items())
    }
    ranking = sorted(separation_ratios.items(), key=lambda item: (item[1], item[0]))

    code_revision = get_code_revision()
    evidence = {
        "spec_version": "1.0",
        "benchmark_schema_version": "1.0",
        "dataset_path": str(dataset_path),
        "dataset_hash": _dataset_hash(dataset_path),
        "code_revision": code_revision,
        "conditions": {
            "C1": {"content": "same", "upstream": "A", "drift_injected": False},
            "C2": {"content": "same", "upstream": "B", "drift_injected": False},
            "C3": {"content": "same", "upstream": "A", "drift_injected": True},
            "C4": {"content": "same", "upstream": "B", "drift_injected": True},
        },
        "config": {
            "seed": 0,
            "quantile_bins": 8,
            "equal_width_bins": 8,
            "raw_hist_bins": 16,
            "upstream_b": {"v_scale": 1.03, "v_bias": 0.02, "a_scale": 0.98, "a_bias": -0.01, "d_scale": 1.01},
            "drift_injection": {
                "regime_every_n": 5,
                "regime_v_bias": -0.14,
                "regime_a_bias": 0.14,
                "spike_every_n": 50,
                "spike_a_bias": 0.24,
                "spike_d_bias": 0.08,
            },
            "methods": ["tonesight", "equal_width", "quantile", "raw_jsd_hist16"],
        },
        "distances": distances,
        "separation_ratios": separation_ratios,
        "summary": {
            "best_method_by_lowest_separation_ratio": ranking[0][0],
            "method_ranking": [{"method": key, "separation_ratio": value} for key, value in ranking],
        },
    }

    out_dir = Path(out_root) / "benchmarks" / "killer_stability"
    out_dir.mkdir(parents=True, exist_ok=True)
    evidence_path = out_dir / "evidence.json"
    evidence_path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return {
        "spec_version": "1.0",
        "suite": "killer_stability",
        "out_root": out_root,
        "goldset_path": goldset_path,
        "sample_count": len(base_vads),
        "artifacts": {"evidence": str(evidence_path), "report": str(evidence_path)},
        "results": {"killer_stability": evidence},
    }

