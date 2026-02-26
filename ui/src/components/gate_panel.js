function gateOneLine(gate, safeText) {
  if (!gate) {
    return "Gate evidence unavailable.";
  }
  if (gate.human_summary) {
    return safeText(gate.human_summary);
  }
  if (Array.isArray(gate.violations) && gate.violations.length > 0) {
    const v = gate.violations[0] || {};
    return `Gate failed: ${safeText(v.metric)} ${safeText(v.operator)} ${safeText(v.threshold)} (actual ${safeText(v.actual)}).`;
  }
  if (Array.isArray(gate.incompatibilities) && gate.incompatibilities.length > 0) {
    const issue = gate.incompatibilities[0] || {};
    return `Gate incompatible: ${safeText(issue.reason)}`;
  }
  return `Gate decision: ${safeText(gate.decision)}`;
}

export function renderGatePanel(row, options) {
  if (!row || !row.previousRunId) {
    return `
      <section class="panel">
        <h3>Gate Evidence</h3>
        <div class="empty">No previous run available for gate evidence.</div>
      </section>
    `;
  }

  const gateHref = options.toApi(`/api/gate/${row.previousRunId}/${row.runId}`);
  const gate = row.gate;
  if (!gate) {
    return `
      <section class="panel">
        <h3>Gate Evidence</h3>
        <div class="empty">No gate_result artifact found for this run pair.${row.gateError ? ` ${options.safeText(row.gateError)}` : ""}</div>
      </section>
    `;
  }

  const badgeClass = options.statusClassByStatus[row.gateStatus] || options.statusClassByStatus[options.statusNoGate];
  const thresholds = gate.thresholds || {};
  const firstLine = gateOneLine(gate, options.safeText);

  return `
    <section class="panel gate-panel">
      <h3>Gate Evidence</h3>
      <div class="badges">
        <span class="badge ${badgeClass}">${options.safeText(row.gateStatus)}</span>
      </div>
      <p class="gate-line">${firstLine}</p>
      <div class="kv-grid dense">
        <div class="kv"><span>decision</span><strong>${options.safeText(gate.decision)}</strong></div>
        <div class="kv"><span>min_pass_rate_delta</span><strong>${options.safeText(thresholds.min_pass_rate_delta)}</strong></div>
        <div class="kv"><span>max_avg_l1_delta</span><strong>${options.safeText(thresholds.max_avg_l1_delta)}</strong></div>
        <div class="kv"><span>max_p95_l1_delta</span><strong>${options.safeText(thresholds.max_p95_l1_delta)}</strong></div>
        <div class="kv"><span>violation_count</span><strong>${options.safeText(Array.isArray(gate.violations) ? gate.violations.length : 0)}</strong></div>
        <div class="kv"><span>incompatibility_count</span><strong>${options.safeText(Array.isArray(gate.incompatibilities) ? gate.incompatibilities.length : 0)}</strong></div>
      </div>
      <div class="actions inline-actions">
        <button class="btn btn-mini" data-copy-url="${options.uiLink(row.runId, "gate")}">Copy gate deep link</button>
        <a href="${gateHref}" target="_blank" rel="noreferrer">gate_result.json</a>
      </div>
    </section>
  `;
}
