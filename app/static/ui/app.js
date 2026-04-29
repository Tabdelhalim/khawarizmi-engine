/**
 * Khawarizmi Engine – Stata-style UI
 *
 * Panels: History (left) | Data Editor + Results (center) | Variables + Properties (right)
 * Command bar at bottom; typing Stata-like commands calls the backend.
 */

"use strict";

/* ─── State ────────────────────────────────────────────────────────────── */
const state = {
  name: "",
  headers: [],
  rows: [],
  history: [],     // [{cmd, rc}]
  historyIdx: -1,  // for arrow-up recall
  selectedVar: null,
};

/* ─── Sample data ──────────────────────────────────────────────────────── */
const SAMPLE_CSV = `date,gdp,cpi,unemp,interest,m2,exports,imports
2000q1,2143.2,88.7,8.6,6.12,10234,245.3,302.1
2000q2,2180.7,89.1,8.3,6.00,10421,246.7,305.8
2000q3,2216.4,89.6,8.1,5.88,10615,248.9,308.7
2000q4,2241.1,90.2,7.9,5.75,10832,249.5,311.2
2001q1,2278.6,90.9,7.8,5.50,11021,250.1,315.6
2001q2,2316.9,91.4,7.6,5.25,11220,251.4,318.9
2001q3,2355.7,91.9,7.4,5.00,11431,252.7,322.3
2001q4,2388.6,92.5,7.3,4.75,11641,254.2,325.7
2002q1,2422.1,93.2,7.2,4.50,11852,255.1,329.6
2002q2,2461.8,93.8,7.1,4.38,12085,256.4,332.1
2002q3,2501.2,94.3,6.9,4.25,12324,257.9,335.4
2002q4,2540.5,94.9,6.8,4.12,12566,259.3,338.9
2003q1,2581.3,95.5,6.7,4.00,12810,260.8,342.4
2003q2,2622.8,96.1,6.6,3.88,13061,262.4,346.1
2003q3,2665.4,96.8,6.5,3.75,13319,264.1,349.9
2003q4,2709.6,97.4,6.4,3.62,13583,265.9,353.8
2004q1,2754.6,98.1,6.3,3.50,13854,267.8,357.9
2004q2,2801.2,98.9,6.2,3.62,14132,269.8,362.1
2004q3,2849.6,99.6,6.1,3.75,14416,271.9,366.5
2004q4,2899.9,100.4,6.0,3.88,14707,274.1,371.0
`;

/* ─── CSV parser ───────────────────────────────────────────────────────── */
function parseCsv(text) {
  const lines = text.replace(/\r/g, "").split("\n").filter((l) => l.trim());
  if (!lines.length) return { headers: [], rows: [] };

  const split = (line) => {
    const out = [];
    let cur = "";
    let inQ = false;
    for (let i = 0; i < line.length; i++) {
      const c = line[i];
      if (c === '"') { inQ = !inQ; continue; }
      if (c === "," && !inQ) { out.push(cur.trim()); cur = ""; continue; }
      cur += c;
    }
    out.push(cur.trim());
    return out;
  };

  const rows = lines.map(split);
  const first = rows[0];
  const hasHeader = first.every((c) => /[a-zA-Z]/.test(c));
  if (hasHeader) return { headers: first, rows: rows.slice(1) };
  return { headers: first.map((_, i) => `var${i + 1}`), rows };
}

function isNumericCol(colIdx) {
  const sample = state.rows.slice(0, 20).map((r) => r[colIdx]);
  const nums = sample.filter((v) => v !== undefined && /^-?\d+(\.\d+)?$/.test(v.trim()));
  return nums.length / Math.max(sample.length, 1) >= 0.8;
}

function colValues(colName) {
  const idx = state.headers.indexOf(colName);
  if (idx < 0) return null;
  return state.rows.map((r) => r[idx]).filter((v) => /^-?\d+(\.\d+)?$/.test((v || "").trim())).map(Number);
}

