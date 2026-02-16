"""Deterministic segment -> speaker/session analytics."""

from __future__ import annotations

from collections import defaultdict

from .schema import SegmentRecord, SessionSummary, SpeakerSummary


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


def _arousal_volatility(segments: list[SegmentRecord]) -> float:
    if len(segments) < 2:
        return 0.0
    ordered = _stable_sorted(segments)
    deltas = [abs(ordered[i].A - ordered[i - 1].A) for i in range(1, len(ordered))]
    return sum(deltas) / len(deltas)


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
            distributions=_make_distributions(speaker_segments),
        )
        result[speaker_id] = summary
    return result


def summarize_session(
    session_id: str,
    segments: list[SegmentRecord],
    arousal_spike_threshold: int = 7,
) -> SessionSummary:
    """Summarize session-level analytics over all segments."""
    _validate_bin("arousal_spike_threshold", arousal_spike_threshold)
    for segment in segments:
        _validate_segment(segment)

    ordered = _stable_sorted(segments)
    spike_segments = [s.segment_id for s in ordered if s.A >= arousal_spike_threshold]
    count = len(ordered)
    spike_count = len(spike_segments)
    spike_rate = (spike_count / count) if count > 0 else 0.0

    return SessionSummary(
        session_id=session_id,
        count_segments=count,
        vad_centroid=_centroid(ordered),
        distributions=_make_distributions(ordered),
        spike_count=spike_count,
        spike_rate=spike_rate,
        spike_segments=spike_segments,
    )

