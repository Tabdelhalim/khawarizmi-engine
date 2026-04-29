"""Tests for the ARIMA service and /api/v1/arima endpoints."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.services.arima_service import fit_arima, forecast_arima
from tests.conftest import make_ar1, make_random_walk


# ---------------------------------------------------------------------------
# Service-level tests
# ---------------------------------------------------------------------------

class TestARIMAService:
    def test_fit_returns_correct_lengths(self):
        series = make_ar1(100)
        result = fit_arima(series, order=(1, 0, 0))
        assert len(result.fitted) == len(series)
        assert len(result.residuals) == len(series)

    def test_fit_summary_fields(self):
        series = make_ar1(100)
        result = fit_arima(series, order=(1, 0, 0))
        assert isinstance(result.summary.aic, float)
        assert isinstance(result.summary.bic, float)
        assert isinstance(result.summary.hqic, float)
        assert result.summary.n_obs == 100
        assert len(result.summary.params) > 0

    def test_fit_with_differencing(self):
        rw = make_random_walk(80)
        result = fit_arima(rw, order=(1, 1, 0))
        # statsmodels reports n_obs as the original series length
        assert result.summary.n_obs == 80

    def test_forecast_returns_n_steps(self):
        series = make_ar1(100)
        result = forecast_arima(series, order=(1, 0, 0), steps=15)
        assert len(result.forecast) == 15

    def test_forecast_confidence_intervals_ordered(self):
        series = make_ar1(100)
        result = forecast_arima(series, order=(1, 0, 0), steps=5)
        for pt in result.forecast:
            assert pt.lower_ci <= pt.forecast <= pt.upper_ci

    def test_forecast_steps_are_sequential(self):
        series = make_ar1(100)
        result = forecast_arima(series, order=(1, 0, 0), steps=5)
        assert [pt.step for pt in result.forecast] == [1, 2, 3, 4, 5]

    def test_arima_ma_component(self):
        series = make_ar1(100)
        result = fit_arima(series, order=(0, 0, 1))
        assert len(result.fitted) == 100

    def test_arima_with_dates(self):
        import pandas as pd

        dates = pd.date_range("2020-01-01", periods=60, freq="MS").strftime("%Y-%m-%d").tolist()
        series = make_ar1(60)
        result = fit_arima(series, order=(1, 0, 0), dates=dates)
        assert len(result.fitted) == 60


# ---------------------------------------------------------------------------
# API-level tests
# ---------------------------------------------------------------------------

class TestARIMAEndpoints:
    def test_fit_endpoint_success(self, client: TestClient):
        payload = {
            "data": {"values": make_ar1(60)},
            "order": {"p": 1, "d": 0, "q": 0},
        }
        resp = client.post("/api/v1/arima/fit", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert "fitted" in body
        assert "residuals" in body
        assert "summary" in body

    def test_fit_endpoint_summary_keys(self, client: TestClient):
        payload = {
            "data": {"values": make_ar1(60)},
            "order": {"p": 1, "d": 0, "q": 1},
        }
        resp = client.post("/api/v1/arima/fit", json=payload)
        assert resp.status_code == 200
        summary = resp.json()["summary"]
        for key in ("aic", "bic", "hqic", "log_likelihood", "n_obs"):
            assert key in summary

    def test_forecast_endpoint_success(self, client: TestClient):
        payload = {
            "data": {"values": make_ar1(80)},
            "order": {"p": 1, "d": 0, "q": 0},
            "steps": 10,
            "alpha": 0.05,
        }
        resp = client.post("/api/v1/arima/forecast", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["forecast"]) == 10

    def test_forecast_ci_present(self, client: TestClient):
        payload = {
            "data": {"values": make_ar1(80)},
            "order": {"p": 1, "d": 0, "q": 0},
            "steps": 5,
        }
        resp = client.post("/api/v1/arima/forecast", json=payload)
        assert resp.status_code == 200
        for pt in resp.json()["forecast"]:
            assert "lower_ci" in pt
            assert "upper_ci" in pt
            assert "forecast" in pt

    def test_fit_endpoint_too_short_series(self, client: TestClient):
        payload = {
            "data": {"values": [1.0, 2.0, 3.0]},
            "order": {"p": 1, "d": 0, "q": 0},
        }
        resp = client.post("/api/v1/arima/fit", json=payload)
        assert resp.status_code == 422

    def test_fit_endpoint_invalid_order(self, client: TestClient):
        payload = {
            "data": {"values": make_ar1(60)},
            "order": {"p": -1, "d": 0, "q": 0},
        }
        resp = client.post("/api/v1/arima/fit", json=payload)
        assert resp.status_code == 422
