"""Deterministic killer-stability benchmark (v0.2.1)."""

from __future__ import annotations

import hashlib
import html
import json
import math
from pathlib import Path
from typing import Any

from .ns8 import compute_A
from .provenance import get_code_revision

_DEFAULT_ROBUSTNESS_PROFILES: tuple[str, ...] = ("default", "oscillation_path", "temporal_ramp", "subgroup_mixture")
_DEFAULT_ROBUSTNESS_SEEDS: tuple[int, ...] = (0, 1, 2, 3, 4)
_AVAILABLE_ROBUSTNESS_PROFILES: tuple[str, ...] = (
    "default",
    "oscillation_path",
    "temporal_ramp",
    "subgroup_mixture",
    "boundary_jitter",
    "phase_flip_cycle",
)


def _render_robustness_report_html(evidence: dict[str, Any]) -> str:
    summary = evidence.get("robustness_sweep", {}).get("summary", {})
    wins = summary.get("wins_by_method", {})
    stats = summary.get("ratio_stats_by_method", {})
    pass_rates = summary.get("absolute_criteria_pass_rate", {})
    profiles = summary.get("by_profile", {})
    method_rows = sorted(stats.keys())
    profile_rows = sorted(profiles.keys())

    method_table_rows = []
    for method in method_rows:
        method_stats = stats.get(method, {})
        method_pass = pass_rates.get(method, {})
        method_wins = int(wins.get(method, 0))
        method_table_rows.append(
            "<tr>"
            f"<td>{html.escape(method)}</td>"
            f"<td>{method_wins}</td>"
            f"<td>{float(method_stats.get('mean', 0.0)):.6f}</td>"
            f"<td>{float(method_stats.get('p50', 0.0)):.6f}</td>"
            f"<td>{float(method_stats.get('p90', 0.0)):.6f}</td>"
            f"<td>{float(method_stats.get('max', 0.0)):.6f}</td>"
            f"<td>{float(method_pass.get('separation_ratio_lt_1', 0.0)):.6f}</td>"
            f"<td>{float(method_pass.get('true_drift_gt_false_drift', 0.0)):.6f}</td>"
            f"<td>{float(method_pass.get('both_ratio_and_true_gt_false', 0.0)):.6f}</td>"
            "</tr>"
        )

    profile_table_rows = []
    for profile in profile_rows:
        profile_summary = profiles.get(profile, {})
        profile_wins = profile_summary.get("wins_by_method", {})
        tonesight_wins = int(profile_wins.get("tonesight", 0))
        equal_width_wins = int(profile_wins.get("equal_width", 0))
        quantile_wins = int(profile_wins.get("quantile", 0))
        raw_wins = int(profile_wins.get("raw_jsd_hist16", 0))
        profile_table_rows.append(
            "<tr>"
            f"<td>{html.escape(profile)}</td>"
            f"<td>{tonesight_wins}</td>"
            f"<td>{equal_width_wins}</td>"
            f"<td>{quantile_wins}</td>"
            f"<td>{raw_wins}</td>"
            "</tr>"
        )

    return (
        "<!doctype html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '<meta charset="utf-8" />\n'
        "<title>ToneSight Robustness Report</title>\n"
        "<style>\n"
        "body{font-family:Segoe UI,Arial,sans-serif;background:#f8fafc;color:#0f172a;margin:20px;}\n"
        "h1,h2{margin:0 0 12px 0;}\n"
        ".panel{background:#ffffff;border:1px solid #cbd5e1;border-radius:8px;padding:12px;margin-bottom:14px;}\n"
        "table{width:100%;border-collapse:collapse;}\n"
        "th,td{border:1px solid #cbd5e1;padding:6px 8px;text-align:left;font-size:12px;}\n"
        "th{background:#e2e8f0;}\n"
        ".muted{color:#475569;font-size:12px;}\n"
        "code{background:#e2e8f0;padding:1px 3px;border-radius:4px;}\n"
        "</style>\n"
        "</head>\n"
        "<body>\n"
        "<h1>ToneSight Killer Stability Robustness Report</h1>\n"
        "<div class=\"muted\">Deterministic summary generated from evidence.json</div>\n"
        "<div class=\"panel\">"
        f"<div><strong>spec_version:</strong> {html.escape(str(evidence.get('spec_version', '')))}</div>"
        f"<div><strong>benchmark_schema_version:</strong> {html.escape(str(evidence.get('benchmark_schema_version', '')))}</div>"
        f"<div><strong>dataset_hash:</strong> <code>{html.escape(str(evidence.get('dataset_hash', '')))}</code></div>"
        f"<div><strong>code_revision:</strong> <code>{html.escape(str(evidence.get('code_revision', '')))}</code></div>"
        "</div>\n"
        "<div class=\"panel\">"
        "<h2>Global Method Summary</h2>"
        "<table><thead><tr>"
        "<th>method</th><th>wins</th><th>mean</th><th>p50</th><th>p90</th><th>max</th>"
        "<th>ratio&lt;1 pass</th><th>true&gt;false pass</th><th>combined pass</th>"
        "</tr></thead><tbody>"
        + "".join(method_table_rows)
        + "</tbody></table></div>\n"
        "<div class=\"panel\">"
        "<h2>Profile Wins</h2>"
        "<table><thead><tr>"
        "<th>profile</th><th>tonesight</th><th>equal_width</th><th>quantile</th><th>raw_jsd_hist16</th>"
        "</tr></thead><tbody>"
        + "".join(profile_table_rows)
        + "</tbody></table></div>\n"
        "</body>\n"
        "</html>\n"
    )


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