/* ─── Render: Data Editor ──────────────────────────────────────────────── */
function renderDataEditor() {
  const thead = document.querySelector("#dataTable thead tr");
  const tbody = document.querySelector("#dataTable tbody");

  thead.innerHTML = "<th>#</th>";
  state.headers.forEach((h) => {
    const th = document.createElement("th");
    th.textContent = h;
    thead.appendChild(th);
  });

  tbody.innerHTML = "";
  const MAX_ROWS = 200;
  state.rows.slice(0, MAX_ROWS).forEach((row, ri) => {
    const tr = document.createElement("tr");
    const idx = document.createElement("td");
    idx.textContent = String(ri + 1);
    tr.appendChild(idx);
    state.headers.forEach((_, ci) => {
      const td = document.createElement("td");
      td.textContent = row[ci] !== undefined ? row[ci] : "";
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });

  document.getElementById("dataStats").textContent =
    `${state.rows.length} obs  ${state.headers.length} vars`;
}

/* ─── Render: Variables panel ──────────────────────────────────────────── */
function renderVars() {
  const tbody = document.querySelector("#varsTable tbody");
  tbody.innerHTML = "";
  state.headers.forEach((h, ci) => {
    const tr = document.createElement("tr");
    tr.dataset.col = ci;

    const tdName = document.createElement("td");
    tdName.textContent = h;
    const tdType = document.createElement("td");
    tdType.textContent = isNumericCol(ci) ? "float" : "str";
    const tdLabel = document.createElement("td");
    tdLabel.textContent = h.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());

    tr.append(tdName, tdType, tdLabel);

    tr.addEventListener("click", () => {
      document.querySelectorAll("#varsTable tr").forEach((r) => r.querySelectorAll("td").forEach((t) => t.classList.remove("sel")));
      tr.querySelectorAll("td").forEach((t) => t.classList.add("sel"));
      state.selectedVar = h;
      updateProps();
    });

    tbody.appendChild(tr);
  });
}

/* ─── Render: Properties panel ─────────────────────────────────────────── */
function updateProps() {
  document.getElementById("pDataset").textContent = state.name || "–";
  document.getElementById("pObs").textContent = state.rows.length || "–";
  document.getElementById("pVars").textContent = state.headers.length || "–";
  document.getElementById("pSelected").textContent = state.selectedVar || "–";

  if (state.selectedVar) {
    const ci = state.headers.indexOf(state.selectedVar);
    document.getElementById("pType").textContent = isNumericCol(ci) ? "float" : "str";
    const vals = colValues(state.selectedVar);
    if (vals && vals.length) {
      const mn = Math.min(...vals).toFixed(3);
      const mx = Math.max(...vals).toFixed(3);
      document.getElementById("pRange").textContent = `${mn} – ${mx}`;
    } else {
      document.getElementById("pRange").textContent = "–";
    }
  } else {
    document.getElementById("pType").textContent = "–";
    document.getElementById("pRange").textContent = "–";
  }
}

/* ─── Render: Status bar ───────────────────────────────────────────────── */
function updateStatus(msg) {
  document.getElementById("sbLeft").textContent = msg || (state.name ? `Dataset: ${state.name}` : "No data loaded");
}

/* ─── Results window helpers ───────────────────────────────────────────── */
function appendResults(text) {
  const el = document.getElementById("resultsOut");
  el.textContent += "\n" + text;
  el.parentElement.scrollTop = el.parentElement.scrollHeight;
}

function clearResults() {
  document.getElementById("resultsOut").textContent = "";
}

function echoCmd(cmd) {
  appendResults(`. ${cmd}`);
}

/* ─── History panel ────────────────────────────────────────────────────── */
function addHistory(cmd, rc) {
  state.history.push({ cmd, rc });
  const li = document.createElement("li");
  li.textContent = cmd;
  li.title = `rc=${rc}`;
  li.style.color = rc === 0 ? "#003399" : "#990000";
  li.addEventListener("click", () => {
    document.getElementById("cmdInput").value = cmd;
    document.getElementById("cmdInput").focus();
  });
  const ul = document.getElementById("historyList");
  ul.appendChild(li);
  ul.scrollTop = ul.scrollHeight;
}

/* ─── Load dataset ─────────────────────────────────────────────────────── */
function loadData(csvText, filename) {
  const { headers, rows } = parseCsv(csvText);
  state.headers = headers;
  state.rows = rows;
  state.name = filename || "dataset.csv";
  state.selectedVar = headers[0] || null;
  renderDataEditor();
  renderVars();
  updateProps();
  updateStatus(`Dataset: ${state.name}`);
  document.getElementById("sbRight").textContent = `${rows.length} obs, ${headers.length} vars`;
  appendResults(`\n. use "${state.name}"\n(${rows.length} observations, ${headers.length} variables)\n`);
}

/* ═══════════════════════════════════════════════════════════════════════
   COMMAND PARSER
   ═══════════════════════════════════════════════════════════════════════ */

async function runCommand(raw) {
  const cmd = raw.trim();
  if (!cmd) return;

  echoCmd(cmd);
  addHistory(cmd, 0);
  updateStatus(`Running: ${cmd}`);

  try {
    await dispatch(cmd);
  } catch (err) {
    appendResults(`(error) ${err.message}`);
    addHistory(cmd, 1);
  }

  updateStatus();
}

async function dispatch(cmd) {
  const lower = cmd.toLowerCase();
  const tokens = cmd.trim().split(/\s+/);
  const verb = tokens[0].toLowerCase();

  /* ── describe ─────────────────────────────────────────────────── */
  if (verb === "describe" || verb === "desc") {
    return cmdDescribe();
  }

  /* ── summarize ────────────────────────────────────────────────── */
  if (verb === "summarize" || verb === "sum") {
    const varName = tokens[1] || null;
    return cmdSummarize(varName);
  }

  /* ── clear ────────────────────────────────────────────────────── */
  if (verb === "clear") {
    clearResults();
    return;
  }

  /* ── help ─────────────────────────────────────────────────────── */
  if (verb === "help") {
    return cmdHelp();
  }

  /* ── adf varname ──────────────────────────────────────────────── */
  if (verb === "adf") {
    const varName = tokens[1];
    if (!varName) { appendResults("Usage: adf varname"); return; }
    return cmdAdf(varName);
  }

  /* ── acf varname [, lags(N)] ──────────────────────────────────── */
  if (verb === "acf") {
    const varName = tokens[1];
    if (!varName) { appendResults("Usage: acf varname"); return; }
    const lagsMatch = lower.match(/lags\((\d+)\)/);
    const nLags = lagsMatch ? parseInt(lagsMatch[1], 10) : 20;
    return cmdAcf(varName, nLags);
  }

  /* ── arima varname [, arima(p,d,q)] ──────────────────────────── */
  if (verb === "arima") {
    const varName = tokens[1];
    if (!varName) { appendResults("Usage: arima varname [, arima(p,d,q)]"); return; }
    const orderMatch = lower.match(/arima\((\d+),(\d+),(\d+)\)/);
    if (orderMatch) {
      const p = parseInt(orderMatch[1], 10);
      const d = parseInt(orderMatch[2], 10);
      const q = parseInt(orderMatch[3], 10);
      return cmdArimaFit(varName, p, d, q);
    }
    return cmdAutoArima(varName);
  }

  /* ── auto_arima varname ───────────────────────────────────────── */
  if (verb === "auto_arima" || verb === "auto-arima") {
    const varName = tokens[1] || state.headers.find((h) => isNumericCol(state.headers.indexOf(h))) || null;
    if (!varName) { appendResults("Usage: auto_arima varname"); return; }
    return cmdAutoArima(varName);
  }

  /* ── reg depvar [indepvars] ───────────────────────────────────── */
  if (verb === "reg" || verb === "regress") {
    appendResults(
      "\n  reg: OLS regression is not yet implemented in the backend.\n" +
      "  Use 'arima', 'adf', 'acf', or 'summarize' for now.\n"
    );
    return;
  }

  appendResults(`unrecognized command: ${tokens[0]}`);
}

/* ─── describe ─────────────────────────────────────────────────────────── */
function cmdDescribe() {
  if (!state.headers.length) { appendResults("No data in memory."); return; }

  const lines = [
    "",
    `  Contains data from ${state.name}`,
    `  obs:         ${String(state.rows.length).padStart(10)}`,
    `  vars:        ${String(state.headers.length).padStart(10)}`,
    "",
    `  ${"Variable".padEnd(18)} ${"Type".padEnd(8)} ${"Label"}`,
    "  " + "-".repeat(54),
  ];

  state.headers.forEach((h, ci) => {
    const type = isNumericCol(ci) ? "float" : "str";
    const label = h.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
    lines.push(`  ${h.padEnd(18)} ${type.padEnd(8)} ${label}`);
  });

  appendResults(lines.join("\n") + "\n");
}

/* ─── summarize ────────────────────────────────────────────────────────── */
function cmdSummarize(varName) {
  if (!state.headers.length) { appendResults("No data in memory."); return; }

  const targets = varName
    ? [varName]
    : state.headers.filter((h, ci) => isNumericCol(ci));

  const header = [
    "",
    `    ${"Variable".padEnd(14)} ${"Obs".padStart(8)} ${"Mean".padStart(12)} ${"Std. Dev.".padStart(12)} ${"Min".padStart(10)} ${"Max".padStart(10)}`,
    "    " + "-".repeat(72),
  ];

  const rows = [];
  for (const h of targets) {
    const vals = colValues(h);
    if (!vals || !vals.length) { rows.push(`    ${h.padEnd(14)} (non-numeric)`); continue; }
    const n = vals.length;
    const mean = vals.reduce((a, b) => a + b, 0) / n;
    const variance = vals.reduce((a, b) => a + (b - mean) ** 2, 0) / (n - 1);
    const std = Math.sqrt(variance);
    const min = Math.min(...vals);
    const max = Math.max(...vals);
    rows.push(
      `    ${h.padEnd(14)} ${String(n).padStart(8)} ${mean.toFixed(4).padStart(12)} ${std.toFixed(4).padStart(12)} ${min.toFixed(3).padStart(10)} ${max.toFixed(3).padStart(10)}`
    );
  }

  appendResults([...header, ...rows, ""].join("\n"));
}

/* ─── help ─────────────────────────────────────────────────────────────── */
function cmdHelp() {
  appendResults(`
  Khawarizmi Engine – Command Reference
  ────────────────────────────────────────────────────────────
  describe                  describe dataset (obs, vars, types)
  summarize [varname]       summary statistics
  arima varname             auto-select best ARIMA(p,d,q)
  arima varname, arima(p,d,q)  fit a specific ARIMA model
  auto_arima varname        alias for arima (auto selection)
  adf varname               Augmented Dickey-Fuller unit-root test
  acf varname [, lags(N)]   ACF and PACF table
  reg y x1 x2               (OLS – planned)
  clear                     clear results window
  help                      show this help
  ────────────────────────────────────────────────────────────
`);
}

/* ─── ADF test ─────────────────────────────────────────────────────────── */
async function cmdAdf(varName) {
  const vals = colValues(varName);
  if (!vals) { appendResults(`Variable '${varName}' not found or not numeric.`); return; }
  if (vals.length < 10) { appendResults(`Too few observations for ADF.`); return; }

  appendResults(`\n  Augmented Dickey-Fuller test for unit root: ${varName}\n  Running…`);

  const resp = await fetch("/api/v1/diagnostics/adf", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ values: vals }),
  });

  if (!resp.ok) { appendResults(`  (HTTP ${resp.status}) ${await resp.text()}`); return; }
  const d = await resp.json();

  appendResults(
    [
      "",
      `  Dickey-Fuller = ${d.test_statistic.toFixed(4)}`,
      `  p-value       = ${d.p_value.toFixed(4)}`,
      `  Lags used     = ${d.n_lags_used}`,
      `  n obs         = ${d.n_obs}`,
      "",
      "  Critical values:",
      ...Object.entries(d.critical_values).map(([k, v]) => `    ${k}: ${v.toFixed(3)}`),
      "",
      d.is_stationary
        ? "  Conclusion: reject unit root => series is STATIONARY (p < 0.05)"
        : "  Conclusion: cannot reject unit root => series may be NON-STATIONARY",
      "",
    ].join("\n")
  );
}

