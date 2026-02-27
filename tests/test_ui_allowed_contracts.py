import re
from pathlib import Path


def _extract_ts_string_array(source: str, const_name: str) -> list[str]:
    pattern = rf"export const {const_name}\s*=\s*\[(.*?)\]\s*as const;"
    match = re.search(pattern, source, flags=re.DOTALL)
    if not match:
        raise AssertionError(f"Missing constant array: {const_name}")
    block = match.group(1)
    return re.findall(r'"([^"]+)"', block)


def test_ui_contracts_allowlist_contains_required_artifacts_and_fields():
    ts_path = Path("ui/src/contracts.ts")
    assert ts_path.exists(), "Missing ui/src/contracts.ts"
    source = ts_path.read_text(encoding="utf-8")

    artifact_patterns = _extract_ts_string_array(source, "UI_ALLOWED_ARTIFACT_PATH_PATTERNS")
    assert "runs/index.json" in artifact_patterns
    assert "runs/<run_id>/receipt.json" in artifact_patterns
    assert "runs/<run_id>/eval_summary.json" in artifact_patterns
    assert "runs/<run_id>/report.html" in artifact_patterns
    assert "runs/<run_b>/comparisons/<run_a>/compare_report.html" in artifact_patterns
    assert "runs/<run_b>/comparisons/<run_a>/compare_summary.json" in artifact_patterns
    assert "runs/<run_b>/comparisons/<run_a>/gate_result.json" in artifact_patterns

    index_fields = _extract_ts_string_array(source, "UI_INDEX_ROW_ALLOWED_FIELDS")
    assert "run_id" in index_fields
    assert "dataset_hash" in index_fields
    assert "artifacts.eval_summary_json" in index_fields

    receipt_fields = _extract_ts_string_array(source, "UI_RECEIPT_ALLOWED_FIELDS")
    assert "mapping_id" in receipt_fields
    assert "model_digest" in receipt_fields
    assert "redaction_summary" in receipt_fields

    eval_fields = _extract_ts_string_array(source, "UI_EVAL_SUMMARY_ALLOWED_FIELDS")
    assert "pass_rate" in eval_fields
    assert "avg_l1" in eval_fields
    assert "threshold_l1" in eval_fields


def test_ui_contracts_disallow_raw_capture_artifacts_by_default():
    source = Path("ui/src/contracts.ts").read_text(encoding="utf-8")
    disallowed = _extract_ts_string_array(source, "UI_DISALLOWED_ARTIFACT_PATTERNS")
    assert "runs/captures/<capture_id>/events.raw.jsonl" in disallowed
    assert "runs/<run_live_id>/quarantine.jsonl" in disallowed

    allowed = _extract_ts_string_array(source, "UI_ALLOWED_ARTIFACT_PATH_PATTERNS")
    assert "runs/captures/<capture_id>/events.raw.jsonl" not in allowed
    assert "runs/<run_live_id>/quarantine.jsonl" not in allowed


def test_ui_contracts_doc_exists_and_references_enforcement_points():
    doc = Path("docs/UI_ALLOWED_CONTRACTS.md")
    assert doc.exists(), "Missing docs/UI_ALLOWED_CONTRACTS.md"
    text = doc.read_text(encoding="utf-8")
    assert "UI is a read-only renderer" in text
    assert "ui/src/contracts.ts" in text
    assert "tests/test_ui_allowed_contracts.py" in text


def test_ui_phase_a_status_mapping_and_raw_artifact_exclusion():
    app_js = Path("ui/src/app.js")
    styles_css = Path("ui/src/styles.css")
    index_html = Path("ui/index.html")

    assert app_js.exists(), "Missing ui/src/app.js"
    assert styles_css.exists(), "Missing ui/src/styles.css"
    assert index_html.exists(), "Missing ui/index.html"

    app_text = app_js.read_text(encoding="utf-8")
    css_text = styles_css.read_text(encoding="utf-8")

    # Fixed status mapping required by Phase A.
    assert 'PASS: "PASS"' in app_text
    assert 'REGRESSED: "REGRESSED"' in app_text
    assert 'INCOMPATIBLE: "INCOMPATIBLE"' in app_text
    assert 'NO_GATE: "NO-GATE"' in app_text
    assert "badge-pass" in css_text
    assert "badge-regressed" in css_text
    assert "badge-incompatible" in css_text
    assert "badge-no-gate" in css_text

    # UI shell remains artifact API-driven and does not reference restricted artifacts.
    assert "/api/index" in app_text
    assert "/api/run/" in app_text
    assert "/api/run/${row.runId}/report-html" in app_text
    assert "/api/compare-report/" in app_text
    assert "/api/compare/" in app_text
    assert "/api/gate/" in app_text
    assert "/api/pipeline/run" in app_text
    assert "runPipelineBtn" in app_text
    assert "pipelineEventsPath" in app_text
    assert "events.raw.jsonl" not in app_text
    assert "quarantine.jsonl" not in app_text