def _circle_distance_8(a: int, b: int) -> float:
    delta = abs(int(a) - int(b))
    return float(min(delta, 8 - delta))


def _topology_pair_distance(left: list[int], right: list[int]) -> float:
    if not left or not right:
        return 0.0
    count = float(min(len(left), len(right)))
    if count == 0:
        return 0.0
    total = 0.0
    for a_state, b_state in zip(left, right):
        total += _circle_distance_8(a_state, b_state) / 4.0
    return total / count


def _transition_distribution(states: list[int], bins: int = 8) -> list[float]:
    if len(states) < 2:
        return [0.0] * (bins * bins)
    counts = [0.0] * (bins * bins)
    for i in range(1, len(states)):
        left = max(1, min(bins, int(states[i - 1]))) - 1
        right = max(1, min(bins, int(states[i]))) - 1
        idx = left * bins + right
        counts[idx] += 1.0
    total = float(len(states) - 1)
    return [value / total for value in counts]


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


def _mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return float(sum(values) / len(values))


def _std(values: list[float]) -> float:
    if len(values) <= 1:
        return 0.0
    mu = _mean(values)
    return float(math.sqrt(sum((v - mu) ** 2 for v in values) / len(values)))


def _quantile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    pos = q * (len(sorted_vals) - 1)
    lo = int(math.floor(pos))
    hi = min(lo + 1, len(sorted_vals) - 1)
    frac = pos - lo
    return float(sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * frac)


def _rate(flags: list[bool]) -> float:
    if not flags:
        return 0.0
    return float(sum(1 for flag in flags if flag) / len(flags))


def _seed_noise(seed: int, index: int, channel: int) -> float:
    # deterministic pseudo-noise in [-1, 1]
    angle = (seed + 1) * (index + 3) * (channel + 5) * 0.173
    return float(math.sin(angle))


