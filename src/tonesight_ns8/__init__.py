"""ToneSight NS8 package surface (incremental pre-1.0)."""

from .api import (
    attach_tonesight_to_segment,
    tonesight_from_label,
    tonesight_from_vad,
    tonesight_receipt_from_segment,
)
from .analytics import summarize_session, summarize_speaker
from .bundle_runner import run_bundle
from .benchmark_runner import run_benchmark_suite
from .canary_runner import run_canary
from .compare_runner import run_compare
from .eval_compare_runner import run_eval_compare
from .eval_runner import run_eval
from .gate_runner import run_gate
from .incident_runner import run_incident
from .live_identity import canonical_live_event, stable_event_hash
from .live_runner import run_live_capture, run_live_replay, run_live_verify
from .live_shadow_policy import apply_shadow_policy
from .mapping import (
    get_default_mapping,
    get_default_mapping_id,
    get_mapping,
    list_mappings,
    register_mapping,
)
from .ns8 import compute_A, resolve_to_seed, validate_inputs
from .redaction import redact_live_event, redact_text
from .retention import run_retention_purge
from .run_index import run_index
from .schema import Route, SegmentRecord, SessionSummary, SpeakerSummary, ToneReceipt
from .trend_runner import run_trend
from .triage_runner import run_triage

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
    "run_gate",
    "run_canary",
    "run_triage",
    "run_bundle",
    "run_benchmark_suite",
    "run_incident",
    "run_trend",
    "canonical_live_event",
    "stable_event_hash",
    "apply_shadow_policy",
    "run_live_capture",
    "run_live_replay",
    "run_live_verify",
    "run_index",
    "redact_text",
    "redact_live_event",
    "run_retention_purge",
    "register_mapping",
    "get_mapping",
    "list_mappings",
    "get_default_mapping",
    "get_default_mapping_id",
]
