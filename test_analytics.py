from tonesight_ns8.analytics import summarize_session, summarize_speaker
from tonesight_ns8.schema import SegmentRecord


def _fixture_segments():
    return [
        SegmentRecord("seg_01", "spk_a", 0.0, 1.0, 6, 3, 4, ns8_A=2),
        SegmentRecord("seg_02", "spk_b", 1.1, 2.0, 4, 7, 5, ns8_A=6),
        SegmentRecord("seg_03", "spk_a", 2.1, 3.0, 7, 2, 3, ns8_A=1),
        SegmentRecord("seg_04", "spk_b", 3.1, 4.0, 5, 6, 5, ns8_A=4),
        SegmentRecord("seg_05", "spk_a", 4.1, 5.0, 6, 4, 4, ns8_A=3),
        SegmentRecord("seg_06", "spk_b", 5.1, 6.0, 3, 8, 6, ns8_A=8),
    ]


def test_summarize_speaker_centroid_volatility_and_histograms():
    summaries = summarize_speaker(_fixture_segments())
    a = summaries["spk_a"]
    b = summaries["spk_b"]

    assert a.count_segments == 3
    assert b.count_segments == 3

    # spk_a VAD means: V=(6+7+6)/3, A=(3+2+4)/3, D=(4+3+4)/3
    assert a.vad_centroid == (19 / 3, 3.0, 11 / 3)
    # arousal volatility by time: |2-3| and |4-2| -> (1 + 2)/2 = 1.5
    assert a.volatility == 1.5
    assert a.arousal_momentum == {"mean_momentum": 0.5, "positive_momentum_ratio": 0.5, "count_transitions": 2.0}
    assert a.tone_stability_index == 0.785714

    # spk_b VAD means: V=(4+5+3)/3, A=(7+6+8)/3, D=(5+5+6)/3
    assert b.vad_centroid == (4.0, 7.0, 16 / 3)
    # arousal volatility: |6-7| and |8-6| -> (1 + 2)/2 = 1.5
    assert b.volatility == 1.5
    assert b.arousal_momentum == {"mean_momentum": 0.5, "positive_momentum_ratio": 0.5, "count_transitions": 2.0}
    assert b.tone_stability_index == 0.785714

    for summary in (a, b):
        assert len(summary.distributions["V"]) == 8
        assert len(summary.distributions["A"]) == 8
        assert len(summary.distributions["D"]) == 8
        assert len(summary.distributions["anchor_A"]) == 8
        assert sum(summary.distributions["V"]) == 3
        assert sum(summary.distributions["A"]) == 3
        assert sum(summary.distributions["D"]) == 3


def test_summarize_session_spikes_and_totals():
    session = summarize_session("session_001", _fixture_segments(), arousal_spike_threshold=7)
    assert session.session_id == "session_001"
    assert session.count_segments == 6
    assert session.vad_centroid == (31 / 6, 5.0, 27 / 6)
    assert session.spike_count == 2
    assert session.spike_rate == 2 / 6
    assert session.spike_density == session.spike_rate
    assert session.drift_window_k == 2
    assert session.drift_v == -0.5
    assert session.drift_a == 1.0
    assert session.drift_d == 0.5
    assert session.drift_anchor == 1.5
    assert session.arousal_momentum == {"mean_momentum": 1.0, "positive_momentum_ratio": 0.6, "count_transitions": 5.0}
    assert session.tone_stability_index == 0.457143
    assert session.spike_segments == ["seg_02", "seg_06"]

    assert len(session.distributions["V"]) == 8
    assert len(session.distributions["A"]) == 8
    assert len(session.distributions["D"]) == 8
    assert len(session.distributions["anchor_A"]) == 8
    assert sum(session.distributions["V"]) == 6
    assert sum(session.distributions["A"]) == 6
    assert sum(session.distributions["D"]) == 6
    assert sum(session.distributions["anchor_A"]) == 6