def test_ui_phase_b_detail_compare_gate_modules_and_constraints():
    app_text = Path("ui/src/app.js").read_text(encoding="utf-8")
    run_detail = Path("ui/src/components/run_detail.js")
    compare_panel = Path("ui/src/components/compare_panel.js")
    gate_panel = Path("ui/src/components/gate_panel.js")

    assert run_detail.exists(), "Missing ui/src/components/run_detail.js"
    assert compare_panel.exists(), "Missing ui/src/components/compare_panel.js"
    assert gate_panel.exists(), "Missing ui/src/components/gate_panel.js"

    run_detail_text = run_detail.read_text(encoding="utf-8")
    compare_text = compare_panel.read_text(encoding="utf-8")
    gate_text = gate_panel.read_text(encoding="utf-8")

    assert "renderRunDetail" in app_text
    assert "renderComparePanel" in app_text
    assert "renderGatePanel" in app_text

    # Ensure run detail includes receipt provenance and eval summary links.
    assert "Provider" in run_detail_text
    assert "Model tag" in run_detail_text
    assert "Eval Summary" in run_detail_text
    assert "/api/run/${row.runId}/receipt" in run_detail_text
    assert "/api/run/${row.runId}/summary" in run_detail_text
    assert "/api/run/${row.runId}/report-html" in run_detail_text

    # Compare and gate panels render artifact payloads only.
    assert "compare.metrics" in compare_text
    assert "/api/compare-report/${row.previousRunId}/${row.runId}" in compare_text
    assert "/api/compare/${row.previousRunId}/${row.runId}" in compare_text
    assert "gate.human_summary" in gate_text
    assert "/api/gate/${row.previousRunId}/${row.runId}" in gate_text

    # Restricted raw artifacts must remain absent from UI modules.
    joined = "\n".join([app_text, run_detail_text, compare_text, gate_text])
    assert "events.raw.jsonl" not in joined
    assert "quarantine.jsonl" not in joined


def test_ui_phase_c_artifact_links_safety_separation():
    app_text = Path("ui/src/app.js").read_text(encoding="utf-8")
    artifact_links = Path("ui/src/components/artifact_links.js")
    assert artifact_links.exists(), "Missing ui/src/components/artifact_links.js"
    artifact_text = artifact_links.read_text(encoding="utf-8")

    assert "renderArtifactLinks" in app_text
    assert "Derived artifacts (UI-safe)" in artifact_text
    assert "Raw artifacts (restricted)" in artifact_text
    assert "events.raw.jsonl (not linked)" in artifact_text
    assert "quarantine.jsonl (not linked)" in artifact_text
    assert "hidden by default per retention policy" in artifact_text

    # Restricted artifacts are visible as labels only, not default hyperlinks.
    assert "href=\"/runs/captures/" not in artifact_text
    assert "href=\"/runs/<run_live_id>/quarantine.jsonl\"" not in artifact_text


def test_ui_deeplink_and_polish_controls_present():
    app_text = Path("ui/src/app.js").read_text(encoding="utf-8")
    styles_text = Path("ui/src/styles.css").read_text(encoding="utf-8")
    compare_panel = Path("ui/src/components/compare_panel.js").read_text(encoding="utf-8")
    gate_panel = Path("ui/src/components/gate_panel.js").read_text(encoding="utf-8")
    run_detail = Path("ui/src/components/run_detail.js").read_text(encoding="utf-8")

    # Deep-link smoke: run/panel parsing and target mapping.
    assert 'const RUN_PARAM = SEARCH_PARAMS.get("run")' in app_text
    assert 'const PANEL_PARAM = SEARCH_PARAMS.get("panel")' in app_text
    assert "panelTargetByParam" in app_text
    assert '".compare-panel"' in app_text
    assert '".gate-panel"' in app_text

    # UX polish controls.
    assert "autoRefreshToggle" in app_text
    assert "densityBtn" in app_text
    assert "Last refreshed:" in app_text
    assert "data-copy-url" in app_text
    assert "skeleton-card" in app_text
    assert "density-compact" in styles_text
    assert "artifact-table" in styles_text

    # Share buttons available in detail/compare/gate panels.
    assert "Copy detail link" in run_detail
    assert "Copy compare deep link" in compare_panel
    assert "Copy gate deep link" in gate_panel
