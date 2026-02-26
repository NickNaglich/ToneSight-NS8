export function renderArtifactLinks(row, options) {
  if (!row) {
    return `
      <section class="panel">
        <h3>Artifacts</h3>
        <div class="empty">Select a run to view artifact links.</div>
      </section>
    `;
  }

  const reportHref = options.toApi(`/api/run/${row.runId}/report-html`);
  const receiptHref = options.toApi(`/api/run/${row.runId}/receipt`);
  const summaryHref = options.toApi(`/api/run/${row.runId}/summary`);
  const reportJsonHref = options.toApi(`/api/run/${row.runId}/report`);
  const compareHref = row.previousRunId ? options.toApi(`/api/compare/${row.previousRunId}/${row.runId}`) : "";
  const comparePageHref = row.previousRunId ? options.toApi(`/api/compare-report/${row.previousRunId}/${row.runId}`) : "";
  const gateHref = row.previousRunId ? options.toApi(`/api/gate/${row.previousRunId}/${row.runId}`) : "";
  const derivedRows = [
    { label: "receipt.json", href: receiptHref, enabled: true },
    { label: "eval_summary.json", href: summaryHref, enabled: true },
    { label: "report.json", href: reportJsonHref, enabled: true },
    { label: "report.html", href: reportHref, enabled: true },
    { label: "compare_report.html", href: comparePageHref, enabled: Boolean(comparePageHref) },
    { label: "compare_summary.json", href: compareHref, enabled: Boolean(compareHref) },
    { label: "gate_result.json", href: gateHref, enabled: Boolean(gateHref) },
  ];

  return `
    <section class="panel">
      <h3>Artifacts</h3>
      <p class="meta">Derived artifacts (UI-safe)</p>
      <table class="artifact-table">
        <thead><tr><th>Artifact</th><th>Open</th><th>Copy URL</th></tr></thead>
        <tbody>
          ${derivedRows
            .map(
              (rowItem) => `
                <tr>
                  <td>${rowItem.label}</td>
                  <td>${rowItem.enabled ? `<a href="${rowItem.href}" target="_blank" rel="noreferrer">Open</a>` : `<span class="muted-pill">Unavailable</span>`}</td>
                  <td>${rowItem.enabled ? `<button class="btn btn-mini" data-copy-url="${rowItem.href}">Copy</button>` : `<span class="muted-pill">-</span>`}</td>
                </tr>
              `
            )
            .join("")}
        </tbody>
      </table>

      <p class="meta top-gap">Raw artifacts (restricted)</p>
      <div class="restricted-list">
        <span class="restricted-item" title="Restricted artifacts may include raw/sensitive data; hidden by default per retention policy.">events.raw.jsonl (not linked)</span>
        <span class="restricted-item" title="Restricted artifacts may include raw/sensitive data; hidden by default per retention policy.">quarantine.jsonl (not linked)</span>
      </div>
      <p class="safety-note">Restricted artifacts may include raw/sensitive data; hidden by default per retention policy.</p>
    </section>
  `;
}
