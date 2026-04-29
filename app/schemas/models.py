"""Request and response schemas for the Khawarizmi Engine API."""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field, model_validator


# ---------------------------------------------------------------------------
# Shared
# ---------------------------------------------------------------------------

class TimeSeriesData(BaseModel):
    """Raw time series values supplied by the caller."""

    values: List[float] = Field(
        ...,
        min_length=10,
        description="Observed time series values (chronological order).",
    )
    dates: Optional[List[str]] = Field(
        None,
        description=(
            "Optional ISO-8601 date strings aligned with *values*. "
            "When omitted the engine uses an integer index."
        ),
    )
    frequency: Optional[int] = Field(
        None,
        ge=1,
        description=(
            "Seasonal period (e.g. 12 for monthly, 4 for quarterly). "
            "Required for SARIMA."
        ),
    )


# ---------------------------------------------------------------------------
# ARIMA
# ---------------------------------------------------------------------------

class ARIMAOrder(BaseModel):
    p: int = Field(..., ge=0, le=20, description="AR order")
    d: int = Field(..., ge=0, le=2, description="Differencing order")
    q: int = Field(..., ge=0, le=20, description="MA order")


class ARIMAFitRequest(BaseModel):
    data: TimeSeriesData
    order: ARIMAOrder
    trend: Optional[str] = Field(
        "n",
        description="Trend component: 'n' (none), 'c' (constant), 't' (linear trend), 'ct'.",
    )


class ForecastRequest(BaseModel):
    data: TimeSeriesData
    order: ARIMAOrder
    steps: int = Field(10, ge=1, le=1000, description="Number of steps ahead to forecast.")
    alpha: float = Field(0.05, gt=0, lt=1, description="Significance level for confidence intervals.")
    trend: Optional[str] = Field("n", description="Trend component passed to ARIMA.")


# ---------------------------------------------------------------------------
# SARIMA
# ---------------------------------------------------------------------------

class SARIMAOrder(BaseModel):
    p: int = Field(..., ge=0, le=20)
    d: int = Field(..., ge=0, le=2)
    q: int = Field(..., ge=0, le=20)
    P: int = Field(..., ge=0, le=10, description="Seasonal AR order")
    D: int = Field(..., ge=0, le=2, description="Seasonal differencing order")
    Q: int = Field(..., ge=0, le=10, description="Seasonal MA order")
    s: int = Field(..., ge=2, description="Seasonal period")


class SARIMAFitRequest(BaseModel):
    data: TimeSeriesData
    order: SARIMAOrder
    trend: Optional[str] = Field("n", description="Trend component.")


class SARIMAForecastRequest(BaseModel):
    data: TimeSeriesData
    order: SARIMAOrder
    steps: int = Field(10, ge=1, le=1000)
    alpha: float = Field(0.05, gt=0, lt=1)
    trend: Optional[str] = Field("n")


# ---------------------------------------------------------------------------
# Auto-ARIMA
# ---------------------------------------------------------------------------

class AutoARIMARequest(BaseModel):
    data: TimeSeriesData
    max_p: int = Field(5, ge=0, le=10)
    max_d: int = Field(2, ge=0, le=2)
    max_q: int = Field(5, ge=0, le=10)
    seasonal: bool = Field(False, description="Whether to consider seasonal components.")
    information_criterion: str = Field(
        "aic", description="Model selection criterion: 'aic', 'bic', or 'hqic'."
    )
    steps: int = Field(10, ge=1, le=1000, description="Forecast horizon after fitting.")
    alpha: float = Field(0.05, gt=0, lt=1)

    @model_validator(mode="after")
    def seasonal_needs_frequency(self) -> "AutoARIMARequest":
        if self.seasonal and self.data.frequency is None:
            raise ValueError("data.frequency must be set when seasonal=True.")
        return self


# ---------------------------------------------------------------------------
# Diagnostics
# ---------------------------------------------------------------------------

class DiagnosticsRequest(BaseModel):
    values: List[float] = Field(..., min_length=10)


class ADFRequest(BaseModel):
    values: List[float] = Field(..., min_length=10)
    regression: str = Field(
        "c",
        description="Regression type for ADF: 'c', 'ct', 'ctt', or 'n'.",
    )
    max_lags: Optional[int] = Field(None, ge=0)


class ACFPACFRequest(BaseModel):
    values: List[float] = Field(..., min_length=10)
    n_lags: int = Field(20, ge=1, le=500)
    alpha: float = Field(0.05, gt=0, lt=1)


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class ModelSummary(BaseModel):
    aic: float
    bic: float
    hqic: float
    log_likelihood: float
    params: dict
    p_values: dict
    std_errors: dict
    n_obs: int


class ForecastPoint(BaseModel):
    step: int
    forecast: float
    lower_ci: float
    upper_ci: float


class ForecastResponse(BaseModel):
    fitted: List[float]
    residuals: List[float]
    summary: ModelSummary
    forecast: List[ForecastPoint]


class FitResponse(BaseModel):
    fitted: List[float]
    residuals: List[float]
    summary: ModelSummary


class ADFResponse(BaseModel):
    test_statistic: float
    p_value: float
    n_lags_used: int
    n_obs: int
    critical_values: dict
    is_stationary: bool


class ACFPACFResponse(BaseModel):
    lags: List[int]
    acf: List[float]
    pacf: List[float]
    acf_confint_lower: List[float]
    acf_confint_upper: List[float]
    pacf_confint_lower: List[float]
    pacf_confint_upper: List[float]


class ResidualDiagnosticsResponse(BaseModel):
    ljung_box_stat: float
    ljung_box_p_value: float
    jarque_bera_stat: float
    jarque_bera_p_value: float
    durbin_watson: float
    residuals_mean: float
    residuals_std: float
    is_white_noise: bool
    is_normal: bool


class AutoARIMAResponse(BaseModel):
    best_order: dict
    summary: ModelSummary
    fitted: List[float]
    residuals: List[float]
    forecast: List[ForecastPoint]
    search_results: List[dict]
