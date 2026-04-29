"""Diagnostics router."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.models import (
    ACFPACFRequest,
    ACFPACFResponse,
    ADFRequest,
    ADFResponse,
    DiagnosticsRequest,
    ResidualDiagnosticsResponse,
)
from app.services.diagnostics_service import (
    analyze_residuals,
    compute_acf_pacf,
    run_adf_test,
)

router = APIRouter(prefix="/diagnostics", tags=["Diagnostics"])


@router.post("/adf", response_model=ADFResponse, summary="Augmented Dickey-Fuller test")
def adf_test(request: ADFRequest) -> ADFResponse:
    """Run the Augmented Dickey-Fuller unit root test on the supplied series.

    A p-value below 0.05 is interpreted as evidence against a unit root
    (i.e. the series is likely stationary).
    """
    try:
        return run_adf_test(
            values=request.values,
            regression=request.regression,
            max_lags=request.max_lags,
        )
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/acf-pacf", response_model=ACFPACFResponse, summary="ACF and PACF")
def acf_pacf(request: ACFPACFRequest) -> ACFPACFResponse:
    """Compute the autocorrelation (ACF) and partial-autocorrelation (PACF) functions.

    Returns correlation values and pointwise confidence-interval bounds for
    each requested lag — useful for identifying ARIMA orders visually.
    """
    try:
        return compute_acf_pacf(
            values=request.values,
            n_lags=request.n_lags,
            alpha=request.alpha,
        )
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post(
    "/residuals",
    response_model=ResidualDiagnosticsResponse,
    summary="Residual diagnostics",
)
def residual_diagnostics(request: DiagnosticsRequest) -> ResidualDiagnosticsResponse:
    """Analyse a set of model residuals.

    Tests performed:
    - **Ljung–Box**: checks for remaining autocorrelation (white-noise test).
    - **Jarque–Bera**: checks residual normality.
    - **Durbin–Watson**: checks for first-order autocorrelation.
    """
    try:
        return analyze_residuals(residuals=request.values)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
