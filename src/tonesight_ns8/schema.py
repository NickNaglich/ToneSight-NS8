"""Schema dataclasses for segment/speaker/session analytics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class SegmentRecord:
    segment_id: str
    speaker_id: str
    start_sec: float
    end_sec: float
    V: int
    A: int
    D: int
    tone_label: Optional[str] = None
    ns8_family: Optional[str] = None
    ns8_r: Optional[int] = None
    ns8_c: Optional[int] = None
    ns8_k: Optional[int] = None
    ns8_seed_family: Optional[str] = None
    ns8_r_prime: Optional[int] = None
    ns8_c_prime: Optional[int] = None
    ns8_A: Optional[int] = None
    receipt_ref: Optional[str] = None


@dataclass(frozen=True)
class SpeakerSummary:
    speaker_id: str
    count_segments: int
    vad_centroid: tuple[float, float, float]
    volatility: float
    distributions: dict[str, list[int]]


@dataclass(frozen=True)
class SessionSummary:
    session_id: str
    count_segments: int
    vad_centroid: tuple[float, float, float]
    distributions: dict[str, list[int]]
    spike_count: int
    spike_rate: float
    spike_segments: list[str]


@dataclass(frozen=True)
class Route:
    seed_family: str
    r_prime: int
    c_prime: int


@dataclass(frozen=True)
class ToneReceipt:
    spec_version: str
    input: dict
    route: dict
    output: dict
