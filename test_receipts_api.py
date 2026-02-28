import pytest

from tonesight_ns8 import (
    compute_A,
    resolve_to_seed,
    tonesight_from_label,
    tonesight_from_llm_labels,
    tonesight_from_vad,
    tonesight_from_vad_batch,
)


def test_compute_and_route_public_api():
    seed_family, r_prime, c_prime, k = resolve_to_seed("TRF", 6, 4, 3)
    assert seed_family in {"TLF", "TRB"}
    assert (r_prime, c_prime, k) == (6, 5, 3)
    assert compute_A("TRF", 6, 4, 3) == 2


def test_receipt_from_vad_shape_and_determinism():
    rec1 = tonesight_from_vad(7, 3, 3, "TRF", 6, 4, 3)
    rec2 = tonesight_from_vad(7, 3, 3, "TRF", 6, 4, 3)
    assert rec1 == rec2
    assert set(rec1.keys()) == {"spec_version", "input", "route", "output"}
    assert set(rec1["input"].keys()) == {"family", "r", "c", "k", "vad"}
    assert set(rec1["route"].keys()) == {"seed_family", "r_prime", "c_prime"}
    assert set(rec1["output"].keys()) == {"A"}
    assert rec1["spec_version"] == "1.0"


def test_receipt_from_label():
    rec = tonesight_from_label(
        label="empathetic",
        family="TRF",
        r=6,
        c=4,
        k=3,
        taxonomy_path="taxonomy/tone_taxonomy.v1.json",
    )
    assert rec["input"]["label"] == "empathetic"
    assert rec["input"]["vad"] == {"V": 7, "A": 3, "D": 3}


def test_receipt_from_vad_batch_shape_order_and_determinism():
    rows = [
        {"V": 7, "A": 3, "D": 3},
        {"V": 2, "A": 7, "D": 4},
        {"V": 5, "A": 5, "D": 5},
    ]
    rec1 = tonesight_from_vad_batch(rows, "TRF", 6, 4, 3)
    rec2 = tonesight_from_vad_batch(rows, "TRF", 6, 4, 3)
    assert rec1 == rec2
    assert len(rec1) == 3
    assert rec1[0]["input"]["vad"] == rows[0]
    assert rec1[1]["input"]["vad"] == rows[1]
    assert rec1[2]["input"]["vad"] == rows[2]


def test_receipt_from_llm_labels_shape_order_and_determinism():
    labels = ["empathetic", "reassuring", "neutral"]
    rec1 = tonesight_from_llm_labels(labels, "TRF", 6, 4, 3, taxonomy_path="taxonomy/tone_taxonomy.v1.json")
    rec2 = tonesight_from_llm_labels(labels, "TRF", 6, 4, 3, taxonomy_path="taxonomy/tone_taxonomy.v1.json")
    assert rec1 == rec2
    assert len(rec1) == 3
    assert [r["input"]["label"] for r in rec1] == labels


def test_batch_adapter_type_validation():
    with pytest.raises(ValueError, match="rows must be a list"):
        tonesight_from_vad_batch("bad", "TRF", 6, 4, 3)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="rows\\[0\\] must define exactly V,A,D"):
        tonesight_from_vad_batch([{"V": 7, "A": 3}], "TRF", 6, 4, 3)
    with pytest.raises(ValueError, match="rows\\[0\\] D must be an integer in 1..8"):
        tonesight_from_vad_batch([{"V": 7, "A": 3, "D": "x"}], "TRF", 6, 4, 3)  # type: ignore[dict-item]
    with pytest.raises(ValueError, match="labels must be a list"):
        tonesight_from_llm_labels("bad", "TRF", 6, 4, 3, taxonomy_path="taxonomy/tone_taxonomy.v1.json")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="labels\\[0\\] must be a non-empty string"):
        tonesight_from_llm_labels([""], "TRF", 6, 4, 3, taxonomy_path="taxonomy/tone_taxonomy.v1.json")


def test_vad_adapter_strict_domain_validation():
    with pytest.raises(ValueError, match="input V must be an integer in 1..8"):
        tonesight_from_vad(True, 3, 3, "TRF", 6, 4, 3)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="input A must be in 1..8"):
        tonesight_from_vad(7, 9, 3, "TRF", 6, 4, 3)
    with pytest.raises(ValueError, match="rows\\[0\\] V must be an integer in 1..8"):
        tonesight_from_vad_batch([{"V": True, "A": 3, "D": 3}], "TRF", 6, 4, 3)  # type: ignore[dict-item]
    with pytest.raises(ValueError, match="rows\\[0\\] A must be in 1..8"):
        tonesight_from_vad_batch([{"V": 7, "A": 0, "D": 3}], "TRF", 6, 4, 3)
