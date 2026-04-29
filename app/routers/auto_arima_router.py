"""Auto-ARIMA router."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.models import AutoARIMARequest, AutoARIMAResponse
from app.services.auto_arima_service import run_auto_arima

router = APIRouter(prefix="/auto-arima", tags=["Auto-ARIMA"])


@router.post("", response_model=AutoARIMAResponse, summary="Auto-ARIMA model selection")
def auto_arima(request: AutoARIMARequest) -> AutoARIMAResponse:
    """Automatically search for the best ARIMA or SARIMA order.

    The engine performs an exhaustive grid search over all ``(p, d, q)``
    combinations up to the supplied maxima, selecting the model with the
    lowest value of the chosen information criterion (AIC by default).

    When ``seasonal=True`` a seasonal grid ``(P, D, Q) ∈ {0,1}³`` is also
    evaluated using ``data.frequency`` as the seasonal period ``s``.

    Returns the best-fit model summary, in-sample fitted values, residuals,
    out-of-sample forecasts, and the full ranked search table.
    """
    try:
        return run_auto_arima(
            values=request.data.values,
            max_p=request.max_p,
            max_d=request.max_d,
            max_q=request.max_q,
            seasonal=request.seasonal,
            frequency=request.data.frequency,
            information_criterion=request.information_criterion,
            steps=request.steps,
            alpha=request.alpha,
            dates=request.data.dates,
        )
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
