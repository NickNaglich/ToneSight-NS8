from __future__ import annotations

from tonesight_ns8.mapping import NS8MappingAdapter
from tonesight_ns8.mapping_examples import TLFConstantMappingAdapter

from .mapping_conformance import assert_mapping_adapter_conformance


def test_ns8_adapter_passes_conformance_harness():
    assert_mapping_adapter_conformance(
        NS8MappingAdapter(),
        valid_cases=[
            ("TLF", 1, 1, 1),
            ("TRF", 6, 4, 3),
            ("BRB", 8, 8, 2),
        ],
        invalid_cases=[
            ("BAD", 1, 1, 1),
            ("TLF", 0, 1, 1),
            ("TLF", 1, 9, 1),
        ],
    )


def test_example_adapter_passes_conformance_harness():
    assert_mapping_adapter_conformance(
        TLFConstantMappingAdapter(),
        valid_cases=[
            ("TLF", 1, 1, 1),
            ("TLF", 8, 8, 8),
        ],
        invalid_cases=[
            ("TRF", 1, 1, 1),
            ("TLF", 0, 1, 1),
            ("TLF", 1, 9, 1),
        ],
    )
