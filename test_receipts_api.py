from tonesight_ns8 import compute_A, resolve_to_seed, tonesight_from_label, tonesight_from_vad


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
