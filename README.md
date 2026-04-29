# Khawarizmi Engine

**No-code econometrics and time series analysis platform**

Khawarizmi Engine exposes a clean REST API that lets you fit, forecast, and diagnose
time series models **without writing a single line of statistical code**.
Point it at your data, choose your model parameters (or let auto-ARIMA choose for you),
and get back structured JSON containing fitted values, forecasts with confidence
intervals, and a rich set of diagnostic statistics.

---

## Features

| Capability | Details |
|---|---|
| **ARIMA** | Fit ARIMA(p,d,q) models; retrieve in-sample fits, residuals, AIC/BIC/HQIC, parameter estimates and p-values |
| **SARIMA** | Seasonal ARIMA(p,d,q)(P,D,Q,s) with the same rich output |
| **Forecasting** | Point forecasts + configurable confidence intervals for any horizon |
| **Auto-ARIMA** | Exhaustive (p,d,q) grid search with AIC / BIC / HQIC model selection; optional seasonal grid |
| **ADF test** | Augmented Dickey-Fuller unit root / stationarity test |
| **ACF / PACF** | Autocorrelation and partial-autocorrelation functions with confidence bands |
| **Residual diagnostics** | Ljung-Box, Jarque-Bera, Durbin-Watson; automatic pass/fail flags |

---

## Quick start

### 1 – Install dependencies

```bash
pip install -r requirements.txt
```

### 2 – Start the server

```bash
uvicorn app.main:app --reload
```

The interactive API docs are available at **http://localhost:8000/docs**.

### 3 – Open the UI (preview)

Visit **http://localhost:8000/ui** to access the desktop-style interface shell.
You can upload a CSV file to populate the data grid and run Auto-ARIMA or
diagnostics directly from the toolbar.

---

## API reference

All endpoints live under `/api/v1`.

### ARIMA

#### `POST /api/v1/arima/fit`

Fit an ARIMA(p,d,q) model.

```json
{
  "data": { "values": [112, 118, 132, 129, 121, 135, 148, 148, 136, 119, 104, 118] },
  "order": { "p": 1, "d": 1, "q": 1 }
}
```

#### `POST /api/v1/arima/forecast`

Fit an ARIMA model and produce out-of-sample forecasts.

```json
{
  "data": { "values": [112, 118, 132, 129, 121, 135, 148, 148, 136, 119, 104, 118] },
  "order": { "p": 1, "d": 1, "q": 1 },
  "steps": 12,
  "alpha": 0.05
}
```

---

### SARIMA

#### `POST /api/v1/sarima/fit`

```json
{
  "data": { "values": ["...120 monthly observations..."], "frequency": 12 },
  "order": { "p": 1, "d": 1, "q": 1, "P": 1, "D": 1, "Q": 1, "s": 12 }
}
```

#### `POST /api/v1/sarima/forecast`

Same payload as `/sarima/fit`, plus `"steps"` and `"alpha"`.

---

### Auto-ARIMA

#### `POST /api/v1/auto-arima`

Automatically select the best ARIMA or SARIMA order.

```json
{
  "data": { "values": ["..."], "frequency": 12 },
  "max_p": 5,
  "max_d": 2,
  "max_q": 5,
  "seasonal": true,
  "information_criterion": "aic",
  "steps": 12,
  "alpha": 0.05
}
```

Returns the best order, model summary, fitted values, forecasts **and** the full
ranked search table.

---

### Diagnostics

#### `POST /api/v1/diagnostics/adf`

Augmented Dickey-Fuller unit root test.

```json
{ "values": ["..."], "regression": "c" }
```

#### `POST /api/v1/diagnostics/acf-pacf`

ACF and PACF with confidence intervals.

```json
{ "values": ["..."], "n_lags": 20, "alpha": 0.05 }
```

#### `POST /api/v1/diagnostics/residuals`

Residual diagnostics (Ljung-Box, Jarque-Bera, Durbin-Watson).

```json
{ "values": ["...residuals from a fitted model..."] }
```

---

## Running the tests

```bash
pytest
```

The test suite covers service-layer unit tests and full HTTP endpoint integration
tests for every capability (57 tests total).

---

## Project layout

```
app/
  main.py                  # FastAPI application
  routers/
    arima_router.py
    sarima_router.py
    diagnostics_router.py
    auto_arima_router.py
  services/
    arima_service.py
    sarima_service.py
    diagnostics_service.py
    auto_arima_service.py
  schemas/
    models.py              # Pydantic request / response schemas
tests/
  conftest.py              # Shared fixtures and synthetic data generators
  test_arima.py
  test_sarima.py
  test_diagnostics.py
  test_auto_arima.py
  test_health.py
requirements.txt
pytest.ini
```
