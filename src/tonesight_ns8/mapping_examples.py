"""Example mapping adapters for registry/conformance demonstrations."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TLFConstantMappingAdapter:
    """Minimal deterministic example adapter.

    This adapter only supports the `TLF` family and always returns anchor `1`.
    It exists as a plugin example and conformance-harness fixture.
    """

    name: str = "tlf_constant"
    spec_version: str = "1.0"
    n: int = 8
    families: tuple[str, ...] = ("TLF",)

    def validate_inputs(self, family: str, r: int, c: int, k: int, N: int = 8) -> None:
        if family not in self.families:
            raise ValueError("unsupported family")
        if N != self.n:
            raise ValueError("unsupported N")
        for value_name, value in (("r", r), ("c", c), ("k", k)):
            if not isinstance(value, int) or isinstance(value, bool):
                raise ValueError(f"{value_name} must be int")
            if value < 1 or value > self.n:
                raise ValueError(f"{value_name} out of range")

    def resolve_to_seed(self, family: str, r: int, c: int, k: int, N: int = 8) -> tuple[str, int, int, int]:
        self.validate_inputs(family, r, c, k, N)
        return (family, r, c, k)

    def compute_A(self, family: str, r: int, c: int, k: int, N: int = 8) -> int:
        self.validate_inputs(family, r, c, k, N)
        return 1