def _profile_params(profile: str, seed: int) -> dict[str, Any]:
    if profile == "default":
        return {
            "upstream_b": {"v_scale": 1.03, "v_bias": 0.02, "a_scale": 0.98, "a_bias": -0.01, "d_scale": 1.01},
            "drift": {"global_v": -0.30, "global_a": 0.30, "regime_v": -0.25, "regime_a": 0.25, "spike_a": 0.40, "spike_d": 0.15, "regime_every_n": 5, "spike_every_n": 20, "mode": "default"},
            "seed_jitter": 0.02 if seed != 0 else 0.0,
        }
    if profile == "oscillation_path":
        return {
            "upstream_b": {"v_scale": 1.02, "v_bias": 0.03, "a_scale": 0.97, "a_bias": -0.02, "d_scale": 1.00},
            "drift": {"global_v": -0.20, "global_a": 0.20, "regime_v": -0.15, "regime_a": 0.15, "spike_a": 0.30, "spike_d": 0.10, "regime_every_n": 6, "spike_every_n": 16, "mode": "oscillation_path"},
            "seed_jitter": 0.03,
        }
    if profile == "temporal_ramp":
        return {
            "upstream_b": {"v_scale": 1.04, "v_bias": 0.01, "a_scale": 0.95, "a_bias": -0.01, "d_scale": 1.02},
            "drift": {"global_v": -0.22, "global_a": 0.28, "regime_v": -0.18, "regime_a": 0.20, "spike_a": 0.32, "spike_d": 0.12, "regime_every_n": 5, "spike_every_n": 22, "mode": "temporal_ramp"},
            "seed_jitter": 0.035,
        }
    if profile == "subgroup_mixture":
        return {
            "upstream_b": {"v_scale": 1.05, "v_bias": 0.00, "a_scale": 0.96, "a_bias": -0.02, "d_scale": 1.01},
            "drift": {"global_v": -0.18, "global_a": 0.24, "regime_v": -0.22, "regime_a": 0.26, "spike_a": 0.35, "spike_d": 0.14, "regime_every_n": 7, "spike_every_n": 25, "mode": "subgroup_mixture"},
            "seed_jitter": 0.03,
        }
    if profile == "boundary_jitter":
        return {
            "upstream_b": {"v_scale": 1.01, "v_bias": 0.015, "a_scale": 0.99, "a_bias": -0.015, "d_scale": 1.00},
            "drift": {"global_v": -0.16, "global_a": 0.16, "regime_v": -0.12, "regime_a": 0.12, "spike_a": 0.22, "spike_d": 0.06, "regime_every_n": 4, "spike_every_n": 18, "mode": "boundary_jitter"},
            "seed_jitter": 0.025,
        }
    if profile == "phase_flip_cycle":
        return {
            "upstream_b": {"v_scale": 1.02, "v_bias": 0.01, "a_scale": 0.98, "a_bias": -0.01, "d_scale": 1.01},
            "drift": {
                "global_v": -0.12,
                "global_a": 0.12,
                "regime_v": -0.18,
                "regime_a": 0.18,
                "spike_a": 0.28,
                "spike_d": 0.10,
                "regime_every_n": 6,
                "spike_every_n": 24,
                "mode": "phase_flip_cycle",
            },
            "seed_jitter": 0.03,
        }
    raise ValueError(f"unknown robustness profile: {profile}")


def _tonesight_loss_tags(
    *,
    profile: str,
    winner: str,
    method_distances: dict[str, dict[str, float]],
) -> list[str]:
    if winner == "tonesight":
        return []

    tags: list[str] = []
    tonesight = method_distances["tonesight"]
    winner_metrics = method_distances.get(winner, {})

    if tonesight["d_c1_c3"] <= tonesight["d_c1_c2"]:
        tags.append("true_drift_not_dominant")

    if winner == "equal_width" and winner_metrics:
        if winner_metrics["d_c1_c2"] < tonesight["d_c1_c2"]:
            tags.append("occupancy_dominated_shift")

    if profile == "subgroup_mixture":
        tags.append("subgroup_underpowered")
    elif profile == "temporal_ramp":
        tags.append("ramp_mild_or_late")
    elif profile == "oscillation_path":
        tags.append("transition_signal_weak")
    elif profile == "phase_flip_cycle":
        tags.append("phase_flip_competition")

    if not tags:
        tags.append("competitive_baseline_overlap")
    return tags


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


def _upstream_variant(vads: list[tuple[int, int, int]], variant: str, *, params: dict[str, Any], seed: int) -> list[tuple[int, int, int]]:
    out: list[tuple[int, int, int]] = []
    for v, a, d in vads:
        u_v = _to_u(v)
        u_a = _to_u(a)
        u_d = _to_u(d)
        if variant == "A":
            pass
        elif variant == "B":
            upstream = params["upstream_b"]
            jitter = float(params.get("seed_jitter", 0.0))
            u_v = _clamp01((u_v * float(upstream["v_scale"])) + float(upstream["v_bias"]) + (jitter * _seed_noise(seed, len(out), 1)))
            u_a = _clamp01((u_a * float(upstream["a_scale"])) + float(upstream["a_bias"]) + (jitter * _seed_noise(seed, len(out), 2)))
            u_d = _clamp01((u_d * float(upstream["d_scale"])) + (jitter * _seed_noise(seed, len(out), 3)))
        else:
            raise ValueError(f"unknown upstream variant: {variant}")
        out.append((_to_bin_1_to_8(u_v), _to_bin_1_to_8(u_a), _to_bin_1_to_8(u_d)))
    return out


