"""Deterministic goldset evaluation runner."""

from __future__ import annotations

import hashlib
import html
import json
import platform
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .defaults import EVAL_DEFAULTS
from .taxonomy import get_vad, load_taxonomy


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    text = "\n".join(json.dumps(row, ensure_ascii=True) for row in rows) + "\n"
    path.write_text(text, encoding="utf-8")


def _l1(a: tuple[int, int, int], b: tuple[int, int, int]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2])


def _p95(values: list[float]) -> float:
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    idx = int(round(0.95 * (len(sorted_vals) - 1)))
    return float(sorted_vals[idx])


def _median(values: list[float]) -> float:
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    mid = n // 2
    if n % 2 == 1:
        return float(sorted_vals[mid])
    return float((sorted_vals[mid - 1] + sorted_vals[mid]) / 2.0)


def _percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    pos = p * (len(sorted_vals) - 1)
    lo = int(pos)
    hi = min(lo + 1, len(sorted_vals) - 1)
    if lo == hi:
        return float(sorted_vals[lo])
    frac = pos - lo
    return float(sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * frac)


def _dataset_hash(path: Path) -> str:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return digest[:12]


def _load_calibration(calibration_path: str | None) -> dict[str, tuple[int, int, int]]:
    if not calibration_path:
        return {}
    payload = json.loads(Path(calibration_path).read_text(encoding="utf-8"))
    overrides = payload.get("label_overrides", {})
    out: dict[str, tuple[int, int, int]] = {}
    for label, vad in overrides.items():
        out[str(label)] = (int(vad["V"]), int(vad["A"]), int(vad["D"]))
    return out


def _gpu_snapshot() -> dict[str, Any]:
    if shutil.which("nvidia-smi") is None:
        return {"available": False, "reason": "nvidia-smi not found"}
    cmd = [
        "nvidia-smi",
        "--query-gpu=index,name,utilization.gpu,utilization.memory,memory.total,memory.used,temperature.gpu,power.draw",
        "--format=csv,noheader,nounits",
    ]
    try:
        proc = subprocess.run(cmd, check=True, capture_output=True, text=True)
        rows = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
        return {"available": True, "rows": rows}
    except Exception as exc:  # pragma: no cover
        return {"available": False, "reason": str(exc)}


def _maybe_log_mlflow(
    *,
    tracking_uri: str | None,
    result: dict[str, Any],
    out_dir: Path,
    threshold_l1: int,
    taxonomy_path: str,
    calibration_path: str | None,
) -> dict[str, Any] | None:
    if not tracking_uri:
        return None
    try:
        import mlflow  # type: ignore
    except Exception as exc:  # pragma: no cover
        return {"enabled": False, "reason": f"mlflow import failed: {exc}"}

    mlflow.set_tracking_uri(tracking_uri)
    with mlflow.start_run() as run:
        mlflow.log_param("threshold_l1", threshold_l1)
        mlflow.log_param("taxonomy_path", taxonomy_path)
        mlflow.log_param("calibration_path", calibration_path or "")
        summary = result["summary"]
        mlflow.log_metric("pass_rate", float(summary["pass_rate"]))
        mlflow.log_metric("avg_l1", float(summary["avg_l1"]))
        mlflow.log_metric("p95_l1", float(summary["p95_l1"]))
        mlflow.log_artifact(str(out_dir / "out.jsonl"))
        mlflow.log_artifact(str(out_dir / "eval_summary.json"))
        mlflow.log_artifact(str(out_dir / "report.html"))
        mlflow.log_artifact(str(out_dir / "receipt.json"))
        return {"enabled": True, "run_id": run.info.run_id}


