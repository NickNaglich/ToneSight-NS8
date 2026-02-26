
import { renderRunDetail } from "./components/run_detail.js";
import { renderComparePanel } from "./components/compare_panel.js";
import { renderGatePanel } from "./components/gate_panel.js";
import { renderArtifactLinks } from "./components/artifact_links.js";

const API_ROOT = "http://127.0.0.1:8081";
const PAGE_SIZE = 8;

const STATUS = {
  PASS: "PASS",
  REGRESSED: "REGRESSED",
  INCOMPATIBLE: "INCOMPATIBLE",
  NO_GATE: "NO-GATE",
};

const STATUS_CLASS = {
  [STATUS.PASS]: "badge-pass",
  [STATUS.REGRESSED]: "badge-regressed",
  [STATUS.INCOMPATIBLE]: "badge-incompatible",
  [STATUS.NO_GATE]: "badge-no-gate",
};

const SEARCH_PARAMS = new URLSearchParams(window.location.search);
const DEMO_MODE = SEARCH_PARAMS.get("demo") === "1";
const RUN_PARAM = SEARCH_PARAMS.get("run");
const PANEL_PARAM = SEARCH_PARAMS.get("panel");
const AUTO_REFRESH_MS = 30000;
let autoRefreshHandle = null;

const state = {
  loading: true,
  rows: [],
  filtered: [],
  selectedRunId: null,
  page: 1,
  search: "",
  adapter: "ALL",
  status: "ALL",
  density: "expanded",
  autoRefresh: false,
  lastRefreshedAt: null,
  error: "",
};

function toApi(path) {
  return `${API_ROOT}${path}`;
}

function safeText(value, fallback = "n/a") {
  if (value === null || value === undefined || value === "") {
    return fallback;
  }
  return String(value);
}

function floatText(value) {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return "n/a";
  }
  return value.toFixed(3);
}

function percent(value) {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return "n/a";
  }
  return `${(value * 100).toFixed(1)}%`;
}

async function fetchJson(path) {
  const resp = await fetch(toApi(path));
  if (!resp.ok) {
    let payload = null;
    try {
      payload = await resp.json();
    } catch (_err) {
      payload = null;
    }
    return { ok: false, status: resp.status, payload };
  }
  const payload = await resp.json();
  return { ok: true, status: resp.status, payload };
}

function uiLink(runId, panel) {
  const params = new URLSearchParams();
  if (runId) {
    params.set("run", runId);
  }
  if (panel) {
    params.set("panel", panel);
  }
  if (DEMO_MODE) {
    params.set("demo", "1");
  }
  const query = params.toString();
  return `${window.location.origin}${window.location.pathname}${query ? `?${query}` : ""}`;
}

function formatTimestamp(value) {
  if (!value) {
    return "never";
  }
  try {
    return new Date(value).toLocaleString();
  } catch (_err) {
    return String(value);
  }
}

async function copyText(value) {
  if (!value) {
    return;
  }
  try {
    await navigator.clipboard.writeText(value);
  } catch (_err) {
    const input = document.createElement("input");
    input.value = value;
    document.body.appendChild(input);
    input.select();
    document.execCommand("copy");
    document.body.removeChild(input);
  }
}

function syncAutoRefreshTimer() {
  if (autoRefreshHandle) {
    clearInterval(autoRefreshHandle);
    autoRefreshHandle = null;
  }
  if (state.autoRefresh) {
    autoRefreshHandle = setInterval(() => {
      load({ silent: true });
    }, AUTO_REFRESH_MS);
  }
}

function orderRuns(rows) {
  return [...rows].sort((a, b) => String(b.run_id).localeCompare(String(a.run_id)));
}

function pairPreviousRunId(ordered) {
  const asc = [...ordered].reverse();
  const prevById = {};
  for (let i = 0; i < asc.length; i += 1) {
    prevById[asc[i].run_id] = i > 0 ? asc[i - 1].run_id : null;
  }
  return prevById;
}

function gateStatusFromDecision(decision) {
  if (decision === "passed") {
    return STATUS.PASS;
  }
  if (decision === "regressed") {
    return STATUS.REGRESSED;
  }
  if (decision === "incompatible") {
    return STATUS.INCOMPATIBLE;
  }
  return STATUS.NO_GATE;
}

