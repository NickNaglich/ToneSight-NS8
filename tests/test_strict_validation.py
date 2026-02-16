import pytest

from tonesight_ns8 import compute_A
from tonesight_ns8.errors import InvalidInput, InvalidTaxonomy
from tonesight_ns8.taxonomy import validate_taxonomy


@pytest.mark.parametrize(
    ("family", "r", "c", "k", "N"),
    [
        ("TLF", 1.0, 1, 1, 8),
        ("TLF", True, 1, 1, 8),
        ("TLF", 1, 1.0, 1, 8),
        ("TLF", 1, False, 1, 8),
        ("TLF", 1, 1, 1.0, 8),
        ("TLF", 1, 1, True, 8),
        ("TLF", 1, 1, 1, 8.0),
    ],
)
def test_compute_a_rejects_non_int_inputs(family, r, c, k, N):
    with pytest.raises(InvalidInput):
        compute_A(family, r, c, k, N)


def test_validate_taxonomy_rejects_non_snake_case_label():
    with pytest.raises(InvalidTaxonomy):
        validate_taxonomy(
            {
                "spec_version": "1.0",
                "N": 8,
                "vad_scale": "1..8",
                "tones": {"Bad-Label": {"V": 1, "A": 1, "D": 1}},
            }
        )
