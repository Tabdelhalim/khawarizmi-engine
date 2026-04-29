"""Tests for core API endpoints (health check, OpenAPI schema)."""

from __future__ import annotations

from fastapi.testclient import TestClient


class TestHealthEndpoints:
    def test_root(self, client: TestClient):
        resp = client.get("/")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert body["service"] == "khawarizmi-engine"

    def test_health(self, client: TestClient):
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert isinstance(body["endpoints"], list)
        assert len(body["endpoints"]) > 0

    def test_openapi_schema_available(self, client: TestClient):
        resp = client.get("/openapi.json")
        assert resp.status_code == 200
        schema = resp.json()
        assert "paths" in schema
        assert "/api/v1/arima/fit" in schema["paths"]
        assert "/api/v1/sarima/fit" in schema["paths"]
        assert "/api/v1/diagnostics/adf" in schema["paths"]
        assert "/api/v1/auto-arima" in schema["paths"]