function topDriftLabel(comparePayload) {
  if (!comparePayload || typeof comparePayload !== "object") {
    return "n/a";
  }
  const metrics = comparePayload.metrics || comparePayload;
  const keys = ["delta_avg_l1", "delta_p95_l1", "delta_pass_rate"];
  for (const key of keys) {
    if (typeof metrics[key] === "number") {
      return `${key}: ${metrics[key].toFixed(3)}`;
    }
  }
  return "n/a";
}

function codingSignal(comparePayload, key, formatter = (v) => String(v)) {
  if (!comparePayload || typeof comparePayload !== "object") {
    return "n/a";
  }
  const metrics = comparePayload.metrics || comparePayload;
  if (typeof metrics[key] === "number") {
    return formatter(metrics[key]);
  }
  return "n/a";
}

async function enrichRows(indexRows) {
  const ordered = orderRuns(indexRows);
  const prevById = pairPreviousRunId(ordered);
  const out = [];

  for (const row of ordered) {
    const runId = String(row.run_id);
    const previousRunId = prevById[runId];

    const [receiptResp, summaryResp] = await Promise.all([
      fetchJson(`/api/run/${runId}/receipt`),
      fetchJson(`/api/run/${runId}/summary`),
    ]);

    let compare = null;
    let gate = null;
    let compareError = "";
    let gateError = "";
    if (previousRunId) {
      const [compareResp, gateResp] = await Promise.all([
        fetchJson(`/api/compare/${previousRunId}/${runId}`),
        fetchJson(`/api/gate/${previousRunId}/${runId}`),
      ]);
      compare = compareResp.ok ? compareResp.payload : null;
      gate = gateResp.ok ? gateResp.payload : null;
      compareError = compareResp.ok
        ? ""
        : `compare artifact unavailable (status ${compareResp.status})`;
      gateError = gateResp.ok
        ? ""
        : `gate artifact unavailable (status ${gateResp.status})`;
    }

    const gateStatus = gate ? gateStatusFromDecision(gate.decision) : STATUS.NO_GATE;
    out.push({
      ...row,
      runId,
      previousRunId,
      receipt: receiptResp.ok ? receiptResp.payload : null,
      summary: summaryResp.ok ? summaryResp.payload : null,
      receiptError: receiptResp.ok ? "" : `receipt unavailable (status ${receiptResp.status})`,
      summaryError: summaryResp.ok ? "" : `eval summary unavailable (status ${summaryResp.status})`,
      compare,
      gate,
      compareError,
      gateError,
      gateStatus,
    });
  }
  return out;
}
function applyFilters() {
  const q = state.search.trim().toLowerCase();
  state.filtered = state.rows.filter((row) => {
    const modelTag = String(row.receipt?.model_tag || "").toLowerCase();
    const sourceLabel = String(row.source_label || "").toLowerCase();
    const matchesQ = !q || row.runId.toLowerCase().includes(q) || modelTag.includes(q) || sourceLabel.includes(q);
    const matchesAdapter = state.adapter === "ALL" || sourceLabel === state.adapter.toLowerCase();
    const matchesStatus = state.status === "ALL" || row.gateStatus === state.status;
    return matchesQ && matchesAdapter && matchesStatus;
  });
  if (!state.selectedRunId && state.filtered.length) {
    state.selectedRunId = state.filtered[0].runId;
  }
  const maxPage = Math.max(1, Math.ceil(state.filtered.length / PAGE_SIZE));
  state.page = Math.min(state.page, maxPage);
}

function currentPageRows() {
  const start = (state.page - 1) * PAGE_SIZE;
  return state.filtered.slice(start, start + PAGE_SIZE);
}

function selectedRow() {
  return state.rows.find((r) => r.runId === state.selectedRunId) || null;
}

function distinctAdapters() {
  const set = new Set();
  for (const row of state.rows) {
    if (row.source_label) {
      set.add(String(row.source_label));
    }
  }
  return [...set].sort();
}

function computeKpis() {
  const rows = state.rows;
  const runCount = rows.length;
  const passRates = rows.map((r) => r.summary?.pass_rate).filter((v) => typeof v === "number");
  const avgPassRate = passRates.length ? passRates.reduce((a, b) => a + b, 0) / passRates.length : null;
  const driftRun = rows.find((r) => r.compare);
  const pinnedHealthy = rows.filter((r) => {
    const receipt = r.receipt || {};
    return Boolean(receipt.model_tag && (receipt.model_digest || receipt.model_version));
  }).length;
  const pinnedPct = runCount ? pinnedHealthy / runCount : null;

  return {
    runCount,
    avgPassRate,
    topDrift: driftRun ? topDriftLabel(driftRun.compare) : "n/a",
    pinnedPct,
  };
}

