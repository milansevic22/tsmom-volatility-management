"""Synthetic fixtures shared across the test suite.

All fixtures are synthetic (seeded random data or hand-built toy series) and
are never presented as research evidence — they exist only to exercise the
code paths without requiring licensed Bloomberg data.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def rng() -> np.random.Generator:
    return np.random.default_rng(0)


@pytest.fixture
def synthetic_monthly_returns(rng: np.random.Generator) -> pd.DataFrame:
    """~15 years of synthetic monthly returns for a small multi-asset universe."""
    dates = pd.date_range("2000-01-31", periods=180, freq="ME")
    tickers = ["ASSET_A", "ASSET_B", "ASSET_C", "ASSET_D"]
    data = rng.normal(loc=0.004, scale=0.05, size=(len(dates), len(tickers)))
    return pd.DataFrame(data, index=dates, columns=tickers)


@pytest.fixture
def synthetic_daily_returns(rng: np.random.Generator, synthetic_monthly_returns: pd.DataFrame) -> pd.DataFrame:
    """Daily returns spanning the same window and columns as the monthly fixture."""
    dates = pd.date_range("2000-01-01", "2014-12-31", freq="B")
    data = rng.normal(loc=0.0002, scale=0.01, size=(len(dates), synthetic_monthly_returns.shape[1]))
    return pd.DataFrame(data, index=dates, columns=synthetic_monthly_returns.columns)
