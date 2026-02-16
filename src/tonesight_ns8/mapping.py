"""Mapping adapter interface and deterministic registry."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .ns8 import compute_A, resolve_to_seed, validate_inputs


class MappingAdapter(Protocol):
    """Contract for deterministic mapping adapters."""

    name: str
    spec_version: str
    n: int
    families: tuple[str, ...]

    def validate_inputs(self, family: str, r: int, c: int, k: int, N: int = 8) -> None: ...

    def resolve_to_seed(self, family: str, r: int, c: int, k: int, N: int = 8) -> tuple[str, int, int, int]: ...

    def compute_A(self, family: str, r: int, c: int, k: int, N: int = 8) -> int: ...


@dataclass(frozen=True)
class NS8MappingAdapter:
    """Built-in deterministic NS8 mapping adapter."""

    name: str = "ns8"
    spec_version: str = "1.0"
    n: int = 8
    families: tuple[str, ...] = ("TLF", "TRF", "BLF", "BRF", "TRB", "TLB", "BLB", "BRB")

    def validate_inputs(self, family: str, r: int, c: int, k: int, N: int = 8) -> None:
        validate_inputs(family, r, c, k, N)

    def resolve_to_seed(self, family: str, r: int, c: int, k: int, N: int = 8) -> tuple[str, int, int, int]:
        return resolve_to_seed(family, r, c, k, N)

    def compute_A(self, family: str, r: int, c: int, k: int, N: int = 8) -> int:
        return compute_A(family, r, c, k, N)


class MappingRegistry:
    """In-memory registry for deterministic mapping adapters."""

    def __init__(self) -> None:
        self._adapters: dict[str, MappingAdapter] = {}
        self._default_id: str | None = None

    def register(self, mapping_id: str, adapter: MappingAdapter, *, set_default: bool = False) -> None:
        key = mapping_id.strip().lower()
        if not key:
            raise ValueError("mapping_id must be non-empty")
        if key in self._adapters:
            raise ValueError(f"mapping_id already registered: {mapping_id}")
        self._adapters[key] = adapter
        if set_default or self._default_id is None:
            self._default_id = key

    def get(self, mapping_id: str) -> MappingAdapter:
        key = mapping_id.strip().lower()
        if key not in self._adapters:
            raise ValueError(f"Unknown mapping_id: {mapping_id}")
        return self._adapters[key]

    def default(self) -> MappingAdapter:
        if self._default_id is None:
            raise ValueError("No default mapping registered")
        return self._adapters[self._default_id]

    def default_id(self) -> str:
        if self._default_id is None:
            raise ValueError("No default mapping registered")
        return self._default_id

    def ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._adapters.keys()))


_REGISTRY = MappingRegistry()
_REGISTRY.register("ns8", NS8MappingAdapter(), set_default=True)


def register_mapping(mapping_id: str, adapter: MappingAdapter, *, set_default: bool = False) -> None:
    """Register a deterministic mapping adapter."""
    _REGISTRY.register(mapping_id, adapter, set_default=set_default)


def get_mapping(mapping_id: str) -> MappingAdapter:
    """Resolve mapping adapter by id."""
    return _REGISTRY.get(mapping_id)


def get_default_mapping() -> MappingAdapter:
    """Return default deterministic mapping adapter."""
    return _REGISTRY.default()


def get_default_mapping_id() -> str:
    """Return default mapping id."""
    return _REGISTRY.default_id()


def list_mappings() -> tuple[str, ...]:
    """List registered mapping ids."""
    return _REGISTRY.ids()
