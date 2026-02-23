import pytest

from tonesight_ns8 import compute_A, resolve_to_seed
from tonesight_ns8.errors import InvalidInput

FAMILIES = ("TLF", "TRF", "BLF", "BRF", "TRB", "TLB", "BLB", "BRB")
DOMAIN_VALUES = range(1, 9)


def test_property_a_stays_in_domain_for_valid_inputs():
    for family in FAMILIES:
        for r in DOMAIN_VALUES:
            for c in DOMAIN_VALUES:
                for k in DOMAIN_VALUES:
                    a = compute_A(family, r, c, k, 8)
                    assert 1 <= a <= 8


def test_property_route_stays_in_seed_and_range_for_valid_inputs():
    for family in FAMILIES:
        for r in DOMAIN_VALUES:
            for c in DOMAIN_VALUES:
                for k in DOMAIN_VALUES:
                    seed_family, r_prime, c_prime, k_out = resolve_to_seed(family, r, c, k, 8)
                    assert seed_family in {"TLF", "TRB"}
                    assert 1 <= r_prime <= 8
                    assert 1 <= c_prime <= 8
                    assert k_out == k


@pytest.mark.parametrize(
    ("family", "r", "c", "k", "N"),
    [
        ("BAD", 1, 1, 1, 8),
        ("TLF", 0, 1, 1, 8),
        ("TLF", 9, 1, 1, 8),
        ("TLF", 1, 0, 1, 8),
        ("TLF", 1, 9, 1, 8),
        ("TLF", 1, 1, 0, 8),
        ("TLF", 1, 1, 9, 8),
        ("TLF", 1, 1, 1, 7),
        ("TLF", 1, 1, 1, 8.0),
        ("TLF", True, 1, 1, 8),
        ("TLF", 1, False, 1, 8),
        ("TLF", 1, 1, True, 8),
    ],
)
def test_property_invalid_inputs_are_rejected(family, r, c, k, N):
    with pytest.raises(InvalidInput):
        compute_A(family, r, c, k, N)
    with pytest.raises(InvalidInput):
        resolve_to_seed(family, r, c, k, N)