function renderRunCard(row) {
  const reportHref = toApi(`/api/run/${row.runId}/report-html`);
  const compareHref = row.previousRunId ? toApi(`/api/compare-report/${row.previousRunId}/${row.runId}`) : "#";
  const gateHref = row.previousRunId ? toApi(`/api/gate/${row.previousRunId}/${row.runId}`) : "#";
  const detailHref = uiLink(row.runId, "detail");
  const compareDeepHref = uiLink(row.runId, "compare");
  const gateDeepHref = uiLink(row.runId, "gate");
  const badgeClass = STATUS_CLASS[row.gateStatus] || STATUS_CLASS[STATUS.NO_GATE];
  const comparable = row.compare ? "yes" : "no";
  const drift = topDriftLabel(row.compare);
  const mismatch = codingSignal(row.compare, "language_mismatch_rate_delta", (v) => `${(v * 100).toFixed(1)}%`);
  const testsSignal = codingSignal(row.compare, "tests_presence_rate_delta", (v) => (v >= 0 ? "improved" : "declined"));
  const selectedClass = row.runId === state.selectedRunId ? "is-selected" : "";
  const hasErrors = Boolean(row.receiptError || row.summaryError || row.compareError || row.gateError);
  return `
    <article class="run-card ${selectedClass} ${hasErrors ? "has-warning" : ""}" data-run-id="${row.runId}">
      <div class="run-row">
        <div class="badges">
          <span class="badge ${badgeClass}">${row.gateStatus}</span>
          <span class="badge badge-outline">adapter: ${safeText(row.source_label, "n/a")}</span>
          ${hasErrors ? `<span class="badge badge-warn">artifact warnings</span>` : ""}
        </div>
        <div class="meta">${safeText(row.receipt?.model_tag)} | ${safeText(row.receipt?.created_at_utc, "time n/a")}</div>
      </div>
      <div class="run-row quick-grid">
        <div class="quick-item"><div class="k">Comparable</div><div class="v">${comparable}</div></div>
        <div class="quick-item"><div class="k">Top Drift</div><div class="v">${drift}</div></div>
        <div class="quick-item"><div class="k">Lang Mismatch</div><div class="v">${mismatch}</div></div>
        <div class="quick-item"><div class="k">Tests Status</div><div class="v">${testsSignal}</div></div>
      </div>
      <div class="run-row actions">
        <a href="#" data-action="view" data-run-id="${row.runId}">View run</a>
        <a href="${compareHref}" target="_blank" rel="noreferrer" class="${row.compare ? "" : "disabled"}">Compare page</a>
        <a href="${gateHref}" target="_blank" rel="noreferrer" class="${row.gate ? "" : "disabled"}">Gate evidence</a>
        <a href="${reportHref}" target="_blank" rel="noreferrer">report.html</a>
        <button class="btn btn-mini" data-copy-url="${detailHref}">Copy detail</button>
        <button class="btn btn-mini" data-copy-url="${compareDeepHref}">Copy compare</button>
        <button class="btn btn-mini" data-copy-url="${gateDeepHref}">Copy gate</button>
      </div>
    </article>
  `;
}

