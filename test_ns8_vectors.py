import json
from pathlib import Path

import pytest

from ns8_ref import InvalidInput, ns8_A, ns8_route


VECTOR_PATH = Path("vectors/ns8_test_vectors.json")
if not VECTOR_PATH.exists():
    VECTOR_PATH = Path(__file__).with_name("ns8_test_vectors.json")


def load_vectors():
    with VECTOR_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


@pytest.mark.parametrize("vector", load_vectors(), ids=lambda v: v["id"])
def test_ns8_vectors(vector):
    if vector.get("expected_error"):
        with pytest.raises(InvalidInput):
            ns8_A(vector["family"], vector["r"], vector["c"], vector["k"], vector["N"])
        return

    actual = ns8_A(vector["family"], vector["r"], vector["c"], vector["k"], vector["N"])
    assert actual == vector["expected_A"]

    route = ns8_route(vector["family"], vector["r"], vector["c"], vector["k"], vector["N"])
    assert route.seed_family == vector["expected_seed_family"]
    assert route.r_prime == vector["expected_r_prime"]
    assert route.c_prime == vector["expected_c_prime"]