def _render_eval_report_html(
    *,
    summary: dict[str, Any],
    scored: list[dict[str, Any]],
    threshold_l1: int,
    top_n_failures: int = 10,
) -> str:
    title = html.escape(str(summary.get("run_id", "eval_report")))
    summary_json = json.dumps(summary, ensure_ascii=True)
    rows_json = json.dumps(scored, ensure_ascii=True)
    return (
        "<!doctype html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '<meta charset="utf-8" />\n'
        f"<title>ToneSight Interactive Report - {title}</title>\n"
        "<style>\n"
        ":root { --bg:#0f172a; --panel:#111827; --ink:#e5e7eb; --muted:#94a3b8; --grid:#334155; --accent:#22c55e; }\n"
        "body { font-family: Segoe UI, Arial, sans-serif; margin: 0; background: var(--bg); color: var(--ink); }\n"
        ".wrap { max-width: 1220px; margin: 0 auto; padding: 20px; }\n"
        "h1,h2,h3 { margin: 0 0 10px 0; }\n"
        ".panel { background: var(--panel); border: 1px solid #1f2937; border-radius: 10px; padding: 14px; margin-bottom: 14px; }\n"
        ".kpis { display: grid; grid-template-columns: repeat(auto-fill,minmax(170px,1fr)); gap: 8px; }\n"
        ".kpi { background:#0b1220; border:1px solid #1f2937; border-radius:8px; padding:8px; }\n"
        ".kpi .label { color: var(--muted); font-size: 12px; }\n"
        ".kpi .value { font-weight: 700; font-size: 16px; }\n"
        ".controls { display:flex; flex-wrap:wrap; gap:10px; margin:8px 0 10px 0; align-items:center; }\n"
        "label { color: var(--muted); font-size: 13px; }\n"
        "select,input[type=range],input[type=checkbox] { margin-left: 4px; }\n"
        "canvas { width: 100%; height: 420px; background: #070b14; border: 1px solid #1f2937; border-radius: 8px; }\n"
        ".grid3 { display:grid; grid-template-columns: repeat(3,minmax(0,1fr)); gap:10px; }\n"
        ".grid5 { display:grid; grid-template-columns: repeat(5,minmax(0,1fr)); gap:10px; }\n"
        "svg { width: 100%; height: 180px; background:#070b14; border:1px solid #1f2937; border-radius:8px; }\n"
        ".heatmap { display:grid; grid-template-columns: repeat(8, 1fr); gap:4px; }\n"
        ".cell { text-align:center; font-size:11px; padding:6px 0; border-radius:4px; color:#fff; }\n"
        "table { width: 100%; border-collapse: collapse; }\n"
        "th, td { border: 1px solid #1f2937; padding: 6px; text-align: left; font-size: 12px; }\n"
        "th { background: #0b1220; }\n"
        ".muted { color: var(--muted); }\n"
        "</style>\n"
        "</head>\n"
        "<body>\n"
        '<div class="wrap">\n'
        f"<h1>ToneSight Eval Report (Interactive)</h1><div class=\"muted\">run_id: {title}</div>\n"
        '<div class="panel"><h2>Conformance Context</h2><div class="muted">Pass/fail here measures tone conformance against target bins, not classifier accuracy. This goldset intentionally includes negative anchors to verify failure surfacing and regression sensitivity.</div></div>\n'
        '<div class="panel"><h2>Run Summary</h2><div id="kpis" class="kpis"></div></div>\n'
        '<div class="panel"><h2>3D VAD Explorer</h2>'
        '<div class="controls">'
        '<label>Color by<select id="colorBy"><option value="label">label</option><option value="source">source</option><option value="agent">agent</option><option value="pass">pass</option></select></label>'
        '<label>Max rows<input id="maxRows" type="range" min="1" max="1" value="1" /></label><span id="maxRowsVal" class="muted"></span>'
        '<label>Rotate X<input id="rotX" type="range" min="-90" max="90" value="25" /></label>'
        '<label>Rotate Y<input id="rotY" type="range" min="-180" max="180" value="-35" /></label>'
        '<label><input id="showTrajectory" type="checkbox" checked />Trajectory</label>'
        "</div>"
        '<canvas id="vad3d" width="1100" height="420"></canvas>'
        '<div id="hover" class="muted" style="margin-top:6px;"></div>'
        "</div>\n"
        '<div class="panel"><h2>Drift Over Time</h2><div class="grid5"><svg id="vChart"></svg><svg id="aChart"></svg><svg id="dChart"></svg><svg id="passChart"></svg><svg id="failChart"></svg></div></div>\n'
        '<div class="panel"><h2>8x8 V-A Heatmap</h2><div id="heatmap" class="heatmap"></div><div class="muted" style="margin-top:8px;">Counts of predicted V/A bins from eval output.</div></div>\n'
        '<div class="panel"><h2>Regression Panel</h2><div id="regressionFlags" class="kpis"></div><h3 style="margin-top:10px;">Top Failures</h3><table><thead><tr><th>rank</th><th>id</th><th>label</th><th>L1</th><th>pred_vad</th><th>target_vad</th><th>source</th></tr></thead><tbody id="failRows"></tbody></table></div>\n'
        "</div>\n"
        "<script>\n"
        f"const SUMMARY = {summary_json};\n"
        f"const ROWS = {rows_json};\n"
        "const THRESHOLD = " + str(int(threshold_l1)) + ";\n"
        "const TOP_N_FAIL = " + str(max(0, int(top_n_failures))) + ";\n"
        "const labelOr = (v, d) => (v === null || v === undefined || v === '' ? d : String(v));\n"
        "const pred = (r) => r.pred_vad || {V:0,A:0,D:0};\n"
        "const kpisEl = document.getElementById('kpis');\n"
        "const coverage = { withLabel: ROWS.filter(r => r.label).length, withGold: ROWS.filter(r => r.gold_vad != null).length, labels: new Set(ROWS.filter(r => r.label).map(r => String(r.label))).size };\n"
        "const intentionalNeg = ROWS.filter(r => Array.isArray(r.tags) && (r.tags.includes('negative_anchor') || r.tags.includes('hard_negative'))).length;\n"
        "const l1Vals = ROWS.map(r => Number(r.compliance_l1 || 0));\n"
        "const pct = (arr,p) => { if (!arr.length) return 0; const s=[...arr].sort((a,b)=>a-b); const pos=p*(s.length-1); const lo=Math.floor(pos); const hi=Math.min(lo+1,s.length-1); if (lo===hi) return s[lo]; const frac=pos-lo; return s[lo] + (s[hi]-s[lo])*frac; };\n"
        "const buckets = { b0:0,b13:0,b46:0,b7:0 }; l1Vals.forEach(v=>{ if(v<=0) buckets.b0++; else if(v<=3) buckets.b13++; else if(v<=6) buckets.b46++; else buckets.b7++; });\n"
        "const goldRows = ROWS.filter(r => r.gold_vad && r.pred_vad);\n"
        "const mae = (dim) => goldRows.length ? goldRows.reduce((acc,r)=>acc+Math.abs(Number(r.pred_vad[dim])-Number(r.gold_vad[dim])),0)/goldRows.length : 0;\n"
        "const kpiItems = [\n"
        " ['rows', SUMMARY.count_rows], ['dataset_hash', labelOr(SUMMARY.dataset_hash, '')], ['pass_rate', Number(SUMMARY.pass_rate).toFixed(3)], ['avg_l1', Number(SUMMARY.avg_l1).toFixed(3)], ['p95_l1', Number(SUMMARY.p95_l1).toFixed(3)],\n"
        " ['eval_duration_seconds', Number(SUMMARY.eval_duration_seconds || 0).toFixed(3)], ['intentional_negative_rows', intentionalNeg],\n"
        " ['rows_with_label', `${coverage.withLabel} (${(coverage.withLabel/Math.max(1,ROWS.length)).toFixed(3)})`], ['rows_with_gold_vad', `${coverage.withGold} (${(coverage.withGold/Math.max(1,ROWS.length)).toFixed(3)})`], ['distinct_labels', coverage.labels],\n"
        " ['p50_l1', pct(l1Vals,0.50).toFixed(3)], ['p75_l1', pct(l1Vals,0.75).toFixed(3)], ['p90_l1', pct(l1Vals,0.90).toFixed(3)], ['p99_l1', pct(l1Vals,0.99).toFixed(3)],\n"
        " ['l1_bucket_0', buckets.b0], ['l1_bucket_1_3', buckets.b13], ['l1_bucket_4_6', buckets.b46], ['l1_bucket_7_plus', buckets.b7],\n"
        " ['mae_v_gold', mae('V').toFixed(3)], ['mae_a_gold', mae('A').toFixed(3)], ['mae_d_gold', mae('D').toFixed(3)]\n"
        "];\n"
        "kpiItems.forEach(([k,v]) => { const d=document.createElement('div'); d.className='kpi'; d.innerHTML=`<div class=\"label\">${k}</div><div class=\"value\">${v}</div>`; kpisEl.appendChild(d); });\n"
        "const failRows = [...ROWS].filter(r => !r.pass).sort((a,b)=> (Number(b.compliance_l1)-Number(a.compliance_l1)) || String(a.id).localeCompare(String(b.id))).slice(0, TOP_N_FAIL);\n"
        "const failBody = document.getElementById('failRows');\n"
        "if (!failRows.length) { failBody.innerHTML = '<tr><td colspan=\"7\">No failing rows.</td></tr>'; }\n"
        "else { failRows.forEach((r,i)=>{ const tr=document.createElement('tr'); const pv=pred(r); const tv=r.target_vad||{}; tr.innerHTML=`<td>${i+1}</td><td>${labelOr(r.id,'')}</td><td>${labelOr(r.label,'')}</td><td>${labelOr(r.compliance_l1,'')}</td><td>(${pv.V},${pv.A},${pv.D})</td><td>(${tv.V},${tv.A},${tv.D})</td><td>${labelOr(r.source,'')}</td>`; failBody.appendChild(tr); }); }\n"
        "const flagsEl=document.getElementById('regressionFlags');\n"
        "const flags=[['status_pass_rate', Number(SUMMARY.pass_rate)>=0.8?'ok':'watch'], ['status_p95_l1', Number(SUMMARY.p95_l1)<=THRESHOLD?'ok':'watch'], ['status_fail_count', Number(SUMMARY.fail_count)===0?'ok':'watch']];\n"
        "flags.forEach(([k,v])=>{ const d=document.createElement('div'); d.className='kpi'; d.innerHTML=`<div class=\"label\">${k}</div><div class=\"value\">${v}</div>`; flagsEl.appendChild(d); });\n"
        "const heatEl=document.getElementById('heatmap');\n"
        "const counts=[]; for(let v=1;v<=8;v++){ for(let a=1;a<=8;a++){ counts.push({v,a,n:ROWS.filter(r=>pred(r).V===v && pred(r).A===a).length}); } }\n"
        "const maxN=Math.max(1,...counts.map(c=>c.n));\n"
        "counts.forEach(c=>{ const alpha=0.2 + 0.8*(c.n/maxN); const div=document.createElement('div'); div.className='cell'; div.style.background=`rgba(56,189,248,${alpha.toFixed(3)})`; div.title=`V=${c.v}, A=${c.a}, n=${c.n}`; div.textContent=String(c.n); heatEl.appendChild(div); });\n"
        "const drawLineChart=(svgId, title, vals, color, minV, maxV, targetVals=null)=>{ const svg=document.getElementById(svgId); const W=svg.clientWidth||360, H=svg.clientHeight||180, m=24; const n=Math.max(1,vals.length-1); const x=i=>m+(i/n)*(W-2*m); const y=v=>{ const cl=Math.max(minV, Math.min(maxV, Number(v))); return H-m-((cl-minV)/Math.max(1e-9,(maxV-minV)))*(H-2*m); }; let d=''; vals.forEach((v,i)=>{ d += (i?'L':'M') + x(i) + ' ' + y(v) + ' '; }); let dt=''; if(targetVals){ targetVals.forEach((v,i)=>{ dt += (i?'L':'M') + x(i) + ' ' + y(v) + ' '; }); } svg.innerHTML = `<text x=\"10\" y=\"16\" fill=\"#94a3b8\">${title}</text>${targetVals?`<path d=\"${dt}\" fill=\"none\" stroke=\"#64748b\" stroke-dasharray=\"4 3\" stroke-width=\"1.5\"/>`:''}<path d=\"${d}\" fill=\"none\" stroke=\"${color}\" stroke-width=\"2\"/>`; };\n"
        "const rollingPass=(windowSize)=>{ const out=[]; for(let i=0;i<ROWS.length;i++){ const lo=Math.max(0,i-windowSize+1); const chunk=ROWS.slice(lo,i+1); const p=chunk.filter(r=>r.pass).length/Math.max(1,chunk.length); out.push(p); } return out; };\n"
        "const cumulativeFails=()=>{ let c=0; const out=[]; ROWS.forEach(r=>{ if(!r.pass) c+=1; out.push(c); }); return out; };\n"
        "drawLineChart('vChart','V over row order', ROWS.map(r=>Number(pred(r).V||0)), '#ef4444', 1, 8, ROWS.map(r=>Number((r.target_vad||{}).V||0)));\n"
        "drawLineChart('aChart','A over row order', ROWS.map(r=>Number(pred(r).A||0)), '#22c55e', 1, 8, ROWS.map(r=>Number((r.target_vad||{}).A||0)));\n"
        "drawLineChart('dChart','D over row order', ROWS.map(r=>Number(pred(r).D||0)), '#38bdf8', 1, 8, ROWS.map(r=>Number((r.target_vad||{}).D||0)));\n"
        "drawLineChart('passChart','Rolling pass rate (window=10)', rollingPass(10), '#f59e0b', 0, 1);\n"
        "drawLineChart('failChart','Cumulative failures', cumulativeFails(), '#f43f5e', 0, Math.max(1, ROWS.length));\n"
        "const canvas=document.getElementById('vad3d'); const ctx=canvas.getContext('2d');\n"
        "const maxRowsInput=document.getElementById('maxRows'); maxRowsInput.max=String(Math.max(1,ROWS.length)); maxRowsInput.value=String(Math.max(1,ROWS.length)); document.getElementById('maxRowsVal').textContent=maxRowsInput.value;\n"
        "const colorBy=document.getElementById('colorBy'); const rotX=document.getElementById('rotX'); const rotY=document.getElementById('rotY'); const showTrajectory=document.getElementById('showTrajectory'); const hoverEl=document.getElementById('hover');\n"
        "const hashColor=(s)=>{ let h=0; for(let i=0;i<s.length;i++){ h=((h<<5)-h)+s.charCodeAt(i); h|=0; } const r=(h&255), g=((h>>8)&255), b=((h>>16)&255); return `rgb(${(r+256)%256},${(g+256)%256},${(b+256)%256})`; };\n"
        "const proj=(v,a,d,rx,ry)=>{ let x=(v-4.5), y=(a-4.5), z=(d-4.5); const cx=Math.cos(rx), sx=Math.sin(rx), cy=Math.cos(ry), sy=Math.sin(ry); const y1=y*cx-z*sx; const z1=y*sx+z*cx; const x2=x*cy+z1*sy; const z2=-x*sy+z1*cy; const s=28; return { x: canvas.width/2 + x2*s, y: canvas.height/2 - y1*s, z: z2 }; };\n"
        "const draw3d=()=>{ const limit=Number(maxRowsInput.value); document.getElementById('maxRowsVal').textContent=String(limit); const rows=ROWS.slice(0,limit); ctx.clearRect(0,0,canvas.width,canvas.height); ctx.strokeStyle='#1f2937'; ctx.strokeRect(0,0,canvas.width,canvas.height); const rx=Number(rotX.value)*Math.PI/180, ry=Number(rotY.value)*Math.PI/180; const pts=rows.map((r,i)=>{ const p=pred(r); const q=proj(Number(p.V),Number(p.A),Number(p.D),rx,ry); let key=''; if(colorBy.value==='label') key=labelOr(r.label,'(none)'); else if(colorBy.value==='source') key=labelOr(r.source,'(none)'); else if(colorBy.value==='agent') key=labelOr(r.agent,'(none)'); else key=r.pass?'pass':'fail'; return {i, r, ...q, c: colorBy.value==='pass' ? (r.pass?'#22c55e':'#ef4444') : hashColor(key)}; }).sort((a,b)=>a.z-b.z);\n"
        "if (showTrajectory.checked){ ctx.strokeStyle='rgba(148,163,184,0.45)'; ctx.beginPath(); pts.forEach((p,idx)=>{ if(idx===0) ctx.moveTo(p.x,p.y); else ctx.lineTo(p.x,p.y); }); ctx.stroke(); }\n"
        "pts.forEach(p=>{ ctx.fillStyle=p.c; ctx.beginPath(); ctx.arc(p.x,p.y,4.5,0,Math.PI*2); ctx.fill(); });\n"
        "canvas.onmousemove=(ev)=>{ const rect=canvas.getBoundingClientRect(); const mx=(ev.clientX-rect.left)*(canvas.width/rect.width); const my=(ev.clientY-rect.top)*(canvas.height/rect.height); let best=null, bestD=1e9; pts.forEach(p=>{ const d2=(p.x-mx)*(p.x-mx)+(p.y-my)*(p.y-my); if(d2<bestD){ bestD=d2; best=p; } }); if(best && bestD<120){ const pv=pred(best.r); hoverEl.textContent=`id=${labelOr(best.r.id,'')} label=${labelOr(best.r.label,'')} source=${labelOr(best.r.source,'')} agent=${labelOr(best.r.agent,'')} ts=${labelOr(best.r.timestamp,'')} VAD=(${pv.V},${pv.A},${pv.D}) L1=${labelOr(best.r.compliance_l1,'')}`; } else { hoverEl.textContent=''; } };\n"
        "};\n"
        "[maxRowsInput,colorBy,rotX,rotY,showTrajectory].forEach(el=>el.addEventListener('input',draw3d));\n"
        "draw3d();\n"
        "</script>\n"
        "</body>\n"
        "</html>\n"
    )


