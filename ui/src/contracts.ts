// Read-only contract allowlists for the Phase 3 UI.
// These constants are policy boundaries, not scoring logic.

export const UI_ALLOWED_ARTIFACT_PATH_PATTERNS = [
  "runs/index.json",
  "runs/<run_id>/receipt.json",
  "runs/<run_id>/eval_summary.json",
  "runs/<run_id>/report.html",
  "runs/<run_id>/reports/report_<run_id>.json",
  "runs/<run_b>/comparisons/<run_a>/compare_report.html",
  "runs/<run_b>/reports/report_<run_a>_to_<run_b>.json",
  "runs/<run_b>/comparisons/<run_a>/compare_summary.json",
  "runs/<run_b>/comparisons/<run_a>/gate_result.json",
] as const;

export const UI_DISALLOWED_ARTIFACT_PATTERNS = [
  "runs/captures/<capture_id>/events.raw.jsonl",
  "runs/<run_live_id>/quarantine.jsonl",
] as const;

export const UI_INDEX_ROW_ALLOWED_FIELDS = [
  "run_id",
  "dataset_hash",
  "spec_version",
  "mapping_id",
  "mapping_version",
  "profile_label",
  "source_label",
  "source_labels",
  "artifacts.out_jsonl",
  "artifacts.eval_summary_json",
  "artifacts.report_html",
  "artifacts.receipt_json",
] as const;

export const UI_RECEIPT_ALLOWED_FIELDS = [
  "run_id",
  "spec_version",
  "dataset_hash",
  "taxonomy_hash",
  "defaults_hash",
  "mapping_id",
  "mapping_version",
  "defaults_spec_version",
  "provider",
  "model_tag",
  "model_digest",
  "model_version",
  "generation_settings",
  "redaction_summary",
  "created_at_utc",
  "code_revision",
] as const;

export const UI_EVAL_SUMMARY_ALLOWED_FIELDS = [
  "count_rows",
  "pass_rate",
  "fail_rate",
  "avg_l1",
  "p95_l1",
  "max_l1",
  "pass_count",
  "fail_count",
  "threshold_l1",
] as const;

export type UIAllowedArtifactPathPattern = (typeof UI_ALLOWED_ARTIFACT_PATH_PATTERNS)[number];
export type UIDisallowedArtifactPathPattern = (typeof UI_DISALLOWED_ARTIFACT_PATTERNS)[number];
export type UIIndexRowAllowedField = (typeof UI_INDEX_ROW_ALLOWED_FIELDS)[number];
export type UIReceiptAllowedField = (typeof UI_RECEIPT_ALLOWED_FIELDS)[number];
export type UIEvalSummaryAllowedField = (typeof UI_EVAL_SUMMARY_ALLOWED_FIELDS)[number];
