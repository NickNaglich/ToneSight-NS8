"""ToneSight NS8 package surface (incremental v1)."""

from .api import (
    attach_tonesight_to_segment,
    tonesight_from_label,
    tonesight_from_vad,
    tonesight_receipt_from_segment,
)
from .analytics import summarize_session, summarize_speaker
from .compare_runner import run_compare
from .eval_compare_runner import run_eval_compare
from .eval_runner import run_eval
from .mapping import (
    get_default_mapping,
    get_default_mapping_id,
    get_mapping,
    list_mappings,
    register_mapping,
)
from .ns8 import compute_A, resolve_to_seed, validate_inputs
from .schema import Route, SegmentRecord, SessionSummary, SpeakerSummary, ToneReceipt

__all__ = [
    "compute_A",
    "resolve_to_seed",
    "validate_inputs",
    "tonesight_from_label",
    "tonesight_from_vad",
    "tonesight_receipt_from_segment",
    "attach_tonesight_to_segment",
    "Route",
    "ToneReceipt",
    "SegmentRecord",
    "SpeakerSummary",
    "SessionSummary",
    "summarize_speaker",
    "summarize_session",
    "run_eval",
    "run_compare",
    "run_eval_compare",
    "register_mapping",
    "get_mapping",
    "list_mappings",
    "get_default_mapping",
    "get_default_mapping_id",
]
