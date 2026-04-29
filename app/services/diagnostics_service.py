"""Diagnostics service: stationarity tests, ACF/PACF, and residual analysis."""

from __future__ import annotations

from typing import List, Optional

import numpy as np
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.stats.stattools import durbin_watson, jarque_bera
from statsmodels.tsa.stattools import acf, adfuller, pacf

from app.schemas.models import (
    ACFPACFResponse,
    ADFResponse,
    ResidualDiagnosticsResponse,
)


def run_adf_test(
    values: List[float],
    regression: str = "c",
    max_lags: Optional[int] = None,
) -> ADFResponse:
    """Run the Augmented Dickey-Fuller unit root test.

    Parameters
    ----------
    values:
        Time series observations.
    regression:
        Constant/trend specification – one of ``'c'``, ``'ct'``, ``'ctt'``, ``'n'``.
    max_lags:
        Maximum number of lags. ``None`` lets statsmodels choose automatically.
    """
    result = adfuller(values, regression=regression, maxlag=max_lags, autolag="AIC")
    adf_stat, p_value, n_lags, n_obs, critical_values = (
        result[0],
        result[1],
        result[2],
        result[3],
        result[4],
    )
    return ADFResponse(
        test_statistic=float(adf_stat),
        p_value=float(p_value),
        n_lags_used=int(n_lags),
        n_obs=int(n_obs),
        critical_values={k: float(v) for k, v in critical_values.items()},
        is_stationary=bool(p_value < 0.05),
    )


def compute_acf_pacf(
    values: List[float],
    n_lags: int = 20,
    alpha: float = 0.05,
) -> ACFPACFResponse:
    """Compute autocorrelation and partial-autocorrelation functions with confidence intervals."""
    arr = np.asarray(values, dtype=float)

    acf_vals, acf_confint = acf(arr, nlags=n_lags, alpha=alpha, fft=True)
    pacf_vals, pacf_confint = pacf(arr, nlags=n_lags, alpha=alpha)

    lags = list(range(n_lags + 1))

    return ACFPACFResponse(
        lags=lags,
        acf=acf_vals.tolist(),
        pacf=pacf_vals.tolist(),
        acf_confint_lower=acf_confint[:, 0].tolist(),
        acf_confint_upper=acf_confint[:, 1].tolist(),
        pacf_confint_lower=pacf_confint[:, 0].tolist(),
        pacf_confint_upper=pacf_confint[:, 1].tolist(),
    )


def analyze_residuals(residuals: List[float]) -> ResidualDiagnosticsResponse:
    """Run a battery of residual diagnostics.

    Tests performed
    ---------------
    * Ljung–Box test (portmanteau white-noise test)
    * Jarque–Bera normality test
    * Durbin–Watson autocorrelation test
    """
    arr = np.asarray(residuals, dtype=float)

    # Ljung-Box: test at lag 10 (or fewer if series is short)
    n_lags_lb = min(10, len(arr) // 5)
    lb_result = acorr_ljungbox(arr, lags=[n_lags_lb], return_df=True)
    lb_stat = float(lb_result["lb_stat"].iloc[-1])
    lb_pvalue = float(lb_result["lb_pvalue"].iloc[-1])

    # Jarque-Bera
    jb_stat, jb_pvalue, _, _ = jarque_bera(arr)

    # Durbin-Watson
    dw_stat = float(durbin_watson(arr))

    return ResidualDiagnosticsResponse(
        ljung_box_stat=lb_stat,
        ljung_box_p_value=lb_pvalue,
        jarque_bera_stat=float(jb_stat),
        jarque_bera_p_value=float(jb_pvalue),
        durbin_watson=dw_stat,
        residuals_mean=float(arr.mean()),
        residuals_std=float(arr.std()),
        is_white_noise=bool(lb_pvalue > 0.05),
        is_normal=bool(jb_pvalue > 0.05),
    )
