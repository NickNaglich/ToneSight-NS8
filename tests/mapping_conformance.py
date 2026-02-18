from __future__ import annotations

from collections.abc import Iterable

from tonesight_ns8.mapping import MappingAdapter


def assert_mapping_adapter_conformance(
    adapter: MappingAdapter,
    *,
    valid_cases: Iterable[tuple[str, int, int, int]],
    invalid_cases: Iterable[tuple[str, int, int, int]] = (),
) -> None:
    """Reusable deterministic conformance checks for mapping adapters."""
    for family, r, c, k in valid_cases:
        route_1 = adapter.resolve_to_seed(family, r, c, k, adapter.n)
        route_2 = adapter.resolve_to_seed(family, r, c, k, adapter.n)
        assert route_1 == route_2
        assert len(route_1) == 4
        assert isinstance(route_1[0], str)
        assert isinstance(route_1[1], int)
        assert isinstance(route_1[2], int)
        assert isinstance(route_1[3], int)
        assert 1 <= route_1[1] <= adapter.n
        assert 1 <= route_1[2] <= adapter.n

        anchor_1 = adapter.compute_A(family, r, c, k, adapter.n)
        anchor_2 = adapter.compute_A(family, r, c, k, adapter.n)
        assert anchor_1 == anchor_2
        assert isinstance(anchor_1, int)
        assert 1 <= anchor_1 <= adapter.n

    for family, r, c, k in invalid_cases:
        raised = False
        try:
            adapter.validate_inputs(family, r, c, k, adapter.n)
        except Exception:
            raised = True
        assert raised