/* ─── ACF / PACF ───────────────────────────────────────────────────────── */
async function cmdAcf(varName, nLags) {
  const vals = colValues(varName);
  if (!vals) { appendResults(`Variable '${varName}' not found or not numeric.`); return; }
  if (vals.length < 10) { appendResults(`Too few observations for ACF.`); return; }

  appendResults(`\n  ACF / PACF for ${varName}  (lags = ${nLags})\n  Running…`);

  const resp = await fetch("/api/v1/diagnostics/acf-pacf", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ values: vals, n_lags: nLags, alpha: 0.05 }),
  });

  if (!resp.ok) { appendResults(`  (HTTP ${resp.status}) ${await resp.text()}`); return; }
  const d = await resp.json();

  const header = [
    "",
    `  ${"Lag".padStart(5)} ${"ACF".padStart(10)} ${"PACF".padStart(10)} ${"[95% CI ACF]".padEnd(22)}`,
    "  " + "-".repeat(52),
  ];
  const rows = d.lags.slice(1).map((lag, i) => {
    const j = i + 1;
    const acf = d.acf[j].toFixed(4).padStart(10);
    const pacf = d.pacf[j].toFixed(4).padStart(10);
    const lo = d.acf_confint_lower[j].toFixed(3);
    const hi = d.acf_confint_upper[j].toFixed(3);
    return `  ${String(lag).padStart(5)} ${acf} ${pacf}  [${lo}, ${hi}]`;
  });

  appendResults([...header, ...rows.slice(0, 20), ""].join("\n"));
}

