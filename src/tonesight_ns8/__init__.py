"""ToneSight NS8 package surface (incremental pre-1.0)."""

from .api import (
    attach_tonesight_to_segment,
    tonesight_from_label,
    tonesight_from_llm_labels,
    tonesight_from_vad,
    tonesight_from_vad_batch,
    tonesight_receipt_from_label_context,
    tonesight_receipt_from_vad_context,
    tonesight_receipt_from_segment,
)
from .analytics import summarize_session, summarize_speaker
from .bundle_runner import run_bundle
from .benchmark_runner import run_benchmark_suite
from .canary_runner import run_canary
from .compare_runner import run_compare
from .data_lint_runner import run_data_lint
from .eval_compare_runner import run_eval_compare
from .eval_runner import log_eval_to_mlflow, run_eval
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
from .domainpacks import (
    get_builtin_domainpack_profile_path,
    list_builtin_domainpack_profiles,
    load_builtin_domainpack_profile,
    load_mapping_profile,
    stable_payload_hash,
    validate_mapping_profile,
)
from .ns8 import compute_A, resolve_to_seed, validate_inputs
from .signal_mapping import fold_channels, map_observation_to_ns8
from .signal_runner import run_signal_pipeline, run_signal_pipeline_with_profile
from .redaction import redact_live_event, redact_text
from .report_runner import run_report
from .release_check_runner import run_release_check
from .retention import run_retention_purge
from .run_index import run_index, run_index_json
from .schema import Route, SegmentRecord, SessionSummary, SpeakerSummary, ToneReceipt
from .stream_runner import new_stream_state, run_stream_update, snapshot_stream_state
from .trend_runner import run_trend
from .triage_runner import run_triage
from .ui_package_runner import run_ui_package

__all__ = [
    "compute_A",
    "resolve_to_seed",
    "validate_inputs",
    "tonesight_from_label",
    "tonesight_from_llm_labels",
    "tonesight_from_vad",
    "tonesight_from_vad_batch",
    "tonesight_receipt_from_label_context",
    "tonesight_receipt_from_vad_context",
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
    "log_eval_to_mlflow",
    "run_compare",
    "run_data_lint",
    "run_eval_compare",
    "run_gate",
    "run_canary",
    "run_triage",
    "run_ui_package",
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
    "run_report",
    "run_release_check",
    "run_index",
    "run_index_json",
    "new_stream_state",
    "snapshot_stream_state",
    "run_stream_update",
    "redact_text",
    "redact_live_event",
    "run_retention_purge",
    "register_mapping",
    "get_mapping",
    "list_mappings",
    "get_default_mapping",
    "get_default_mapping_id",
    "validate_mapping_profile",
    "load_mapping_profile",
    "list_builtin_domainpack_profiles",
    "get_builtin_domainpack_profile_path",
    "load_builtin_domainpack_profile",
    "stable_payload_hash",
    "fold_channels",
    "map_observation_to_ns8",
    "run_signal_pipeline",
    "run_signal_pipeline_with_profile",
]
