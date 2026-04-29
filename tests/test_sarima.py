"""Tests for the SARIMA service and /api/v1/sarima endpoints."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.services.sarima_service import fit_sarima, forecast_sarima
from tests.conftest import make_seasonal


# ---------------------------------------------------------------------------
# Service-level tests
# ---------------------------------------------------------------------------

class TestSARIMAService:
    def test_fit_returns_correct_lengths(self):
        series = make_seasonal(120, period=12)
        result = fit_sarima(series, order=(1, 0, 0), seasonal_order=(1, 0, 0, 12))
        assert len(result.fitted) == len(series)
        assert len(result.residuals) == len(series)

    def test_fit_summary_fields(self):
        series = make_seasonal(120, period=12)
        result = fit_sarima(series, order=(1, 0, 0), seasonal_order=(1, 0, 0, 12))
        assert isinstance(result.summary.aic, float)
        assert result.summary.n_obs == 120

    def test_forecast_returns_n_steps(self):
        series = make_seasonal(120, period=12)
        result = forecast_sarima(series, order=(1, 0, 0), seasonal_order=(1, 0, 0, 12), steps=12)
        assert len(result.forecast) == 12

    def test_forecast_confidence_intervals_ordered(self):
        series = make_seasonal(120, period=12)
        result = forecast_sarima(series, order=(1, 0, 0), seasonal_order=(1, 0, 0, 12), steps=6)
        for pt in result.forecast:
            assert pt.lower_ci <= pt.forecast <= pt.upper_ci

    def test_sarima_quarterly(self):
        series = make_seasonal(80, period=4)
        result = fit_sarima(series, order=(1, 0, 0), seasonal_order=(1, 0, 0, 4))
        assert len(result.fitted) == 80


# ---------------------------------------------------------------------------
# API-level tests
# ---------------------------------------------------------------------------

class TestSARIMAEndpoints:
    def test_fit_endpoint_success(self, client: TestClient):
        payload = {
            "data": {"values": make_seasonal(120, period=12), "frequency": 12},
            "order": {"p": 1, "d": 0, "q": 0, "P": 1, "D": 0, "Q": 0, "s": 12},
        }
        resp = client.post("/api/v1/sarima/fit", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["fitted"]) == 120

    def test_forecast_endpoint_success(self, client: TestClient):
        payload = {
            "data": {"values": make_seasonal(120, period=12), "frequency": 12},
            "order": {"p": 1, "d": 0, "q": 0, "P": 1, "D": 0, "Q": 0, "s": 12},
            "steps": 12,
        }
        resp = client.post("/api/v1/sarima/forecast", json=payload)
        assert resp.status_code == 200
        assert len(resp.json()["forecast"]) == 12

    def test_fit_missing_seasonal_order(self, client: TestClient):
        # Missing 'P', 'D', 'Q', 's' → validation error
        payload = {
            "data": {"values": make_seasonal(120, period=12)},
            "order": {"p": 1, "d": 0, "q": 0},
        }
        resp = client.post("/api/v1/sarima/fit", json=payload)
        assert resp.status_code == 422

    def test_fit_too_short_series(self, client: TestClient):
        payload = {
            "data": {"values": [1.0] * 5},
            "order": {"p": 1, "d": 0, "q": 0, "P": 1, "D": 0, "Q": 0, "s": 12},
        }
        resp = client.post("/api/v1/sarima/fit", json=payload)
        assert resp.status_code == 422
