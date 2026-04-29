"""SARIMA router."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.models import (
    FitResponse,
    ForecastResponse,
    SARIMAFitRequest,
    SARIMAForecastRequest,
)
from app.services.sarima_service import fit_sarima, forecast_sarima

router = APIRouter(prefix="/sarima", tags=["SARIMA"])


@router.post("/fit", response_model=FitResponse, summary="Fit a SARIMA model")
def sarima_fit(request: SARIMAFitRequest) -> FitResponse:
    """Fit a SARIMA(p,d,q)(P,D,Q,s) model to the supplied time series.

    Returns in-sample fitted values, residuals, and key model statistics.
    """
    try:
        order = (request.order.p, request.order.d, request.order.q)
        seasonal_order = (
            request.order.P,
            request.order.D,
            request.order.Q,
            request.order.s,
        )
        return fit_sarima(
            values=request.data.values,
            order=order,
            seasonal_order=seasonal_order,
            trend=request.trend or "n",
            dates=request.data.dates,
        )
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/forecast", response_model=ForecastResponse, summary="SARIMA forecast")
def sarima_forecast(request: SARIMAForecastRequest) -> ForecastResponse:
    """Fit a SARIMA model and produce *steps*-ahead point forecasts with confidence intervals."""
    try:
        order = (request.order.p, request.order.d, request.order.q)
        seasonal_order = (
            request.order.P,
            request.order.D,
            request.order.Q,
            request.order.s,
        )
        return forecast_sarima(
            values=request.data.values,
            order=order,
            seasonal_order=seasonal_order,
            steps=request.steps,
            alpha=request.alpha,
            trend=request.trend or "n",
            dates=request.data.dates,
        )
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
