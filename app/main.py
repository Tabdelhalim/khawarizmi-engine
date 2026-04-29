"""Khawarizmi Engine – No-code econometrics and time series analysis platform.

Start the server::

    uvicorn app.main:app --reload

Interactive API docs:  http://localhost:8000/docs
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.routers.arima_router import router as arima_router
from app.routers.auto_arima_router import router as auto_arima_router
from app.routers.diagnostics_router import router as diagnostics_router
from app.routers.sarima_router import router as sarima_router

app = FastAPI(
    title="Khawarizmi Engine",
    description=(
        "A no-code econometrics and time series analysis platform supporting "
        "ARIMA, SARIMA, automated model selection, forecasting, and a full "
        "suite of statistical diagnostics."
    ),
    version="1.0.0",
    contact={
        "name": "Khawarizmi Engine",
        "url": "https://github.com/Tabdelhalim/khawarizmi-engine",
    },
    license_info={
        "name": "MIT",
    },
)

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_PREFIX = "/api/v1"

app.include_router(arima_router, prefix=API_PREFIX)
app.include_router(sarima_router, prefix=API_PREFIX)
app.include_router(diagnostics_router, prefix=API_PREFIX)
app.include_router(auto_arima_router, prefix=API_PREFIX)


@app.get("/", tags=["Health"], summary="Health check")
def root() -> dict:
    """Return a simple health-check payload."""
    return {
        "status": "ok",
        "service": "khawarizmi-engine",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/api/v1/health", tags=["Health"], summary="API health check")
def health() -> dict:
    """Detailed health check endpoint."""
    return {
        "status": "ok",
        "endpoints": [
            "/api/v1/arima/fit",
            "/api/v1/arima/forecast",
            "/api/v1/sarima/fit",
            "/api/v1/sarima/forecast",
            "/api/v1/diagnostics/adf",
            "/api/v1/diagnostics/acf-pacf",
            "/api/v1/diagnostics/residuals",
            "/api/v1/auto-arima",
        ],
    }


@app.get("/ui", include_in_schema=False)
def ui() -> FileResponse:
    """Serve the preview web UI."""
    index_path = STATIC_DIR / "ui" / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="UI not available.")
    return FileResponse(index_path)