/* ─── Auto-ARIMA ───────────────────────────────────────────────────────── */
async function cmdAutoArima(varName) {
  const vals = colValues(varName);
  if (!vals) { appendResults(`Variable '${varName}' not found or not numeric.`); return; }
  if (vals.length < 10) { appendResults(`Too few observations for ARIMA.`); return; }

  appendResults(`\n  auto_arima ${varName}\n  Searching for best ARIMA(p,d,q)… (this may take a moment)`);

  const resp = await fetch("/api/v1/auto-arima", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      data: { values: vals },
      max_p: 5, max_d: 2, max_q: 5,
      seasonal: false,
      information_criterion: "aic",
      steps: 8,
      alpha: 0.05,
    }),
  });

  if (!resp.ok) { appendResults(`  (HTTP ${resp.status}) ${await resp.text()}`); return; }
  const d = await resp.json();
  formatArimaOutput(d, varName);
}

/* ─── ARIMA fit ────────────────────────────────────────────────────────── */
async function cmdArimaFit(varName, p, d, q) {
  const vals = colValues(varName);
  if (!vals) { appendResults(`Variable '${varName}' not found or not numeric.`); return; }
  if (vals.length < 10) { appendResults(`Too few observations.`); return; }

  appendResults(`\n  arima ${varName}, arima(${p},${d},${q})\n  Fitting ARIMA(${p},${d},${q})…`);

  const resp = await fetch("/api/v1/arima/fit", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      data: { values: vals },
      order: { p, d, q },
      trend: "n",
    }),
  });

  if (!resp.ok) { appendResults(`  (HTTP ${resp.status}) ${await resp.text()}`); return; }
  const data = await resp.json();
  formatFitOutput(data, varName, p, d, q);
}