def run_eval(
    goldset_path: str,
    *,
    out_root: str = EVAL_DEFAULTS["out_root"],
    taxonomy_path: str = EVAL_DEFAULTS["taxonomy_path"],
    threshold_l1: int = EVAL_DEFAULTS["threshold_l1"],
    calibration_path: str | None = EVAL_DEFAULTS["calibration_path"],
    capture_gpu: bool = EVAL_DEFAULTS["capture_gpu"],
    mlflow_tracking_uri: str | None = EVAL_DEFAULTS["mlflow_tracking_uri"],
) -> dict[str, Any]:
    """Run deterministic eval and write out.jsonl, eval_summary.json, report.html, receipt.json."""
    started_utc = datetime.now(timezone.utc)
    started_perf = time.perf_counter()
    gpath = Path(goldset_path)
    rows = _read_jsonl(gpath)
    taxonomy = load_taxonomy(taxonomy_path)
    calibration = _load_calibration(calibration_path)

    d_hash = _dataset_hash(gpath)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    run_id = f"run_{ts}_{d_hash}"

    out_dir = Path(out_root) / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    gpu_before = _gpu_snapshot() if capture_gpu else None

    scored: list[dict[str, Any]] = []
    compliance_l1_values: list[float] = []
    accuracy_l1_values: list[float] = []
    pass_count = 0

    for row in rows:
        target = row["target_vad"]
        target_vad = (int(target["V"]), int(target["A"]), int(target["D"]))

        label = row.get("label")
        if label:
            pred_vad = calibration.get(str(label), get_vad(label, taxonomy))
        elif row.get("gold_vad"):
            g = row["gold_vad"]
            pred_vad = (int(g["V"]), int(g["A"]), int(g["D"]))
        else:
            pred_vad = target_vad

        c_l1 = _l1(pred_vad, target_vad)
        passed = c_l1 <= threshold_l1
        pass_count += 1 if passed else 0
        compliance_l1_values.append(float(c_l1))

        a_l1 = None
        if row.get("gold_vad"):
            g = row["gold_vad"]
            gold_vad = (int(g["V"]), int(g["A"]), int(g["D"]))
            a_l1 = _l1(pred_vad, gold_vad)
            accuracy_l1_values.append(float(a_l1))

        scored.append(
            {
                "id": row.get("id"),
                "label": label,
                "source": row.get("source"),
                "agent": row.get("agent"),
                "timestamp": row.get("timestamp"),
                "text": row.get("text"),
                "tags": row.get("tags"),
                "target_vad": {"V": target_vad[0], "A": target_vad[1], "D": target_vad[2]},
                "pred_vad": {"V": pred_vad[0], "A": pred_vad[1], "D": pred_vad[2]},
                "gold_vad": row.get("gold_vad"),
                "compliance_l1": c_l1,
                "accuracy_l1": a_l1,
                "pass": passed,
            }
        )

    total = len(scored)
    eval_duration_seconds = time.perf_counter() - started_perf
    completed_utc = datetime.now(timezone.utc)
    summary = {
        "run_id": run_id,
        "dataset_hash": d_hash,
        "count_rows": total,
        "threshold_l1": threshold_l1,
        "pass_count": pass_count,
        "fail_count": total - pass_count,
        "pass_rate": (pass_count / total) if total else 0.0,
        "fail_rate": ((total - pass_count) / total) if total else 0.0,
        "avg_l1": (sum(compliance_l1_values) / total) if total else 0.0,
        "median_l1": _median(compliance_l1_values),
        "p95_l1": _p95(compliance_l1_values),
        "max_l1": max(compliance_l1_values) if compliance_l1_values else 0.0,
        "count_with_gold_vad": len(accuracy_l1_values),
        "count_without_gold_vad": total - len(accuracy_l1_values),
        "avg_accuracy_l1": (sum(accuracy_l1_values) / len(accuracy_l1_values)) if accuracy_l1_values else None,
        "eval_duration_seconds": eval_duration_seconds,
    }

    receipt = {
        "spec_version": "1.0",
        "run_id": run_id,
        "dataset_path": str(gpath),
        "dataset_hash": d_hash,
        "row_count": total,
        "config": {
            "threshold_l1": threshold_l1,
            "taxonomy_path": taxonomy_path,
            "calibration_path": calibration_path,
            "capture_gpu": capture_gpu,
            "mlflow_tracking_uri": mlflow_tracking_uri,
        },
        "artifacts": {
            "out_jsonl": str(out_dir / "out.jsonl"),
            "eval_summary_json": str(out_dir / "eval_summary.json"),
            "report_html": str(out_dir / "report.html"),
            "receipt_json": str(out_dir / "receipt.json"),
        },
        "created_at_utc": completed_utc.isoformat(),
        "runtime": {
            "started_at_utc": started_utc.isoformat(),
            "completed_at_utc": completed_utc.isoformat(),
            "eval_duration_seconds": eval_duration_seconds,
            "python_version": platform.python_version(),
            "platform": platform.platform(),
        },
    }
    if gpu_before is not None:
        receipt["artifacts"]["gpu_before_json"] = str(out_dir / "gpu_before.json")

    _write_jsonl(out_dir / "out.jsonl", scored)
    (out_dir / "eval_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    (out_dir / "report.html").write_text(
        _render_eval_report_html(summary=summary, scored=scored, threshold_l1=threshold_l1),
        encoding="utf-8",
    )
    if gpu_before is not None:
        (out_dir / "gpu_before.json").write_text(json.dumps(gpu_before, indent=2) + "\n", encoding="utf-8")
        gpu_after = _gpu_snapshot()
        (out_dir / "gpu_after.json").write_text(json.dumps(gpu_after, indent=2) + "\n", encoding="utf-8")
        receipt["artifacts"]["gpu_after_json"] = str(out_dir / "gpu_after.json")

    mlflow_info = _maybe_log_mlflow(
        tracking_uri=mlflow_tracking_uri,
        result={"summary": summary},
        out_dir=out_dir,
        threshold_l1=threshold_l1,
        taxonomy_path=taxonomy_path,
        calibration_path=calibration_path,
    )
    if mlflow_info is not None:
        receipt["mlflow"] = mlflow_info

    (out_dir / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")

    return {
        "run_id": run_id,
        "out_dir": str(out_dir),
        "summary": summary,
        "receipt": receipt,
    }
