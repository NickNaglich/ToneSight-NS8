from __future__ import annotations

from uuid import uuid4

import pytest

from tonesight_ns8 import (
    compute_A,
    get_default_mapping_id,
    get_mapping,
    list_mappings,
    register_mapping,
    resolve_to_seed,
    tonesight_receipt_from_vad_context,
)
from tonesight_ns8.mapping_examples import TLFConstantMappingAdapter


def test_default_mapping_is_ns8_and_parity_holds():
    assert get_default_mapping_id() == "ns8"
    assert "ns8" in list_mappings()

    ns8 = get_mapping("ns8")
    seed_family, r_prime, c_prime, k = ns8.resolve_to_seed("TRF", 6, 4, 3, 8)
    anchor = ns8.compute_A("TRF", 6, 4, 3, 8)

    assert (seed_family, r_prime, c_prime, k) == resolve_to_seed("TRF", 6, 4, 3, 8)
    assert anchor == compute_A("TRF", 6, 4, 3, 8)


def test_register_custom_mapping_and_use_in_receipt():
    mapping_id = f"tlf_constant_{uuid4().hex}"
    register_mapping(mapping_id, TLFConstantMappingAdapter())

    receipt = tonesight_receipt_from_vad_context(7, 3, 3, "TLF", 6, 4, 3, mapping_id=mapping_id)
    assert receipt["route"] == {"seed_family": "TLF", "r_prime": 6, "c_prime": 4}
    assert receipt["output"]["A"] == 1


def test_register_rejects_duplicate_mapping_id():
    mapping_id = f"dup_{uuid4().hex}"
    register_mapping(mapping_id, TLFConstantMappingAdapter())
    with pytest.raises(ValueError):
        register_mapping(mapping_id, TLFConstantMappingAdapter())
