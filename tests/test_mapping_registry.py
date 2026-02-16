from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

import pytest

from tonesight_ns8 import (
    compute_A,
    get_default_mapping_id,
    get_mapping,
    list_mappings,
    register_mapping,
    resolve_to_seed,
    tonesight_from_vad,
)


@dataclass(frozen=True)
class DummyAdapter:
    name: str = "dummy"
    spec_version: str = "1.0"
    n: int = 8
    families: tuple[str, ...] = ("TLF",)

    def validate_inputs(self, family: str, r: int, c: int, k: int, N: int = 8) -> None:
        if family not in self.families:
            raise ValueError("unsupported family")

    def resolve_to_seed(self, family: str, r: int, c: int, k: int, N: int = 8) -> tuple[str, int, int, int]:
        self.validate_inputs(family, r, c, k, N)
        return (family, r, c, k)

    def compute_A(self, family: str, r: int, c: int, k: int, N: int = 8) -> int:
        self.validate_inputs(family, r, c, k, N)
        return 8


def test_default_mapping_is_ns8_and_parity_holds():
    assert get_default_mapping_id() == "ns8"
    assert "ns8" in list_mappings()

    ns8 = get_mapping("ns8")
    seed_family, r_prime, c_prime, k = ns8.resolve_to_seed("TRF", 6, 4, 3, 8)
    anchor = ns8.compute_A("TRF", 6, 4, 3, 8)

    assert (seed_family, r_prime, c_prime, k) == resolve_to_seed("TRF", 6, 4, 3, 8)
    assert anchor == compute_A("TRF", 6, 4, 3, 8)


def test_register_custom_mapping_and_use_in_receipt():
    mapping_id = f"dummy_{uuid4().hex}"
    register_mapping(mapping_id, DummyAdapter())

    receipt = tonesight_from_vad(7, 3, 3, "TLF", 6, 4, 3, mapping_id=mapping_id)
    assert receipt["route"] == {"seed_family": "TLF", "r_prime": 6, "c_prime": 4}
    assert receipt["output"]["A"] == 8


def test_register_rejects_duplicate_mapping_id():
    mapping_id = f"dup_{uuid4().hex}"
    register_mapping(mapping_id, DummyAdapter())
    with pytest.raises(ValueError):
        register_mapping(mapping_id, DummyAdapter())