/* ─── Output formatters ────────────────────────────────────────────────── */
function formatArimaOutput(d, varName) {
  const s = d.summary;
  const order = d.best_order || "auto";
  const lines = [
    "",
    `  ARIMA model for: ${varName}  (order selected: ${order})`,
    "  " + "─".repeat(58),
    `  ${"Parameter".padEnd(20)} ${"Coef.".padStart(10)} ${"Std. Err.".padStart(12)} ${"P>|z|".padStart(8)}`,
    "  " + "-".repeat(54),
  ];

  Object.entries(s.params).forEach(([k, v]) => {
    const se = s.std_errors[k] !== undefined ? s.std_errors[k].toFixed(4) : "N/A";
    const pv = s.p_values[k] !== undefined ? s.p_values[k].toFixed(4) : "N/A";
    const sig = s.p_values[k] !== undefined && s.p_values[k] < 0.05 ? " *" : "  ";
    lines.push(`  ${k.padEnd(20)} ${v.toFixed(4).padStart(10)} ${se.padStart(12)} ${pv.padStart(8)}${sig}`);
  });

  lines.push(
    "  " + "-".repeat(54),
    `  AIC = ${s.aic.toFixed(4)}    BIC = ${s.bic.toFixed(4)}    HQIC = ${s.hqic.toFixed(4)}`,
    `  Log-likelihood = ${s.log_likelihood.toFixed(4)}    N = ${s.n_obs}`,
    ""
  );

  if (d.forecast && d.forecast.length) {
    lines.push("  Forecasts:");
    lines.push(`  ${"Step".padStart(5)} ${"Forecast".padStart(12)} ${"Lower 95%".padStart(12)} ${"Upper 95%".padStart(12)}`);
    lines.push("  " + "-".repeat(44));
    d.forecast.forEach((f) => {
      lines.push(`  ${String(f.step).padStart(5)} ${f.forecast.toFixed(4).padStart(12)} ${f.lower_ci.toFixed(4).padStart(12)} ${f.upper_ci.toFixed(4).padStart(12)}`);
    });
  }

  appendResults(lines.join("\n") + "\n");
}

