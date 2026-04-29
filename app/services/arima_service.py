"""ARIMA model service."""

from __future__ import annotations

from typing import List, Optional, Tuple

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.tsa.arima.model import ARIMA

from app.schemas.models import FitResponse, ForecastResponse, ModelSummary, ForecastPoint


def _build_series(values: List[float], dates: Optional[List[str]] = None) -> pd.Series:
    """Convert raw lists into a pandas Series with an appropriate index."""
    if dates:
        index = pd.to_datetime(dates)
        return pd.Series(values, index=index, dtype=float)
    return pd.Series(values, dtype=float)


def _extract_summary(result) -> ModelSummary:
    """Pull key statistics out of a fitted statsmodels result."""
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


def _build_forecast_points(
    forecast_object,
    alpha: float,
    steps: int,
) -> List[ForecastPoint]:
    """Build a list of ForecastPoint from a statsmodels GetPrediction result."""
    summary_frame = forecast_object.summary_frame(alpha=alpha)
    points: List[ForecastPoint] = []
    for step_idx in range(steps):
        row = summary_frame.iloc[step_idx]
        points.append(
            ForecastPoint(
                step=step_idx + 1,
                forecast=float(row["mean"]),
                lower_ci=float(row["mean_ci_lower"]),
                upper_ci=float(row["mean_ci_upper"]),
            )
        )
    return points


def fit_arima(
    values: List[float],
    order: Tuple[int, int, int],
    trend: str = "n",
    dates: Optional[List[str]] = None,
) -> FitResponse:
    """Fit an ARIMA(p,d,q) model and return fit statistics."""
    series = _build_series(values, dates)
    model = ARIMA(series, order=order, trend=trend)
    result = model.fit()

    fitted_vals = result.fittedvalues.tolist()
    residuals = result.resid.tolist()
    summary = _extract_summary(result)

    return FitResponse(fitted=fitted_vals, residuals=residuals, summary=summary)


def forecast_arima(
    values: List[float],
    order: Tuple[int, int, int],
    steps: int = 10,
    alpha: float = 0.05,
    trend: str = "n",
    dates: Optional[List[str]] = None,
) -> ForecastResponse:
    """Fit an ARIMA model and return in-sample fit plus out-of-sample forecasts."""
    series = _build_series(values, dates)
    model = ARIMA(series, order=order, trend=trend)
    result = model.fit()

    fitted_vals = result.fittedvalues.tolist()
    residuals = result.resid.tolist()
    summary = _extract_summary(result)

    forecast_obj = result.get_forecast(steps=steps)
    forecast_points = _build_forecast_points(forecast_obj, alpha=alpha, steps=steps)

    return ForecastResponse(
        fitted=fitted_vals,
        residuals=residuals,
        summary=summary,
        forecast=forecast_points,
    )