function wireEvents() {
  const refreshBtn = document.getElementById("refreshBtn");
  if (refreshBtn) {
    refreshBtn.addEventListener("click", () => load({ silent: true }));
  }
  const densityBtn = document.getElementById("densityBtn");
  if (densityBtn) {
    densityBtn.addEventListener("click", () => {
      state.density = state.density === "expanded" ? "compact" : "expanded";
      render();
    });
  }
  const autoRefreshToggle = document.getElementById("autoRefreshToggle");
  if (autoRefreshToggle) {
    autoRefreshToggle.addEventListener("change", (ev) => {
      state.autoRefresh = Boolean(ev.target.checked);
      syncAutoRefreshTimer();
      render();
    });
  }

  const searchInput = document.getElementById("searchInput");
  if (searchInput) {
    searchInput.addEventListener("input", (ev) => {
      state.search = ev.target.value;
      state.page = 1;
      render();
    });
  }

  const adapterSelect = document.getElementById("adapterSelect");
  if (adapterSelect) {
    adapterSelect.addEventListener("change", (ev) => {
      state.adapter = ev.target.value;
      state.page = 1;
      render();
    });
  }

  const statusSelect = document.getElementById("statusSelect");
  if (statusSelect) {
    statusSelect.addEventListener("change", (ev) => {
      state.status = ev.target.value;
      state.page = 1;
      render();
    });
  }

  document.querySelectorAll("[data-action='view']").forEach((el) => {
    el.addEventListener("click", (ev) => {
      ev.preventDefault();
      const runId = ev.currentTarget.getAttribute("data-run-id");
      if (runId) {
        state.selectedRunId = runId;
        render();
      }
    });
  });

  document.querySelectorAll(".run-card").forEach((el) => {
    el.addEventListener("click", (ev) => {
      if (ev.target.closest("[data-action='view']")) {
        return;
      }
      const runId = el.getAttribute("data-run-id");
      if (runId) {
        state.selectedRunId = runId;
        render();
      }
    });
  });
  document.querySelectorAll("[data-copy-url]").forEach((el) => {
    el.addEventListener("click", async (ev) => {
      ev.preventDefault();
      const value = ev.currentTarget.getAttribute("data-copy-url");
      await copyText(value);
      const original = ev.currentTarget.textContent;
      ev.currentTarget.textContent = "Copied";
      setTimeout(() => {
        ev.currentTarget.textContent = original;
      }, 900);
    });
  });
  const prev = document.getElementById("prevPage");
  if (prev) {
    prev.addEventListener("click", () => {
      if (state.page > 1) {
        state.page -= 1;
        render();
      }
    });
  }

  const next = document.getElementById("nextPage");
  if (next) {
    next.addEventListener("click", () => {
      const maxPage = Math.max(1, Math.ceil(state.filtered.length / PAGE_SIZE));
      if (state.page < maxPage) {
        state.page += 1;
        render();
      }
    });
  }
}

