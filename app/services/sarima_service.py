"""SARIMA model service."""

from __future__ import annotations

from typing import List, Optional, Tuple

import pandas as pd
from statsmodels.tsa.statespace.sarimax import SARIMAX

from app.schemas.models import FitResponse, ForecastResponse, ModelSummary, ForecastPoint
from app.services.arima_service import _build_series, _build_forecast_points


def _extract_sarima_summary(result) -> ModelSummary:
    """Extract summary statistics from a fitted SARIMAX result."""
    params = {str(k): float(v) for k, v in result.params.items()}
    p_values = {str(k): float(v) for k, v in result.pvalues.items()}
    std_errors = {str(k): float(v) for k, v in result.bse.items()}
    return ModelSummary(
        aic=float(result.aic),
        bic=float(result.bic),
        hqic=float(result.hqic),
        log_likelihood=float(result.llf),
        params=params,
        p_values=p_values,
        std_errors=std_errors,
        n_obs=int(result.nobs),
    )


def fit_sarima(
    values: List[float],
    order: Tuple[int, int, int],
    seasonal_order: Tuple[int, int, int, int],
    trend: str = "n",
    dates: Optional[List[str]] = None,
) -> FitResponse:
    """Fit a SARIMA(p,d,q)(P,D,Q,s) model."""
    series = _build_series(values, dates)
    model = SARIMAX(series, order=order, seasonal_order=seasonal_order, trend=trend)
    result = model.fit(disp=False)

    fitted_vals = result.fittedvalues.tolist()
    residuals = result.resid.tolist()
    summary = _extract_sarima_summary(result)

    return FitResponse(fitted=fitted_vals, residuals=residuals, summary=summary)


def forecast_sarima(
    values: List[float],
    order: Tuple[int, int, int],
    seasonal_order: Tuple[int, int, int, int],
    steps: int = 10,
    alpha: float = 0.05,
    trend: str = "n",
    dates: Optional[List[str]] = None,
) -> ForecastResponse:
    """Fit a SARIMA model and produce out-of-sample forecasts."""
    series = _build_series(values, dates)
    model = SARIMAX(series, order=order, seasonal_order=seasonal_order, trend=trend)
    result = model.fit(disp=False)

    fitted_vals = result.fittedvalues.tolist()
    residuals = result.resid.tolist()
    summary = _extract_sarima_summary(result)

    forecast_obj = result.get_forecast(steps=steps)
    forecast_points = _build_forecast_points(forecast_obj, alpha=alpha, steps=steps)

    return ForecastResponse(
        fitted=fitted_vals,
        residuals=residuals,
        summary=summary,
        forecast=forecast_points,
    )
