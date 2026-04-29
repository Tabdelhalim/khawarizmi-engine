"""Shared test fixtures and helpers."""

from __future__ import annotations

import math
from typing import List

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


# ---------------------------------------------------------------------------
# Deterministic synthetic time series
# ---------------------------------------------------------------------------

def make_ar1(n: int = 100, phi: float = 0.7, seed: int = 42) -> List[float]:
    """Generate a stationary AR(1) process."""
    rng = np.random.default_rng(seed)
    y = np.zeros(n)
    eps = rng.normal(0, 1, n)
    for t in range(1, n):
        y[t] = phi * y[t - 1] + eps[t]
    return y.tolist()


def make_seasonal(
    n: int = 120,
    period: int = 12,
    phi: float = 0.6,
    seed: int = 42,
) -> List[float]:
    """Generate a series with a deterministic seasonal pattern plus AR(1) noise."""
    rng = np.random.default_rng(seed)
    t = np.arange(n)
    season = 5 * np.sin(2 * math.pi * t / period)
    noise = np.zeros(n)
    eps = rng.normal(0, 0.5, n)
    for i in range(1, n):
        noise[i] = phi * noise[i - 1] + eps[i]
    return (season + noise).tolist()


def make_random_walk(n: int = 100, seed: int = 42) -> List[float]:
    """Generate a random walk (non-stationary I(1) process)."""
    rng = np.random.default_rng(seed)
    eps = rng.normal(0, 1, n)
    return np.cumsum(eps).tolist()