function formatFitOutput(data, varName, p, d, q) {
  const s = data.summary;
  const lines = [
    "",
    `  ARIMA(${p},${d},${q}) – ${varName}`,
    "  " + "─".repeat(58),
    `  ${"Parameter".padEnd(20)} ${"Coef.".padStart(10)} ${"Std. Err.".padStart(12)} ${"P>|z|".padStart(8)}`,
    "  " + "-".repeat(54),
  ];

  Object.entries(s.params).forEach(([k, v]) => {
    const se = s.std_errors[k] !== undefined ? s.std_errors[k].toFixed(4) : "N/A";
    const pv = s.p_values[k] !== undefined ? s.p_values[k].toFixed(4) : "N/A";
    const sig = s.p_values[k] !== undefined && s.p_values[k] < 0.05 ? " *" : "  ";
    lines.push(`  ${k.padEnd(20)} ${v.toFixed(4).padStart(10)} ${se.padStart(12)} ${pv.padStart(8)}${sig}`);
  });

  lines.push(
    "  " + "-".repeat(54),
    `  AIC = ${s.aic.toFixed(4)}    BIC = ${s.bic.toFixed(4)}    HQIC = ${s.hqic.toFixed(4)}`,
    `  Log-likelihood = ${s.log_likelihood.toFixed(4)}    N = ${s.n_obs}`,
    ""
  );
  appendResults(lines.join("\n") + "\n");
}

/* ═══════════════════════════════════════════════════════════════════════
   EVENT WIRING
   ═══════════════════════════════════════════════════════════════════════ */

function init() {
  /* File upload */
  document.getElementById("fileInput").addEventListener("change", (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => loadData(String(reader.result), file.name);
    reader.readAsText(file);
  });

  /* Toolbar buttons */
  document.getElementById("btnSample").addEventListener("click", () => {
    loadData(SAMPLE_CSV, "macro_data.csv");
  });

  document.getElementById("btnSummarize").addEventListener("click", () => {
    runCommand("summarize");
  });

  document.getElementById("btnDescribe").addEventListener("click", () => {
    runCommand("describe");
  });

  document.getElementById("btnAutoArima").addEventListener("click", () => {
    const varName = state.selectedVar || state.headers.find((h, i) => isNumericCol(i));
    if (!varName) { appendResults("Load data first."); return; }
    runCommand(`auto_arima ${varName}`);
  });

  document.getElementById("btnClear").addEventListener("click", () => {
    clearResults();
  });

  /* Command input: Enter to run, Arrow-Up to recall */
  const cmdInput = document.getElementById("cmdInput");
  cmdInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      const cmd = cmdInput.value.trim();
      cmdInput.value = "";
      state.historyIdx = -1;
      runCommand(cmd);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      const list = state.history;
      if (!list.length) return;
      state.historyIdx = state.historyIdx < list.length - 1 ? state.historyIdx + 1 : list.length - 1;
      cmdInput.value = list[list.length - 1 - state.historyIdx].cmd;
    } else if (e.key === "ArrowDown") {
      e.preventDefault();
      if (state.historyIdx <= 0) { state.historyIdx = -1; cmdInput.value = ""; return; }
      state.historyIdx--;
      cmdInput.value = state.history[state.history.length - 1 - state.historyIdx].cmd;
    }
  });

  /* Auto-focus command input on load */
  cmdInput.focus();
}

document.addEventListener("DOMContentLoaded", init);
