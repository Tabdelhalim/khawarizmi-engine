"""ARIMA router."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.models import ARIMAFitRequest, FitResponse, ForecastRequest, ForecastResponse
from app.services.arima_service import fit_arima, forecast_arima

router = APIRouter(prefix="/arima", tags=["ARIMA"])


@router.post("/fit", response_model=FitResponse, summary="Fit an ARIMA model")
def arima_fit(request: ARIMAFitRequest) -> FitResponse:
    """Fit an ARIMA(p,d,q) model to the supplied time series.

    Returns in-sample fitted values, residuals, and key model statistics
    (AIC, BIC, HQIC, log-likelihood, parameter estimates, p-values).
    """
    try:
        return fit_arima(
            values=request.data.values,
            order=(request.order.p, request.order.d, request.order.q),
            trend=request.trend or "n",
            dates=request.data.dates,
        )
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/forecast", response_model=ForecastResponse, summary="ARIMA forecast")
def arima_forecast(request: ForecastRequest) -> ForecastResponse:
    """Fit an ARIMA model and produce *steps*-ahead point forecasts with confidence intervals."""
    try:
        return forecast_arima(
            values=request.data.values,
            order=(request.order.p, request.order.d, request.order.q),
            steps=request.steps,
            alpha=request.alpha,
            trend=request.trend or "n",
            dates=request.data.dates,
        )
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
