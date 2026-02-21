"""Deterministic segment -> speaker/session analytics."""

from __future__ import annotations

from collections import defaultdict

from .schema import SegmentRecord, SessionSummary, SpeakerSummary

_METRIC_PRECISION = 6


def _validate_bin(name: str, value: int) -> None:
    if not isinstance(value, int):
        raise ValueError(f"{name} must be int")
    if value < 1 or value > 8:
        raise ValueError(f"{name} must be in 1..8")


def _validate_segment(segment: SegmentRecord) -> None:
    if segment.end_sec < segment.start_sec:
        raise ValueError("end_sec must be >= start_sec")
    _validate_bin("V", segment.V)
    _validate_bin("A", segment.A)
    _validate_bin("D", segment.D)
    if segment.ns8_A is not None:
        _validate_bin("ns8_A", segment.ns8_A)


def _stable_sorted(segments: list[SegmentRecord]) -> list[SegmentRecord]:
    return sorted(segments, key=lambda s: (s.start_sec, s.end_sec, s.segment_id, s.speaker_id))


def _empty_hist() -> list[int]:
    return [0] * 8


def _make_distributions(segments: list[SegmentRecord]) -> dict[str, list[int]]:
    hist_v = _empty_hist()
    hist_a = _empty_hist()
    hist_d = _empty_hist()
    hist_anchor = _empty_hist()
    for s in segments:
        hist_v[s.V - 1] += 1
        hist_a[s.A - 1] += 1
        hist_d[s.D - 1] += 1
        if s.ns8_A is not None:
            hist_anchor[s.ns8_A - 1] += 1
    return {"V": hist_v, "A": hist_a, "D": hist_d, "anchor_A": hist_anchor}


def _centroid(segments: list[SegmentRecord]) -> tuple[float, float, float]:
    n = len(segments)
    if n == 0:
        return (0.0, 0.0, 0.0)
    return (
        sum(s.V for s in segments) / n,
        sum(s.A for s in segments) / n,
        sum(s.D for s in segments) / n,
    )


def _round_metric(value: float) -> float:
    return round(float(value), _METRIC_PRECISION)


def _arousal_volatility(segments: list[SegmentRecord]) -> float:
    if len(segments) < 2:
        return 0.0
    ordered = _stable_sorted(segments)
    deltas = [abs(ordered[i].A - ordered[i - 1].A) for i in range(1, len(ordered))]
    return _round_metric(sum(deltas) / len(deltas))


def _arousal_momentum(segments: list[SegmentRecord]) -> dict[str, float]:
    ordered = _stable_sorted(segments)
    if len(ordered) < 2:
        return {
            "mean_momentum": 0.0,
            "positive_momentum_ratio": 0.0,
            "count_transitions": 0.0,
        }
    deltas = [float(ordered[i].A - ordered[i - 1].A) for i in range(1, len(ordered))]
    positives = sum(1 for delta in deltas if delta > 0)
    return {
        "mean_momentum": _round_metric(sum(deltas) / len(deltas)),
        "positive_momentum_ratio": _round_metric(positives / len(deltas)),
        "count_transitions": float(len(deltas)),
    }


def _tone_stability_index(segments: list[SegmentRecord]) -> float:
    # Bounded deterministic index derived from normalized arousal volatility.
    # Max per-step arousal delta in NS8 bins is 7 (from 1..8 range).
    volatility = _arousal_volatility(segments)
    normalized = volatility / 7.0
    bounded = max(0.0, min(1.0, 1.0 - normalized))
    return _round_metric(bounded)


def _window_k(count: int, requested_k: int) -> int:
    if count <= 0:
        return 0
    return max(1, min(int(requested_k), count))


def _window_mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def _session_drift(segments: list[SegmentRecord], drift_window_k: int) -> tuple[int, float, float, float, float | None]:
    ordered = _stable_sorted(segments)
    if not ordered:
        return (0, 0.0, 0.0, 0.0, None)

    k = _window_k(len(ordered), drift_window_k)
    start = ordered[:k]
    end = ordered[-k:]

    start_v = _window_mean([float(s.V) for s in start])
    start_a = _window_mean([float(s.A) for s in start])
    start_d = _window_mean([float(s.D) for s in start])
    end_v = _window_mean([float(s.V) for s in end])
    end_a = _window_mean([float(s.A) for s in end])
    end_d = _window_mean([float(s.D) for s in end])

    start_anchor = [float(s.ns8_A) for s in start if s.ns8_A is not None]
    end_anchor = [float(s.ns8_A) for s in end if s.ns8_A is not None]
    if start_anchor and end_anchor:
        drift_anchor = _round_metric(_window_mean(end_anchor) - _window_mean(start_anchor))
    else:
        drift_anchor = None

    return (
        k,
        _round_metric(end_v - start_v),
        _round_metric(end_a - start_a),
        _round_metric(end_d - start_d),
        drift_anchor,
    )


def summarize_speaker(segments: list[SegmentRecord]) -> dict[str, SpeakerSummary]:
    """Summarize segment analytics by speaker_id with deterministic ordering."""
    for segment in segments:
        _validate_segment(segment)

    grouped: dict[str, list[SegmentRecord]] = defaultdict(list)
    for segment in segments:
        grouped[segment.speaker_id].append(segment)

    result: dict[str, SpeakerSummary] = {}
    for speaker_id in sorted(grouped.keys()):
        speaker_segments = _stable_sorted(grouped[speaker_id])
        summary = SpeakerSummary(
            speaker_id=speaker_id,
            count_segments=len(speaker_segments),
            vad_centroid=_centroid(speaker_segments),
            volatility=_arousal_volatility(speaker_segments),
            arousal_momentum=_arousal_momentum(speaker_segments),
            tone_stability_index=_tone_stability_index(speaker_segments),
            distributions=_make_distributions(speaker_segments),
        )
        result[speaker_id] = summary
    return result


def summarize_session(
    session_id: str,
    segments: list[SegmentRecord],
    arousal_spike_threshold: int = 7,
    drift_window_k: int = 2,
) -> SessionSummary:
    """Summarize session-level analytics over all segments."""
    _validate_bin("arousal_spike_threshold", arousal_spike_threshold)
    for segment in segments:
        _validate_segment(segment)
    if drift_window_k < 1:
        raise ValueError("drift_window_k must be >= 1")

    ordered = _stable_sorted(segments)
    resolved_k, drift_v, drift_a, drift_d, drift_anchor = _session_drift(ordered, drift_window_k)
    spike_segments = [s.segment_id for s in ordered if s.A >= arousal_spike_threshold]
    count = len(ordered)
    spike_count = len(spike_segments)
    spike_rate = (spike_count / count) if count > 0 else 0.0
    spike_density = spike_rate

    return SessionSummary(
        session_id=session_id,
        count_segments=count,
        vad_centroid=_centroid(ordered),
        distributions=_make_distributions(ordered),
        drift_window_k=resolved_k,
        drift_v=drift_v,
        drift_a=drift_a,
        drift_d=drift_d,
        drift_anchor=drift_anchor,
        spike_count=spike_count,
        spike_rate=spike_rate,
        spike_density=spike_density,
        arousal_momentum=_arousal_momentum(ordered),
        tone_stability_index=_tone_stability_index(ordered),
        spike_segments=spike_segments,
    )
