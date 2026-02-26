export function renderComparePanel(row, options) {
  if (!row || !row.previousRunId) {
    return `
      <section class="panel">
        <h3>Compare Evidence</h3>
        <div class="empty">No previous run available for compare.</div>
      </section>
    `;
  }

  const compareHref = options.toApi(`/api/compare/${row.previousRunId}/${row.runId}`);
  const comparePageHref = options.toApi(`/api/compare-report/${row.previousRunId}/${row.runId}`);
  const compare = row.compare;
  if (!compare) {
    return `
      <section class="panel">
        <h3>Compare Evidence</h3>
        <div class="empty">No compare_summary artifact found for this run pair.${row.compareError ? ` ${options.safeText(row.compareError)}` : ""}</div>
      </section>
    `;
  }

  const metrics = compare.metrics || {};
  const topSignals = [
    { label: "delta_pass_rate", value: options.floatText(metrics.delta_pass_rate) },
    { label: "delta_avg_l1", value: options.floatText(metrics.delta_avg_l1) },
    { label: "delta_p95_l1", value: options.floatText(metrics.delta_p95_l1) },
    { label: "pass_rate_trend", value: options.safeText(metrics.pass_rate_trend) },
  ];

  const rows = compare.rows || {};
  const regressionCoverage = compare.regression_coverage || {};

  return `
    <section class="panel compare-panel">
      <h3>Compare Evidence</h3>
      <div class="kv-grid">
        ${topSignals.map((item) => `<div class="kv"><span>${item.label}</span><strong>${item.value}</strong></div>`).join("")}
      </div>
      <details>
        <summary>Show full compare fields</summary>
        <div class="kv-grid dense">
          <div class="kv"><span>distance_mode</span><strong>${options.safeText(compare.distance_mode)}</strong></div>
          <div class="kv"><span>count_common_ids</span><strong>${options.safeText(rows.count_common_ids)}</strong></div>
          <div class="kv"><span>count_only_in_a</span><strong>${options.safeText(rows.count_only_in_a)}</strong></div>
          <div class="kv"><span>count_only_in_b</span><strong>${options.safeText(rows.count_only_in_b)}</strong></div>
          <div class="kv"><span>top_n_returned</span><strong>${options.safeText(regressionCoverage.top_n_returned)}</strong></div>
          <div class="kv"><span>truncated</span><strong>${options.safeText(regressionCoverage.truncated)}</strong></div>
        </div>
      </details>
      <div class="actions inline-actions">
        <button class="btn btn-mini" data-copy-url="${options.uiLink(row.runId, "compare")}">Copy compare deep link</button>
        <a href="${comparePageHref}" target="_blank" rel="noreferrer">compare_report.html</a>
        <a href="${compareHref}" target="_blank" rel="noreferrer">compare_summary.json</a>
      </div>
    </section>
  `;
}
