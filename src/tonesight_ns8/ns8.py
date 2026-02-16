"""Package-level NS8 wrappers over the reference oracle."""

from __future__ import annotations

from pathlib import Path
import sys

from .errors import InvalidInput

# Keep root oracle authoritative until packaged parity is complete.
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ns8_ref import (  # noqa: E402
    InvalidInput as OracleInvalidInput,
    ns8_A,
    ns8_route,
)


def validate_inputs(family: str, r: int, c: int, k: int, N: int = 8) -> None:
    """Validate strict NS8 inputs using oracle semantics."""
    try:
        ns8_route(family, r, c, k, N)
    except OracleInvalidInput as exc:
        raise InvalidInput(str(exc)) from exc


def resolve_to_seed(family: str, r: int, c: int, k: int, N: int = 8) -> tuple[str, int, int, int]:
    """Resolve to canonical seed route: (seed_family, r_prime, c_prime, k)."""
    try:
        route = ns8_route(family, r, c, k, N)
    except OracleInvalidInput as exc:
        raise InvalidInput(str(exc)) from exc
    return (route.seed_family, route.r_prime, route.c_prime, k)


def compute_A(family: str, r: int, c: int, k: int, N: int = 8) -> int:
    """Compute deterministic anchor A in 1..8."""
    try:
        return ns8_A(family, r, c, k, N)
    except OracleInvalidInput as exc:
        raise InvalidInput(str(exc)) from exc