def test_deterministic_results_under_input_shuffle():
    ordered = _fixture_segments()
    shuffled = [ordered[5], ordered[3], ordered[0], ordered[2], ordered[4], ordered[1]]

    session_a = summarize_session("session_001", ordered)
    session_b = summarize_session("session_001", shuffled)
    assert session_a == session_b

    speaker_a = summarize_speaker(ordered)
    speaker_b = summarize_speaker(shuffled)
    assert speaker_a == speaker_b


def test_derived_metrics_empty_and_single_segment_inputs():
    single = [SegmentRecord("seg_01", "spk_a", 0.0, 1.0, 5, 6, 4, ns8_A=3)]
    speaker = summarize_speaker(single)["spk_a"]
    session = summarize_session("session_single", single)
    assert speaker.arousal_momentum == {"mean_momentum": 0.0, "positive_momentum_ratio": 0.0, "count_transitions": 0.0}
    assert speaker.tone_stability_index == 1.0
    assert session.arousal_momentum == {"mean_momentum": 0.0, "positive_momentum_ratio": 0.0, "count_transitions": 0.0}
    assert session.tone_stability_index == 1.0
    assert session.drift_window_k == 1
    assert session.drift_v == 0.0
    assert session.drift_a == 0.0
    assert session.drift_d == 0.0
    assert session.drift_anchor == 0.0
    assert session.spike_rate == 0.0
    assert session.spike_density == 0.0

    empty_session = summarize_session("session_empty", [])
    assert empty_session.arousal_momentum == {"mean_momentum": 0.0, "positive_momentum_ratio": 0.0, "count_transitions": 0.0}
    assert empty_session.tone_stability_index == 1.0
    assert empty_session.drift_window_k == 0
    assert empty_session.drift_v == 0.0
    assert empty_session.drift_a == 0.0
    assert empty_session.drift_d == 0.0
    assert empty_session.drift_anchor is None
    assert empty_session.spike_rate == 0.0
    assert empty_session.spike_density == 0.0


def test_derived_metrics_stable_float_precision_rounding():
    # A deltas: +1, +1, +2 -> mean=1.333333..., positive ratio=1.0
    rows = [
        SegmentRecord("s1", "spk_x", 0.0, 1.0, 4, 2, 4, ns8_A=1),
        SegmentRecord("s2", "spk_x", 1.0, 2.0, 4, 3, 4, ns8_A=1),
        SegmentRecord("s3", "spk_x", 2.0, 3.0, 4, 4, 4, ns8_A=1),
        SegmentRecord("s4", "spk_x", 3.0, 4.0, 4, 6, 4, ns8_A=1),
    ]
    speaker = summarize_speaker(rows)["spk_x"]
    assert speaker.arousal_momentum["mean_momentum"] == 1.333333
    assert speaker.arousal_momentum["positive_momentum_ratio"] == 1.0
    assert speaker.tone_stability_index == 0.809524


def test_session_drift_window_policy_and_unordered_determinism():
    ordered = _fixture_segments()
    shuffled = [ordered[4], ordered[2], ordered[0], ordered[5], ordered[1], ordered[3]]

    session_k1 = summarize_session("session_001", ordered, drift_window_k=1)
    assert session_k1.drift_window_k == 1
    assert session_k1.drift_v == -3.0
    assert session_k1.drift_a == 5.0
    assert session_k1.drift_d == 2.0
    assert session_k1.drift_anchor == 6.0

    session_k9 = summarize_session("session_001", ordered, drift_window_k=9)
    assert session_k9.drift_window_k == 6
    assert session_k9.drift_v == 0.0
    assert session_k9.drift_a == 0.0
    assert session_k9.drift_d == 0.0
    assert session_k9.drift_anchor == 0.0

    session_ordered = summarize_session("session_001", ordered, drift_window_k=2)
    session_shuffled = summarize_session("session_001", shuffled, drift_window_k=2)
    assert session_ordered == session_shuffled
