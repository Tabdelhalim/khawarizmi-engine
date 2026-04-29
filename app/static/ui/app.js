const state = {
  name: "macro_data.dta",
  label: "Macroeconomic Quarterly Data",
  headers: [],
  rows: [],
  history: [],
};

const sampleCsv = `date,gdp,cpi,unemp,interest,m2,exports,imports
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
`;

const isNumeric = (value) => /^-?\d+(\.\d+)?$/.test(value.trim());

const splitCsvLine = (line) => {
  const values = [];
  let current = "";
  let inQuotes = false;

  for (let i = 0; i < line.length; i += 1) {
    const char = line[i];
    if (char === '"') {
      if (inQuotes && line[i + 1] === '"') {
        current += '"';
        i += 1;
      } else {
        inQuotes = !inQuotes;
      }
    } else if (char === "," && !inQuotes) {
      values.push(current.trim());
      current = "";
    } else {
      current += char;
    }
  }
  values.push(current.trim());
  return values;
};

const parseCsv = (csvText) => {
  const lines = csvText
    .replace(/\r/g, "")
    .split("\n")
    .filter((line) => line.trim().length > 0);

  if (!lines.length) {
    return { headers: [], rows: [] };
  }

  const parsed = lines.map(splitCsvLine);
  const firstRow = parsed[0];
  const looksLikeHeader = firstRow.every(
    (cell) => /[a-zA-Z]/.test(cell) && !/^\d/.test(cell.trim()),
  );

  let headers = [];
  let rows = [];
  if (looksLikeHeader) {
    headers = firstRow;
    rows = parsed.slice(1);
  } else {
    headers = firstRow.map((_, index) => `var_${index + 1}`);
    rows = parsed;
  }

  return { headers, rows };
};

const renderDataGrid = () => {
  const grid = document.getElementById("dataGrid");
  const table = document.createElement("table");
  const thead = document.createElement("thead");
  const headerRow = document.createElement("tr");

  const rowHeader = document.createElement("th");
  rowHeader.textContent = "#";
  headerRow.appendChild(rowHeader);

  state.headers.forEach((header) => {
    const th = document.createElement("th");
    th.textContent = header;
    headerRow.appendChild(th);
  });

  thead.appendChild(headerRow);
  table.appendChild(thead);

  const tbody = document.createElement("tbody");
  const maxRows = 20;
  state.rows.slice(0, maxRows).forEach((row, rowIndex) => {
    const tr = document.createElement("tr");
    const indexCell = document.createElement("td");
    indexCell.textContent = String(rowIndex + 1);
    tr.appendChild(indexCell);

    state.headers.forEach((_, colIndex) => {
      const td = document.createElement("td");
      td.textContent = row[colIndex] ?? "";
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });

  table.appendChild(tbody);
  grid.innerHTML = "";
  grid.appendChild(table);
};

const toTitleCase = (value) =>
  value
    .replace(/_/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());

const columnStats = (index) => {
  const values = state.rows.map((row) => row[index]).filter((val) => val !== undefined);
  const numericValues = values.filter((val) => isNumeric(val));
  const ratio = values.length ? numericValues.length / values.length : 0;
  const numeric = ratio >= 0.8;
  if (!numeric) {
    return { type: "str", format: "" };
  }
  const hasFloat = numericValues.some((val) => val.includes("."));
  return {
    type: hasFloat ? "float" : "int",
    format: hasFloat ? "%9.2f" : "%9.0f",
  };
};

const renderVariables = () => {
  const tableBody = document.querySelector("#variablesTable tbody");
  tableBody.innerHTML = "";
  state.headers.forEach((header, index) => {
    const { type, format } = columnStats(index);
    const row = document.createElement("tr");

    const checkCell = document.createElement("td");
    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.checked = type !== "str";
    checkCell.appendChild(checkbox);

    const nameCell = document.createElement("td");
    nameCell.textContent = header;

    const labelCell = document.createElement("td");
    labelCell.textContent = toTitleCase(header);

    const typeCell = document.createElement("td");
    typeCell.textContent = type;

    const formatCell = document.createElement("td");
    formatCell.textContent = format;

    row.append(checkCell, nameCell, labelCell, typeCell, formatCell);
    tableBody.appendChild(row);
  });
};

const updateProperties = () => {
  const obs = state.rows.length;
  const vars = state.headers.length;
  const sizeKb = Math.round((obs * vars * 8) / 1024);

  document.getElementById("propName").textContent = state.name;
  document.getElementById("propLabel").textContent = state.label;
  document.getElementById("propObs").textContent = String(obs);
  document.getElementById("propVars").textContent = String(vars);
  document.getElementById("propSize").textContent = `${sizeKb} KB`;

  if (state.rows.length && state.rows[0][0]) {
    const rangeStart = state.rows[0][0];
    const rangeEnd = state.rows[state.rows.length - 1][0];
    document.getElementById("propRange").textContent = `${rangeStart} - ${rangeEnd}`;
  } else {
    document.getElementById("propRange").textContent = "-";
  }
};

const updateStats = () => {
  const obs = state.rows.length;
  const vars = state.headers.length;
  document.getElementById("datasetStats").textContent = `Obs: ${obs} · Vars: ${vars}`;
  document.getElementById("statusLeft").textContent = `Data: ${state.name}`;
  document.getElementById("statusCenter").textContent = `Mode: Analysis · Time Series (Quarterly)`;
};

const renderCommandHistory = () => {
  const tbody = document.querySelector("#commandHistory tbody");
  tbody.innerHTML = "";
  state.history.slice(-12).forEach((entry, index) => {
    const row = document.createElement("tr");
    const idxCell = document.createElement("td");
    idxCell.textContent = String(index + 1);
    const cmdCell = document.createElement("td");
    cmdCell.textContent = entry.command;
    const rcCell = document.createElement("td");
    rcCell.textContent = String(entry.rc);
    row.append(idxCell, cmdCell, rcCell);
    tbody.appendChild(row);
  });
};

const addCommand = (command, rc) => {
  state.history.push({ command, rc });
  renderCommandHistory();
};

const setResults = (value) => {
  const output = document.getElementById("resultsOutput");
  output.textContent = value;
};

const setData = ({ headers, rows }, name = "macro_data.dta") => {
  state.headers = headers;
  state.rows = rows;
  state.name = name;
  renderDataGrid();
  renderVariables();
  updateProperties();
  updateStats();
};

const getPrimarySeries = () => {
  for (let colIndex = 0; colIndex < state.headers.length; colIndex += 1) {
    const values = state.rows.map((row) => row[colIndex]);
    const numericValues = values.filter((value) => isNumeric(value));
    if (numericValues.length >= 10 && numericValues.length / values.length >= 0.8) {
      return numericValues.map((value) => Number(value));
    }
  }
  return [];
};

const runAutoArima = async () => {
  const values = getPrimarySeries();
  if (values.length < 10) {
    setResults("Upload a dataset with at least 10 numeric observations to run Auto-ARIMA.");
    return;
  }

  setResults("Running auto-ARIMA...\n");
  addCommand("auto_arima", 0);

  try {
    const response = await fetch("/api/v1/auto-arima", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        data: { values },
        max_p: 5,
        max_d: 2,
        max_q: 5,
        seasonal: false,
        information_criterion: "aic",
        steps: 12,
        alpha: 0.05,
      }),
    });

    if (!response.ok) {
      const error = await response.text();
      setResults(`Auto-ARIMA failed (HTTP ${response.status}).\n${error}`);
      addCommand("auto_arima", response.status);
      return;
    }

    const payload = await response.json();
    setResults(JSON.stringify(payload, null, 2));
  } catch (error) {
    setResults(`Auto-ARIMA failed: ${error.message}`);
    addCommand("auto_arima", 1);
  }
};

