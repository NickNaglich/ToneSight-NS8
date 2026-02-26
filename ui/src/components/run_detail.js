export function renderRunDetail(row, options) {
  if (!row) {
    return `<div class="empty">Select a run to view detail.</div>`;
  }

  const reportHref = options.toApi(`/api/run/${row.runId}/report-html`);
  const receiptHref = options.toApi(`/api/run/${row.runId}/receipt`);
  const summaryHref = options.toApi(`/api/run/${row.runId}/summary`);
  const reportJsonHref = options.toApi(`/api/run/${row.runId}/report`);
  const badgeClass = options.statusClassByStatus[row.gateStatus] || options.statusClassByStatus[options.statusNoGate];

  const receipt = row.receipt || {};
  const summary = row.summary || {};
  const modelIdentity = receipt.model_digest || receipt.model_version || "n/a";
  const comparable = row.compare ? "yes" : "no";
  const detailLink = options.uiLink(row.runId, "detail");
  const compareLink = options.uiLink(row.runId, "compare");
  const gateLink = options.uiLink(row.runId, "gate");
  const detailErrors = [row.receiptError, row.summaryError].filter(Boolean);

  return `
    <section class="panel run-health">
      <h3>Run Health Summary</h3>
      <div class="badges">
        <span class="badge ${badgeClass}">${options.safeText(row.gateStatus)}</span>
        <span class="badge badge-outline">Adapter: ${options.safeText(row.source_label)}</span>
        <span class="badge badge-outline">Model: ${options.safeText(receipt.model_tag)}</span>
        <span class="badge badge-outline">Comparable: ${comparable}</span>
      </div>
      <div class="actions inline-actions">
        <button class="btn btn-mini" data-copy-url="${detailLink}">Copy detail link</button>
        <button class="btn btn-mini" data-copy-url="${compareLink}">Copy compare link</button>
        <button class="btn btn-mini" data-copy-url="${gateLink}">Copy gate link</button>
      </div>
    </section>

    ${
      detailErrors.length
        ? `<section class="panel"><div class="warn-box">Some run artifacts are unavailable: ${detailErrors.join(" | ")}</div></section>`
        : ""
    }

    <section class="panel">
      <h3>Provenance</h3>
      <div class="kv-grid">
        <div class="kv"><span>Provider</span><strong>${options.safeText(receipt.provider)}</strong></div>
        <div class="kv"><span>Model tag</span><strong>${options.safeText(receipt.model_tag)}</strong></div>
        <div class="kv"><span>Digest or version</span><strong>${options.safeText(modelIdentity)}</strong></div>
        <div class="kv"><span>Created</span><strong>${options.safeText(receipt.created_at_utc)}</strong></div>
        <div class="kv"><span>Redaction</span><strong>${options.safeText(receipt.redaction_summary, "derived-only UI view")}</strong></div>
        <div class="kv"><span>Code revision</span><strong>${options.safeText(receipt.code_revision)}</strong></div>
      </div>
      <pre class="settings">${options.safeText(receipt.generation_settings, "n/a")}</pre>
    </section>

    <section class="panel">
      <h3>Eval Summary</h3>
      <div class="kv-grid">
        <div class="kv"><span>Rows</span><strong>${options.safeText(summary.count_rows)}</strong></div>
        <div class="kv"><span>Pass rate</span><strong>${options.percent(summary.pass_rate)}</strong></div>
        <div class="kv"><span>Fail rate</span><strong>${options.percent(summary.fail_rate)}</strong></div>
        <div class="kv"><span>Avg L1</span><strong>${options.floatText(summary.avg_l1)}</strong></div>
        <div class="kv"><span>P95 L1</span><strong>${options.floatText(summary.p95_l1)}</strong></div>
        <div class="kv"><span>Threshold L1</span><strong>${options.safeText(summary.threshold_l1)}</strong></div>
      </div>
      <div class="actions inline-actions">
        <a href="${reportHref}" target="_blank" rel="noreferrer">report.html</a>
        <a href="${receiptHref}" target="_blank" rel="noreferrer">receipt.json</a>
        <a href="${summaryHref}" target="_blank" rel="noreferrer">eval_summary.json</a>
        <a href="${reportJsonHref}" target="_blank" rel="noreferrer">report json</a>
      </div>
    </section>
  `;
}
