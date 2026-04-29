"""Tests for the diagnostics service and /api/v1/diagnostics endpoints."""

from __future__ import annotations

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.services.diagnostics_service import (
    analyze_residuals,
    compute_acf_pacf,
    run_adf_test,
)
from tests.conftest import make_ar1, make_random_walk


# ---------------------------------------------------------------------------
# ADF test
# ---------------------------------------------------------------------------

class TestADFService:
    def test_stationary_series_detected(self):
        series = make_ar1(200)  # AR(1) with phi=0.7 → stationary
        result = run_adf_test(series)
        assert result.is_stationary is True
        assert isinstance(result.test_statistic, float)
        assert "1%" in result.critical_values

    def test_random_walk_not_stationary(self):
        rw = make_random_walk(200)
        result = run_adf_test(rw)
        # A random walk should fail the ADF test (p-value near 1)
        assert result.p_value > 0.05

    def test_regression_ct(self):
        series = make_ar1(100)
        result = run_adf_test(series, regression="ct")
        assert isinstance(result.test_statistic, float)

    def test_n_obs_reported(self):
        series = make_ar1(120)
        result = run_adf_test(series)
        assert result.n_obs > 0

    def test_critical_values_keys(self):
        series = make_ar1(100)
        result = run_adf_test(series)
        for key in ("1%", "5%", "10%"):
            assert key in result.critical_values


# ---------------------------------------------------------------------------
# ACF/PACF
# ---------------------------------------------------------------------------

class TestACFPACFService:
    def test_lengths_match_n_lags(self):
        series = make_ar1(100)
        result = compute_acf_pacf(series, n_lags=15)
        # lags 0..15 → 16 values
        assert len(result.acf) == 16
        assert len(result.pacf) == 16
        assert len(result.lags) == 16

    def test_acf_at_lag_0_is_one(self):
        series = make_ar1(100)
        result = compute_acf_pacf(series, n_lags=10)
        assert abs(result.acf[0] - 1.0) < 1e-9

    def test_confidence_interval_lengths(self):
        series = make_ar1(100)
        result = compute_acf_pacf(series, n_lags=10)
        assert len(result.acf_confint_lower) == 11
        assert len(result.acf_confint_upper) == 11
        assert len(result.pacf_confint_lower) == 11
        assert len(result.pacf_confint_upper) == 11


# ---------------------------------------------------------------------------
# Residual diagnostics
# ---------------------------------------------------------------------------

class TestResidualDiagnostics:
    def test_white_noise_passes(self):
        rng = np.random.default_rng(42)
        white_noise = rng.normal(0, 1, 200).tolist()
        result = analyze_residuals(white_noise)
        assert result.is_white_noise is True

    def test_autocorrelated_residuals_fail_ljung_box(self):
        series = make_ar1(200, phi=0.9)
        result = analyze_residuals(series)
        assert result.is_white_noise is False

    def test_result_fields_present(self):
        rng = np.random.default_rng(0)
        res = analyze_residuals(rng.normal(0, 1, 100).tolist())
        assert isinstance(res.ljung_box_stat, float)
        assert isinstance(res.jarque_bera_stat, float)
        assert isinstance(res.durbin_watson, float)
        assert isinstance(res.residuals_mean, float)
        assert isinstance(res.residuals_std, float)

    def test_normal_residuals_pass_jarque_bera(self):
        rng = np.random.default_rng(99)
        normal_res = rng.normal(0, 1, 500).tolist()
        result = analyze_residuals(normal_res)
        assert result.is_normal is True


# ---------------------------------------------------------------------------
# API-level tests
# ---------------------------------------------------------------------------

class TestDiagnosticsEndpoints:
    def test_adf_endpoint(self, client: TestClient):
        payload = {"values": make_ar1(100), "regression": "c"}
        resp = client.post("/api/v1/diagnostics/adf", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert "test_statistic" in body
        assert "is_stationary" in body

    def test_acf_pacf_endpoint(self, client: TestClient):
        payload = {"values": make_ar1(100), "n_lags": 20}
        resp = client.post("/api/v1/diagnostics/acf-pacf", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert "acf" in body
        assert "pacf" in body
        assert len(body["lags"]) == 21

    def test_residuals_endpoint(self, client: TestClient):
        import numpy as np

        rng = np.random.default_rng(42)
        payload = {"values": rng.normal(0, 1, 100).tolist()}
        resp = client.post("/api/v1/diagnostics/residuals", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert "ljung_box_stat" in body
        assert "is_white_noise" in body

    def test_adf_invalid_regression(self, client: TestClient):
        payload = {"values": make_ar1(50), "regression": "bad_option"}
        resp = client.post("/api/v1/diagnostics/adf", json=payload)
        assert resp.status_code == 422

    def test_short_series_rejected(self, client: TestClient):
        payload = {"values": [1.0, 2.0], "regression": "c"}
        resp = client.post("/api/v1/diagnostics/adf", json=payload)
        assert resp.status_code == 422