const runDiagnostics = async () => {
  const values = getPrimarySeries();
  if (values.length < 10) {
    setResults("Upload a dataset with at least 10 numeric observations to run diagnostics.");
    return;
  }

  setResults("Running diagnostics...\n");
  addCommand("adf", 0);
  addCommand("acf_pacf", 0);

  try {
    const [adfResp, acfResp] = await Promise.all([
      fetch("/api/v1/diagnostics/adf", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ values }),
      }),
      fetch("/api/v1/diagnostics/acf-pacf", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ values, n_lags: 20, alpha: 0.05 }),
      }),
    ]);

    if (!adfResp.ok || !acfResp.ok) {
      const [adfError, acfError] = await Promise.all([
        adfResp.text(),
        acfResp.text(),
      ]);
      setResults(`Diagnostics failed.\nADF: ${adfError}\nACF/PACF: ${acfError}`);
      return;
    }

    const [adfData, acfData] = await Promise.all([
      adfResp.json(),
      acfResp.json(),
    ]);

    setResults(
      JSON.stringify(
        {
          adf: adfData,
          acf_pacf: acfData,
        },
        null,
        2,
      ),
    );
  } catch (error) {
    setResults(`Diagnostics failed: ${error.message}`);
  }
};

const handleFileUpload = (event) => {
  const file = event.target.files[0];
  if (!file) {
    return;
  }

  const reader = new FileReader();
  reader.onload = () => {
    const { headers, rows } = parseCsv(String(reader.result));
    state.label = file.name.replace(/\.[^/.]+$/, "");
    setData({ headers, rows }, file.name);
    addCommand(`use ${file.name}`, 0);
  };
  reader.readAsText(file);
};

const bindTabs = () => {
  const tabs = document.querySelectorAll(".results-tabs .tab");
  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      tabs.forEach((item) => item.classList.remove("active"));
      tab.classList.add("active");

      const target = tab.getAttribute("data-tab");
      document.querySelectorAll(".results-pane .pane").forEach((pane) => {
        pane.classList.toggle("active", pane.id === target);
      });
    });
  });
};

const init = () => {
  document.getElementById("fileInput").addEventListener("change", handleFileUpload);
  document.getElementById("sampleDataBtn").addEventListener("click", () => {
    const parsed = parseCsv(sampleCsv);
    state.label = "Macroeconomic Quarterly Data";
    setData(parsed, "macro_data.dta");
    addCommand("use macro_data.dta", 0);
  });
  document.getElementById("runAutoBtn").addEventListener("click", runAutoArima);
  document.getElementById("runDiagnosticsBtn").addEventListener("click", runDiagnostics);

  bindTabs();
  setData(parseCsv(sampleCsv), "macro_data.dta");
  addCommand("use macro_data.dta", 0);
  addCommand("describe", 0);
  addCommand("summarize", 0);
};

document.addEventListener("DOMContentLoaded", init);
