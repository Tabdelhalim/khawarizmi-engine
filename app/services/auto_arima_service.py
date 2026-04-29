"""Auto-ARIMA: exhaustive grid search over (p,d,q) using an information criterion."""

from __future__ import annotations

import itertools
from typing import List, Optional

import numpy as np
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX

from app.schemas.models import AutoARIMAResponse, ForecastPoint, ModelSummary
from app.services.arima_service import _build_series, _build_forecast_points


def _ic_value(result, criterion: str) -> float:
    criterion = criterion.lower()
    if criterion == "aic":
        return float(result.aic)
    if criterion == "bic":
        return float(result.bic)
    if criterion == "hqic":
        return float(result.hqic)
    raise ValueError(f"Unknown information criterion: {criterion!r}. Use 'aic', 'bic', or 'hqic'.")


def run_auto_arima(
    values: List[float],
    max_p: int = 5,
    max_d: int = 2,
    max_q: int = 5,
    seasonal: bool = False,
    frequency: Optional[int] = None,
    information_criterion: str = "aic",
    steps: int = 10,
    alpha: float = 0.05,
    dates: Optional[List[str]] = None,
) -> AutoARIMAResponse:
    """Search over ARIMA/SARIMA orders and return the best-fitting model.

    Parameters
    ----------
    values:
        Time series observations.
    max_p, max_d, max_q:
        Upper bounds for the non-seasonal (p, d, q) orders.
    seasonal:
        When ``True`` a seasonal grid is also searched using *frequency* as ``s``.
    frequency:
        Seasonal period – required when *seasonal* is ``True``.
    information_criterion:
        Which IC to minimise: ``'aic'``, ``'bic'``, or ``'hqic'``.
    steps:
        Forecast horizon.
    alpha:
        Significance level for confidence intervals.
    dates:
        Optional ISO-8601 date strings aligned with *values*.
    """
    series = _build_series(values, dates)

    p_range = range(max_p + 1)
    d_range = range(max_d + 1)
    q_range = range(max_q + 1)

    search_results: List[dict] = []
    best_ic = np.inf
    best_result = None
    best_order: Optional[tuple] = None
    best_seasonal_order: Optional[tuple] = None

    candidate_orders = list(itertools.product(p_range, d_range, q_range))

    if seasonal and frequency:
        seasonal_candidates = list(itertools.product([0, 1], [0, 1], [0, 1]))
    else:
        seasonal_candidates = [None]

    for order in candidate_orders:
        for s_order in seasonal_candidates:
            try:
                if s_order is not None:
                    full_s_order = (*s_order, frequency)
                    model = SARIMAX(
                        series,
                        order=order,
                        seasonal_order=full_s_order,
                        trend="n",
                    )
                    result = model.fit(disp=False)
                else:
                    model = ARIMA(series, order=order, trend="n")
                    result = model.fit()
                ic = _ic_value(result, information_criterion)

                entry = {
                    "order": {"p": order[0], "d": order[1], "q": order[2]},
                    information_criterion: ic,
                    "converged": True,
                }
                if s_order is not None:
                    entry["seasonal_order"] = {
                        "P": s_order[0],
                        "D": s_order[1],
                        "Q": s_order[2],
                        "s": frequency,
                    }
                search_results.append(entry)

                if ic < best_ic:
                    best_ic = ic
                    best_result = result
                    best_order = order
                    best_seasonal_order = s_order

            except Exception:
                entry = {
                    "order": {"p": order[0], "d": order[1], "q": order[2]},
                    information_criterion: None,
                    "converged": False,
                }
                if s_order is not None:
                    entry["seasonal_order"] = {
                        "P": s_order[0],
                        "D": s_order[1],
                        "Q": s_order[2],
                        "s": frequency,
                    }
                search_results.append(entry)

    if best_result is None:
        raise RuntimeError("No ARIMA model converged during auto-search.")

    # Sort search results by IC (ascending, failed models last)
    search_results.sort(
        key=lambda x: x.get(information_criterion) or np.inf
    )

    params = {str(k): float(v) for k, v in best_result.params.items()}
    p_values = {str(k): float(v) for k, v in best_result.pvalues.items()}
    std_errors = {str(k): float(v) for k, v in best_result.bse.items()}
    summary = ModelSummary(
        aic=float(best_result.aic),
        bic=float(best_result.bic),
        hqic=float(best_result.hqic),
        log_likelihood=float(best_result.llf),
        params=params,
        p_values=p_values,
        std_errors=std_errors,
        n_obs=int(best_result.nobs),
    )

    fitted_vals = best_result.fittedvalues.tolist()
    residuals = best_result.resid.tolist()

    forecast_obj = best_result.get_forecast(steps=steps)
    forecast_points = _build_forecast_points(forecast_obj, alpha=alpha, steps=steps)

    best_order_dict: dict = {"p": best_order[0], "d": best_order[1], "q": best_order[2]}
    if best_seasonal_order is not None:
        best_order_dict["seasonal"] = {
            "P": best_seasonal_order[0],
            "D": best_seasonal_order[1],
            "Q": best_seasonal_order[2],
            "s": frequency,
        }

    return AutoARIMAResponse(
        best_order=best_order_dict,
        summary=summary,
        fitted=fitted_vals,
        residuals=residuals,
        forecast=forecast_points,
        search_results=search_results,
    )
