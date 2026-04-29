"""Tests for auto-ARIMA service and /api/v1/auto-arima endpoint."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.services.auto_arima_service import run_auto_arima
from tests.conftest import make_ar1, make_seasonal


# ---------------------------------------------------------------------------
# Service-level tests
# ---------------------------------------------------------------------------

class TestAutoARIMAService:
    def test_returns_best_order(self):
        series = make_ar1(100)
        result = run_auto_arima(series, max_p=2, max_d=1, max_q=2)
        assert "p" in result.best_order
        assert "d" in result.best_order
        assert "q" in result.best_order

    def test_forecast_length(self):
        series = make_ar1(100)
        result = run_auto_arima(series, max_p=2, max_d=1, max_q=2, steps=8)
        assert len(result.forecast) == 8

    def test_search_results_populated(self):
        series = make_ar1(80)
        result = run_auto_arima(series, max_p=1, max_d=1, max_q=1)
        assert len(result.search_results) > 0

    def test_search_results_sorted_by_ic(self):
        series = make_ar1(80)
        result = run_auto_arima(series, max_p=2, max_d=1, max_q=2, information_criterion="bic")
        # Converged results should have ascending BIC values
        converged = [r["bic"] for r in result.search_results if r.get("bic") is not None]
        assert converged == sorted(converged)

    def test_summary_fields(self):
        series = make_ar1(80)
        result = run_auto_arima(series, max_p=1, max_d=0, max_q=1)
        assert isinstance(result.summary.aic, float)
        assert isinstance(result.summary.n_obs, int)

    def test_ci_ordered(self):
        series = make_ar1(80)
        result = run_auto_arima(series, max_p=1, max_d=0, max_q=1, steps=5)
        for pt in result.forecast:
            assert pt.lower_ci <= pt.forecast <= pt.upper_ci

    def test_seasonal_auto_arima(self):
        series = make_seasonal(120, period=12)
        result = run_auto_arima(
            series,
            max_p=1,
            max_d=0,
            max_q=1,
            seasonal=True,
            frequency=12,
            steps=6,
        )
        assert "seasonal" in result.best_order
        assert len(result.forecast) == 6

    def test_bic_criterion(self):
        series = make_ar1(100)
        result = run_auto_arima(series, max_p=2, max_d=1, max_q=2, information_criterion="bic")
        assert result.best_order is not None

    def test_hqic_criterion(self):
        series = make_ar1(100)
        result = run_auto_arima(series, max_p=2, max_d=1, max_q=2, information_criterion="hqic")
        assert result.best_order is not None


# ---------------------------------------------------------------------------
# API-level tests
# ---------------------------------------------------------------------------

class TestAutoARIMAEndpoints:
    def test_basic_auto_arima(self, client: TestClient):
        payload = {
            "data": {"values": make_ar1(80)},
            "max_p": 2,
            "max_d": 1,
            "max_q": 2,
            "steps": 5,
        }
        resp = client.post("/api/v1/auto-arima", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert "best_order" in body
        assert "forecast" in body
        assert len(body["forecast"]) == 5

    def test_seasonal_auto_arima_endpoint(self, client: TestClient):
        payload = {
            "data": {"values": make_seasonal(120, period=12), "frequency": 12},
            "max_p": 1,
            "max_d": 0,
            "max_q": 1,
            "seasonal": True,
            "steps": 6,
        }
        resp = client.post("/api/v1/auto-arima", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert "seasonal" in body["best_order"]

    def test_seasonal_without_frequency_rejected(self, client: TestClient):
        payload = {
            "data": {"values": make_ar1(80)},
            "max_p": 1,
            "max_d": 0,
            "max_q": 1,
            "seasonal": True,
        }
        resp = client.post("/api/v1/auto-arima", json=payload)
        assert resp.status_code == 422

    def test_search_results_in_response(self, client: TestClient):
        payload = {
            "data": {"values": make_ar1(80)},
            "max_p": 1,
            "max_d": 1,
            "max_q": 1,
        }
        resp = client.post("/api/v1/auto-arima", json=payload)
        assert resp.status_code == 200
        assert len(resp.json()["search_results"]) > 0

    def test_invalid_criterion_rejected(self, client: TestClient):
        payload = {
            "data": {"values": make_ar1(80)},
            "max_p": 1,
            "max_d": 0,
            "max_q": 1,
            "information_criterion": "xyz",
        }
        resp = client.post("/api/v1/auto-arima", json=payload)
        # The invalid criterion causes a runtime error → 422
        assert resp.status_code == 422