function render() {
  const app = document.getElementById("app");
  if (!app) {
    return;
  }
  if (state.loading) {
    app.innerHTML = `
      <div class="shell">
        <section class="kpis">
          <article class="kpi skeleton-card"></article>
          <article class="kpi skeleton-card"></article>
          <article class="kpi skeleton-card"></article>
          <article class="kpi skeleton-card"></article>
        </section>
        <section class="main-grid">
          <section class="panel">
            <div class="skeleton-title"></div>
            <div class="skeleton-row"></div>
            <div class="skeleton-row"></div>
            <div class="skeleton-row"></div>
          </section>
          <aside class="detail-stack">
            <section class="panel"><div class="skeleton-row"></div><div class="skeleton-row"></div></section>
            <section class="panel"><div class="skeleton-row"></div><div class="skeleton-row"></div></section>
          </aside>
        </section>
      </div>`;
    return;
  }
  if (state.error) {
    app.innerHTML = `<div class="shell"><div class="empty">${state.error}</div></div>`;
    return;
  }

  applyFilters();
  const pageRows = currentPageRows();
  const kpis = computeKpis();
  const adapters = distinctAdapters();
  const selected = selectedRow();
  const maxPage = Math.max(1, Math.ceil(state.filtered.length / PAGE_SIZE));

  app.innerHTML = `
    <header class="topbar">
      <div class="topbar-inner">
        <div class="brand">
          <h1 class="brand-title">ToneSight Read-Only Dashboard</h1>
          <p class="brand-sub">runs root: <code>runs/</code> | deterministic artifact viewer only</p>
          <p class="brand-sub">Last refreshed: ${formatTimestamp(state.lastRefreshedAt)}</p>
        </div>
        <div class="toolbar">
          <button id="refreshBtn" class="btn">Refresh</button>
          <button id="densityBtn" class="btn">${state.density === "expanded" ? "Compact" : "Expanded"} view</button>
          <label class="toggle"><input id="autoRefreshToggle" type="checkbox" ${state.autoRefresh ? "checked" : ""}> Auto refresh (30s)</label>
          <a class="btn btn-primary" href="${DEMO_MODE ? "/index.html" : "/index.html?demo=1"}">${DEMO_MODE ? "Demo Off" : "Demo Mode"}</a>
        </div>
      </div>
    </header>
    <main class="shell ${state.density === "compact" ? "density-compact" : ""}">
      <section class="filters">
        <div class="field">
          <label for="searchInput">Search (run id / model / adapter)</label>
          <input id="searchInput" value="${state.search}" placeholder="run_... / model tag / source label">
        </div>
        <div class="field">
          <label for="adapterSelect">Adapter</label>
          <select id="adapterSelect">
            <option value="ALL">All adapters</option>
            ${adapters.map((a) => `<option value="${a}" ${state.adapter === a ? "selected" : ""}>${a}</option>`).join("")}
          </select>
        </div>
        <div class="field">
          <label for="statusSelect">Status</label>
          <select id="statusSelect">
            ${["ALL", STATUS.PASS, STATUS.REGRESSED, STATUS.INCOMPATIBLE, STATUS.NO_GATE]
              .map((s) => `<option value="${s}" ${state.status === s ? "selected" : ""}>${s}</option>`).join("")}
          </select>
        </div>
      </section>

      <section class="kpis">
        <article class="kpi"><div class="k">Runs</div><div class="v">${kpis.runCount}</div></article>
        <article class="kpi"><div class="k">Avg Pass Rate</div><div class="v">${percent(kpis.avgPassRate)}</div></article>
        <article class="kpi"><div class="k">Top Drift Signal</div><div class="v">${safeText(kpis.topDrift)}</div></article>
        <article class="kpi"><div class="k">Pinned Receipt Health</div><div class="v">${percent(kpis.pinnedPct)}</div></article>
      </section>

      <section class="main-grid">
        <section class="panel">
          <h2>Latest Runs</h2>
          ${pageRows.length ? pageRows.map((row) => renderRunCard(row)).join("") : `<div class="empty">No runs found for current filters. Run <code>powershell -ExecutionPolicy Bypass -File scripts/demo_ui_drift_gate_2min.ps1</code> then press Refresh.</div>`}
          <div class="pager">
            <button id="prevPage" class="btn" ${state.page <= 1 ? "disabled" : ""}>Prev</button>
            <div class="meta">Page ${state.page} / ${maxPage} | ${state.filtered.length} runs</div>
            <button id="nextPage" class="btn" ${state.page >= maxPage ? "disabled" : ""}>Next</button>
          </div>
        </section>

        <aside class="detail-stack">
          ${renderRunDetail(selected, {
            toApi,
            safeText,
            percent,
            floatText,
            uiLink,
            statusClassByStatus: STATUS_CLASS,
            statusNoGate: STATUS.NO_GATE,
          })}
          ${renderComparePanel(selected, { toApi, safeText, floatText, uiLink })}
          ${renderGatePanel(selected, {
            toApi,
            safeText,
            uiLink,
            statusClassByStatus: STATUS_CLASS,
            statusNoGate: STATUS.NO_GATE,
          })}
          ${renderArtifactLinks(selected, { toApi })}
        </aside>
      </section>

      <p class="footer-note">Read-only dashboard over allowlisted artifacts only. Status legend: PASS (green), REGRESSED (red), INCOMPATIBLE (amber), NO-GATE (gray).</p>
    </main>
  `;

  wireEvents();

  const panelTargetByParam = {
    detail: ".run-health",
    compare: ".compare-panel",
    gate: ".gate-panel",
  };
  const targetSelector = panelTargetByParam[PANEL_PARAM] || (DEMO_MODE ? ".gate-panel" : "");
  if (targetSelector) {
    const targetPanel = document.querySelector(targetSelector);
    if (targetPanel) {
      targetPanel.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }
}
async function load({ silent = false } = {}) {
  if (!silent || state.rows.length === 0) {
    state.loading = true;
  }
  state.error = "";
  render();
  try {
    const indexResp = await fetchJson("/api/index");
    if (!indexResp.ok || !Array.isArray(indexResp.payload)) {
      throw new Error("Unable to read /api/index. Start API server with runs root and regenerate index artifacts.");
    }
    state.rows = await enrichRows(indexResp.payload);
    if (RUN_PARAM && state.rows.some((row) => row.runId === RUN_PARAM)) {
      state.selectedRunId = RUN_PARAM;
    } else if (!state.selectedRunId && state.rows.length) {
      state.selectedRunId = state.rows[0].runId;
    }
    state.lastRefreshedAt = new Date().toISOString();
  } catch (err) {
    state.error = `Failed to load dashboard data: ${safeText(err.message)}`;
  } finally {
    state.loading = false;
    render();
  }
}

load();
