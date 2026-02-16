"""High-level deterministic wrapper APIs and receipt builders."""

from __future__ import annotations

from dataclasses import asdict, replace

from .ns8 import compute_A, resolve_to_seed
from .schema import SegmentRecord, ToneReceipt
from .taxonomy import get_vad, load_taxonomy


SPEC_VERSION = "1.0"


def _build_receipt(
    family: str,
    r: int,
    c: int,
    k: int,
    *,
    label: str | None = None,
    vad: tuple[int, int, int] | None = None,
) -> dict:
    seed_family, r_prime, c_prime, _ = resolve_to_seed(family, r, c, k, 8)
    anchor = compute_A(family, r, c, k, 8)

    input_obj = {"family": family, "r": r, "c": c, "k": k}
    if label is not None:
        input_obj["label"] = label
    if vad is not None:
        input_obj["vad"] = {"V": vad[0], "A": vad[1], "D": vad[2]}

    receipt = ToneReceipt(
        spec_version=SPEC_VERSION,
        input=input_obj,
        route={"seed_family": seed_family, "r_prime": r_prime, "c_prime": c_prime},
        output={"A": anchor},
    )
    return asdict(receipt)


def tonesight_from_label(
    label: str,
    family: str,
    r: int,
    c: int,
    k: int,
    taxonomy_path: str,
) -> dict:
    """Resolve tone label to VAD and return deterministic receipt."""
    taxonomy = load_taxonomy(taxonomy_path)
    vad = get_vad(label, taxonomy)
    return _build_receipt(family, r, c, k, label=label, vad=vad)


def tonesight_from_vad(
    V: int,
    A: int,
    D: int,
    family: str,
    r: int,
    c: int,
    k: int,
) -> dict:
    """Use explicit VAD and return deterministic receipt."""
    return _build_receipt(family, r, c, k, vad=(V, A, D))


def tonesight_receipt_from_segment(
    segment: SegmentRecord,
    family: str,
    r: int,
    c: int,
    k: int,
) -> dict:
    """Build receipt for a segment using segment VAD bins."""
    return _build_receipt(
        family,
        r,
        c,
        k,
        label=segment.tone_label,
        vad=(segment.V, segment.A, segment.D),
    )


def attach_tonesight_to_segment(
    segment: SegmentRecord,
    family: str,
    r: int,
    c: int,
    k: int,
) -> SegmentRecord:
    """Return a copy of segment with NS8 route/anchor fields filled."""
    seed_family, r_prime, c_prime, _ = resolve_to_seed(family, r, c, k, 8)
    anchor = compute_A(family, r, c, k, 8)
    return replace(
        segment,
        ns8_family=family,
        ns8_r=r,
        ns8_c=c,
        ns8_k=k,
        ns8_seed_family=seed_family,
        ns8_r_prime=r_prime,
        ns8_c_prime=c_prime,
        ns8_A=anchor,
    )