def _inject_drift(vads: list[tuple[int, int, int]], *, strength: float, params: dict[str, Any], seed: int) -> list[tuple[int, int, int]]:
    out: list[tuple[int, int, int]] = []
    for i, (v, a, d) in enumerate(vads):
        u_v = _to_u(v)
        u_a = _to_u(a)
        u_d = _to_u(d)

        drift = params["drift"]
        jitter = float(params.get("seed_jitter", 0.0))
        mode = str(drift.get("mode", "default"))
        # Global behavioral drift across all samples.
        u_v = _clamp01(u_v + (float(drift["global_v"]) * strength) + (jitter * 0.5 * _seed_noise(seed, i, 4)))
        u_a = _clamp01(u_a + (float(drift["global_a"]) * strength) + (jitter * 0.5 * _seed_noise(seed, i, 5)))

        if mode == "oscillation_path":
            direction = -1.0 if (i % 2 == 0) else 1.0
            u_v = _clamp01(u_v + (direction * 0.18 * strength))
            u_a = _clamp01(u_a - (direction * 0.12 * strength))
        elif mode == "temporal_ramp":
            ramp = float(i) / max(1.0, float(len(vads) - 1))
            u_v = _clamp01(u_v - (0.24 * strength * ramp))
            u_a = _clamp01(u_a + (0.24 * strength * ramp))
        elif mode == "subgroup_mixture":
            # Drift only a deterministic subgroup to emulate mixture shift.
            if (i % 3) == 0:
                u_v = _clamp01(u_v - (0.30 * strength))
                u_a = _clamp01(u_a + (0.30 * strength))
        elif mode == "boundary_jitter":
            # Push samples around bin boundaries to emulate upstream quantization jitter.
            direction = -1.0 if ((i + seed) % 2 == 0) else 1.0
            u_v = _clamp01(u_v + (direction * 0.11 * strength))
            u_a = _clamp01(u_a - (direction * 0.09 * strength))
        elif mode == "phase_flip_cycle":
            # Flip drift direction by deterministic phase block to emulate regime cycling.
            phase_block = ((i // 12) + seed) % 2
            direction = -1.0 if phase_block == 0 else 1.0
            u_v = _clamp01(u_v + (direction * 0.20 * strength))
            u_a = _clamp01(u_a - (direction * 0.16 * strength))

        # Regime shift on deterministic subset.
        if i % int(drift["regime_every_n"]) == 0:
            u_v = _clamp01(u_v + (float(drift["regime_v"]) * strength))
            u_a = _clamp01(u_a + (float(drift["regime_a"]) * strength))

        # Occasional deterministic spikes.
        if i % int(drift["spike_every_n"]) == 0:
            u_a = _clamp01(u_a + (float(drift["spike_a"]) * strength))
            u_d = _clamp01(u_d + (float(drift["spike_d"]) * strength))

        out.append((_to_bin_1_to_8(u_v), _to_bin_1_to_8(u_a), _to_bin_1_to_8(u_d)))
    return out


def _condition_vads(
    base_vads: list[tuple[int, int, int]],
    *,
    drift_strength: float,
    profile: str,
    seed: int,
) -> dict[str, list[tuple[int, int, int]]]:
    params = _profile_params(profile, seed)
    c1 = _upstream_variant(base_vads, "A", params=params, seed=seed)
    c2 = _upstream_variant(base_vads, "B", params=params, seed=seed)
    c3 = _inject_drift(_upstream_variant(base_vads, "A", params=params, seed=seed), strength=drift_strength, params=params, seed=seed)
    c4 = _inject_drift(_upstream_variant(base_vads, "B", params=params, seed=seed), strength=drift_strength, params=params, seed=seed)
    return {"C1": c1, "C2": c2, "C3": c3, "C4": c4}


def run_killer_stability_benchmark(
    *,
    goldset_path: str = "data/goldset.jsonl",
    out_root: str = "runs",
    profiles: list[str] | None = None,
    seeds: list[int] | None = None,
    primary_drift_strength: float = 0.20,
    drift_sweep_strengths: list[float] | None = None,
    sample_multiplier: int = 1,
) -> dict[str, Any]:
    dataset_path = Path(goldset_path)
    base_vads = _extract_base_vads(dataset_path)
    if sample_multiplier < 1:
        raise ValueError("sample_multiplier must be >= 1")
    if sample_multiplier > 1:
        base_vads = base_vads * sample_multiplier

    robustness_profiles = tuple(profiles) if profiles else _DEFAULT_ROBUSTNESS_PROFILES
    robustness_seeds = tuple(seeds) if seeds else _DEFAULT_ROBUSTNESS_SEEDS
    for profile in robustness_profiles:
        if profile not in _AVAILABLE_ROBUSTNESS_PROFILES:
            raise ValueError(
                f"unknown robustness profile: {profile}; available={list(_AVAILABLE_ROBUSTNESS_PROFILES)}"
            )
    sweep_strengths = drift_sweep_strengths or [0.05, 0.10, 0.15, 0.20, 0.30]
    primary_strength = float(primary_drift_strength)
    primary_profile = "default" if "default" in robustness_profiles else robustness_profiles[0]
    conditions = _condition_vads(base_vads, drift_strength=primary_strength, profile=primary_profile, seed=0)

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
        left_states = states_by_condition[left][method]
        right_states = states_by_condition[right][method]
        occupancy_jsd = _jsd(_histogram(left_states, bins=bins), _histogram(right_states, bins=bins))
        if method != "tonesight":
            return occupancy_jsd

        # ToneSight primary metric: topology + transition sensitivity.
        topology = _topology_pair_distance(left_states, right_states)
        transition_jsd = _jsd(
            _transition_distribution(left_states, bins=bins),
            _transition_distribution(right_states, bins=bins),
        )
        return (0.7 * topology) + (0.2 * transition_jsd) + (0.1 * occupancy_jsd)

    distances: dict[str, dict[str, float]] = {}
    core_methods = ("tonesight", "equal_width", "quantile")
    for method in core_methods:
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

    # Drift-strength sweep for sensitivity and monotonicity checks.
    sweep_rows: dict[str, list[dict[str, float]]] = {method: [] for method in distances}
    for strength in sweep_strengths:
        sweep_conditions = _condition_vads(base_vads, drift_strength=strength, profile=primary_profile, seed=0)
        sweep_scalars = {key: [_scalar(vad) for vad in rows] for key, rows in sweep_conditions.items()}
        sweep_quantile_thresholds = _quantile_thresholds(sweep_scalars["C1"], bins=8)
        sweep_states = {
            key: {
                "tonesight": [compute_A("TLF", v, a, d, 8) for v, a, d in rows],
                "equal_width": [_to_bin_1_to_8(value) for value in sweep_scalars[key]],
                "quantile": [_quantile_bin(value, sweep_quantile_thresholds) for value in sweep_scalars[key]],
            }
            for key, rows in sweep_conditions.items()
        }
        for method in core_methods:
            p = _histogram(sweep_states["C1"][method], bins=8)
            q = _histogram(sweep_states["C3"][method], bins=8)
            sweep_rows[method].append({"strength": strength, "d_c1_c3": _jsd(p, q)})

        sweep_raw_hist_c1 = _histogram_continuous(sweep_scalars["C1"], bins=16)
        sweep_raw_hist_c3 = _histogram_continuous(sweep_scalars["C3"], bins=16)
        sweep_rows["raw_jsd_hist16"].append(
            {"strength": strength, "d_c1_c3": _jsd(sweep_raw_hist_c1, sweep_raw_hist_c3)}
        )

    monotonic_non_decreasing: dict[str, bool] = {}
    for method, rows in sweep_rows.items():
        values = [float(item["d_c1_c3"]) for item in rows]
        monotonic_non_decreasing[method] = all(
            values[i] <= values[i + 1] + 1e-12 for i in range(len(values) - 1)
        )

    absolute_criteria: dict[str, dict[str, bool]] = {}
    for method, row in distances.items():
        false_drift = float(row["d_c1_c2"])
        true_drift = float(row["d_c1_c3"])
        ratio = float(row["separation_ratio_c12_over_c13"])
        absolute_criteria[method] = {
            "true_drift_gt_false_drift": true_drift > false_drift,
            "separation_ratio_lt_1": ratio < 1.0,
            "monotonic_drift_sweep": monotonic_non_decreasing.get(method, False),
        }

    robustness_runs: list[dict[str, Any]] = []
    robustness_by_method: dict[str, list[float]] = {method: [] for method in distances}
    win_count: dict[str, int] = {method: 0 for method in distances}
    profile_method_ratios: dict[str, dict[str, list[float]]] = {
        profile: {method: [] for method in distances} for profile in robustness_profiles
    }
    profile_win_count: dict[str, dict[str, int]] = {
        profile: {method: 0 for method in distances} for profile in robustness_profiles
    }
    profile_tonesight_loss_tags: dict[str, dict[str, int]] = {
        profile: {} for profile in robustness_profiles
    }
    profile_criteria: dict[str, dict[str, dict[str, list[bool]]]] = {
        profile: {
            method: {
                "separation_ratio_lt_1": [],
                "true_drift_gt_false_drift": [],
                "both_ratio_and_true_gt_false": [],
            }
            for method in distances
        }
        for profile in robustness_profiles
    }
    robustness_criteria: dict[str, dict[str, list[bool]]] = {
        method: {
            "separation_ratio_lt_1": [],
            "true_drift_gt_false_drift": [],
            "both_ratio_and_true_gt_false": [],
        }
        for method in distances
    }
    tonesight_loss_tag_counts: dict[str, int] = {}
    for profile in robustness_profiles:
        for seed in robustness_seeds:
            robust_conditions = _condition_vads(base_vads, drift_strength=primary_strength, profile=profile, seed=seed)
            robust_scalars = {key: [_scalar(vad) for vad in rows] for key, rows in robust_conditions.items()}
            robust_thresholds = _quantile_thresholds(robust_scalars["C1"], bins=8)
            robust_states = {
                key: {
                    "tonesight": [compute_A("TLF", v, a, d, 8) for v, a, d in rows],
                    "equal_width": [_to_bin_1_to_8(value) for value in robust_scalars[key]],
                    "quantile": [_quantile_bin(value, robust_thresholds) for value in robust_scalars[key]],
                }
                for key, rows in robust_conditions.items()
            }
            robust_distances: dict[str, float] = {}
            robust_method_distances: dict[str, dict[str, float]] = {}
            for method in core_methods:
                def _rpair(left: str, right: str) -> float:
                    left_states = robust_states[left][method]
                    right_states = robust_states[right][method]
                    occ = _jsd(_histogram(left_states, bins=8), _histogram(right_states, bins=8))
                    if method != "tonesight":
                        return occ
                    top = _topology_pair_distance(left_states, right_states)
                    trans = _jsd(_transition_distribution(left_states, bins=8), _transition_distribution(right_states, bins=8))
                    return (0.7 * top) + (0.2 * trans) + (0.1 * occ)
                d12 = _rpair("C1", "C2")
                d13 = _rpair("C1", "C3")
                robust_distances[method] = _safe_ratio(d12, d13)
                robust_method_distances[method] = {
                    "d_c1_c2": d12,
                    "d_c1_c3": d13,
                    "separation_ratio_c12_over_c13": robust_distances[method],
                }
            robust_raw_hist_c1 = _histogram_continuous(robust_scalars["C1"], bins=16)
            robust_raw_hist_c2 = _histogram_continuous(robust_scalars["C2"], bins=16)
            robust_raw_hist_c3 = _histogram_continuous(robust_scalars["C3"], bins=16)
            robust_distances["raw_jsd_hist16"] = _safe_ratio(
                _jsd(robust_raw_hist_c1, robust_raw_hist_c2),
                _jsd(robust_raw_hist_c1, robust_raw_hist_c3),
            )
            robust_method_distances["raw_jsd_hist16"] = {
                "d_c1_c2": _jsd(robust_raw_hist_c1, robust_raw_hist_c2),
                "d_c1_c3": _jsd(robust_raw_hist_c1, robust_raw_hist_c3),
                "separation_ratio_c12_over_c13": robust_distances["raw_jsd_hist16"],
            }
            winner = sorted(robust_distances.items(), key=lambda item: (item[1], item[0]))[0][0]
            win_count[winner] += 1
            profile_win_count[profile][winner] += 1
            loss_tags = _tonesight_loss_tags(
                profile=profile,
                winner=winner,
                method_distances=robust_method_distances,
            )
            robustness_runs.append(
                {
                    "profile": profile,
                    "seed": seed,
                    "separation_ratios": robust_distances,
                    "distances_by_method": robust_method_distances,
                    "winner": winner,
                    "tonesight_loss_tags": loss_tags,
                }
            )
            for method, ratio in robust_distances.items():
                robustness_by_method[method].append(float(ratio))
                profile_method_ratios[profile][method].append(float(ratio))
                d12 = float(robust_method_distances[method]["d_c1_c2"])
                d13 = float(robust_method_distances[method]["d_c1_c3"])
                ratio_lt_1 = float(ratio) < 1.0
                true_gt_false = d13 > d12
                robustness_criteria[method]["separation_ratio_lt_1"].append(ratio_lt_1)
                robustness_criteria[method]["true_drift_gt_false_drift"].append(true_gt_false)
                robustness_criteria[method]["both_ratio_and_true_gt_false"].append(
                    ratio_lt_1 and true_gt_false
                )
                profile_criteria[profile][method]["separation_ratio_lt_1"].append(ratio_lt_1)
                profile_criteria[profile][method]["true_drift_gt_false_drift"].append(true_gt_false)
                profile_criteria[profile][method]["both_ratio_and_true_gt_false"].append(
                    ratio_lt_1 and true_gt_false
                )
            if winner != "tonesight":
                for tag in loss_tags:
                    tonesight_loss_tag_counts[tag] = int(tonesight_loss_tag_counts.get(tag, 0) + 1)
                    profile_tags = profile_tonesight_loss_tags[profile]
                    profile_tags[tag] = int(profile_tags.get(tag, 0) + 1)

    robustness_summary = {
        "seed_count": len(robustness_seeds),
        "profiles": list(robustness_profiles),
        "wins_by_method": {key: int(win_count[key]) for key in sorted(win_count)},
        "ratio_stats_by_method": {
            method: {
                "mean": _mean(values),
                "std": _std(values),
                "min": min(values) if values else 0.0,
                "max": max(values) if values else 0.0,
                "p10": _quantile(values, 0.10),
                "p50": _quantile(values, 0.50),
                "p90": _quantile(values, 0.90),
            }
            for method, values in sorted(robustness_by_method.items())
        },
        "absolute_criteria_pass_rate": {
            method: {
                "separation_ratio_lt_1": _rate(criteria["separation_ratio_lt_1"]),
                "true_drift_gt_false_drift": _rate(criteria["true_drift_gt_false_drift"]),
                "both_ratio_and_true_gt_false": _rate(criteria["both_ratio_and_true_gt_false"]),
                "monotonic_drift_sweep_primary": bool(
                    absolute_criteria.get(method, {}).get("monotonic_drift_sweep", False)
                ),
            }
            for method, criteria in sorted(robustness_criteria.items())
        },
        "tonesight_loss_tag_counts": dict(sorted(tonesight_loss_tag_counts.items())),
        "by_profile": {
            profile: {
                "wins_by_method": {
                    key: int(profile_win_count[profile][key])
                    for key in sorted(profile_win_count[profile])
                },
                "ratio_stats_by_method": {
                    method: {
                        "mean": _mean(values),
                        "std": _std(values),
                        "min": min(values) if values else 0.0,
                        "max": max(values) if values else 0.0,
                        "p10": _quantile(values, 0.10),
                        "p50": _quantile(values, 0.50),
                        "p90": _quantile(values, 0.90),
                    }
                    for method, values in sorted(profile_method_ratios[profile].items())
                },
                "absolute_criteria_pass_rate": {
                    method: {
                        "separation_ratio_lt_1": _rate(
                            profile_criteria[profile][method]["separation_ratio_lt_1"]
                        ),
                        "true_drift_gt_false_drift": _rate(
                            profile_criteria[profile][method]["true_drift_gt_false_drift"]
                        ),
                        "both_ratio_and_true_gt_false": _rate(
                            profile_criteria[profile][method]["both_ratio_and_true_gt_false"]
                        ),
                        "monotonic_drift_sweep_primary": bool(
                            absolute_criteria.get(method, {}).get("monotonic_drift_sweep", False)
                        ),
                    }
                    for method in sorted(profile_criteria[profile])
                },
                "tonesight_loss_tag_counts": dict(
                    sorted(profile_tonesight_loss_tags[profile].items())
                ),
            }
            for profile in sorted(profile_method_ratios)
        },
    }

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
            "sample_multiplier": sample_multiplier,
            "primary_drift_strength": primary_strength,
            "drift_sweep_strengths": sweep_strengths,
            "quantile_bins": 8,
            "equal_width_bins": 8,
            "raw_hist_bins": 16,
            "upstream_b": {"v_scale": 1.03, "v_bias": 0.02, "a_scale": 0.98, "a_bias": -0.01, "d_scale": 1.01},
            "drift_injection": {
                "global_v_bias_per_strength": -0.30,
                "global_a_bias_per_strength": 0.30,
                "regime_every_n": 5,
                "regime_v_bias_per_strength": -0.25,
                "regime_a_bias_per_strength": 0.25,
                "spike_every_n": 20,
                "spike_a_bias_per_strength": 0.40,
                "spike_d_bias_per_strength": 0.15,
            },
            "methods": ["tonesight", "equal_width", "quantile", "raw_jsd_hist16"],
            "tonesight_distance_metric": {
                "type": "weighted_topology_transition",
                "weights": {"topology_pair": 0.7, "transition_jsd": 0.2, "occupancy_jsd": 0.1},
            },
            "robustness": {
                "available_profiles": list(_AVAILABLE_ROBUSTNESS_PROFILES),
                "profiles": list(robustness_profiles),
                "seeds": list(robustness_seeds),
                "notes": "synthetic benchmark robustness sweep over deterministic profile/seed variants",
            },
        },
        "distances": distances,
        "separation_ratios": separation_ratios,
        "drift_sweep": {
            "rows_by_method": sweep_rows,
            "monotonic_non_decreasing": monotonic_non_decreasing,
        },
        "robustness_sweep": {
            "runs": sorted(robustness_runs, key=lambda row: (str(row["profile"]), int(row["seed"]))),
            "summary": robustness_summary,
        },
        "summary": {
            "best_method_by_lowest_separation_ratio": ranking[0][0],
            "method_ranking": [{"method": key, "separation_ratio": value} for key, value in ranking],
            "absolute_criteria": absolute_criteria,
        },
    }

    out_dir = Path(out_root) / "benchmarks" / "killer_stability"
    out_dir.mkdir(parents=True, exist_ok=True)
    evidence_path = out_dir / "evidence.json"
    robustness_summary_path = out_dir / "robustness_summary.json"
    robustness_report_path = out_dir / "robustness_report.html"
    evidence_path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    robustness_summary_path.write_text(
        json.dumps(
            {
                "spec_version": evidence["spec_version"],
                "benchmark_schema_version": evidence["benchmark_schema_version"],
                "dataset_hash": evidence["dataset_hash"],
                "code_revision": evidence["code_revision"],
                "robustness_sweep": evidence["robustness_sweep"],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    robustness_report_path.write_text(_render_robustness_report_html(evidence), encoding="utf-8")

    return {
        "spec_version": "1.0",
        "suite": "killer_stability",
        "out_root": out_root,
        "goldset_path": goldset_path,
        "sample_count": len(base_vads),
        "artifacts": {
            "evidence": str(evidence_path),
            "report": str(evidence_path),
            "robustness_summary": str(robustness_summary_path),
            "robustness_report_html": str(robustness_report_path),
        },
        "results": {"killer_stability": evidence},
    }
