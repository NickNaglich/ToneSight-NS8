from dataclasses import asdict

from tonesight_ns8.analytics import summarize_session, summarize_speaker
from tonesight_ns8.schema import SegmentRecord


def _segments():
    return [
        SegmentRecord("seg_01", "spk_a", 0.0, 1.0, 6, 3, 4, ns8_A=2),
        SegmentRecord("seg_02", "spk_b", 1.0, 2.0, 4, 7, 5, ns8_A=6),
        SegmentRecord("seg_03", "spk_a", 2.0, 3.0, 7, 2, 3, ns8_A=1),
        SegmentRecord("seg_04", "spk_b", 3.0, 4.0, 5, 6, 5, ns8_A=4),
        SegmentRecord("seg_05", "spk_a", 4.0, 5.0, 6, 4, 4, ns8_A=3),
        SegmentRecord("seg_06", "spk_b", 5.0, 6.0, 3, 8, 6, ns8_A=8),
    ]


def test_speaker_derived_metrics_contract_shape_and_types():
    speakers = summarize_speaker(_segments())
    payload = asdict(speakers["spk_a"])

    assert "arousal_momentum" in payload
    assert "tone_stability_index" in payload
    momentum = payload["arousal_momentum"]
    assert set(momentum) == {"mean_momentum", "positive_momentum_ratio", "count_transitions"}
    assert isinstance(momentum["mean_momentum"], float)
    assert isinstance(momentum["positive_momentum_ratio"], float)
    assert isinstance(momentum["count_transitions"], float)
    assert isinstance(payload["tone_stability_index"], float)
    assert 0.0 <= payload["tone_stability_index"] <= 1.0


def test_session_derived_metrics_contract_shape_and_types():
    session = asdict(summarize_session("session_001", _segments()))

    for field in (
        "drift_window_k",
        "drift_v",
        "drift_a",
        "drift_d",
        "spike_density",
        "arousal_momentum",
        "tone_stability_index",
        "arousal_coupling",
    ):
        assert field in session

    assert isinstance(session["drift_window_k"], int)
    assert isinstance(session["drift_v"], float)
    assert isinstance(session["drift_a"], float)
    assert isinstance(session["drift_d"], float)
    assert session["drift_anchor"] is None or isinstance(session["drift_anchor"], float)
    assert isinstance(session["spike_density"], float)
    assert isinstance(session["arousal_momentum"], dict)
    assert isinstance(session["tone_stability_index"], float)
    assert 0.0 <= session["tone_stability_index"] <= 1.0

    coupling = session["arousal_coupling"]
    assert set(coupling) == {"coupling_score", "count_pairs", "alignment"}
    assert coupling["coupling_score"] is None or isinstance(coupling["coupling_score"], float)
    assert isinstance(coupling["count_pairs"], float)
    assert isinstance(coupling["alignment"], dict)
    assert set(coupling["alignment"]) == {
        "policy",
        "speaker_count",
        "speaker_pair_count",
        "pair_details",
        "insufficient_data",
    }
    assert coupling["alignment"]["policy"] == "speaker_pair_index_alignment"
    assert isinstance(coupling["alignment"]["pair_details"], list)
    for item in coupling["alignment"]["pair_details"]:
        assert set(item) == {"speaker_a", "speaker_b", "aligned_count", "coupling_score"}
