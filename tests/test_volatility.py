import numpy as np
import pandas as pd
import pytest

from tsmom.volatility import EWMA_DELTA, TRADING_DAYS_PER_YEAR, ewma_daily_volatility, month_end_volatility


def test_ewma_volatility_is_positive_and_finite():
    dates = pd.date_range("2020-01-01", periods=500, freq="B")
    rng = np.random.default_rng(1)
    returns = pd.DataFrame({"A": rng.normal(0, 0.01, len(dates))}, index=dates)

    vol = ewma_daily_volatility(returns)

    # The very first observation has zero deviation from its own EWMA mean
    # by construction; volatility is meaningfully positive from then on.
    assert (vol.iloc[1:].dropna() > 0).all().all()
    assert np.isfinite(vol.dropna().to_numpy()).all()


def test_ewma_volatility_scales_with_return_scale():
    dates = pd.date_range("2020-01-01", periods=500, freq="B")
    rng = np.random.default_rng(2)
    base = rng.normal(0, 0.01, len(dates))
    low_vol = pd.DataFrame({"A": base}, index=dates)
    high_vol = pd.DataFrame({"A": base * 3}, index=dates)

    vol_low = ewma_daily_volatility(low_vol).iloc[-1]["A"]
    vol_high = ewma_daily_volatility(high_vol).iloc[-1]["A"]

    assert vol_high == pytest.approx(vol_low * 3)


def test_ewma_matches_manual_recursion_on_constant_return():
    dates = pd.date_range("2020-01-01", periods=5, freq="B")
    returns = pd.DataFrame({"A": [0.01, 0.01, 0.01, 0.01, 0.01]}, index=dates)

    vol = ewma_daily_volatility(returns)

    # A constant series has zero deviation from its own EWMA mean at every step.
    assert (vol.iloc[1:] == 0).all().all()


def test_month_end_volatility_takes_last_observation_per_month():
    dates = pd.date_range("2020-01-01", periods=40, freq="B")
    values = np.arange(len(dates), dtype=float)
    daily_vol = pd.DataFrame({"A": values}, index=dates)

    monthly = month_end_volatility(daily_vol)

    for month_end in monthly.index:
        in_month = daily_vol.loc[:month_end]
        assert monthly.loc[month_end, "A"] == in_month["A"].iloc[-1]


def test_constants_match_moskowitz_ooi_pedersen_specification():
    assert TRADING_DAYS_PER_YEAR == 261
    assert abs(EWMA_DELTA - 60 / 61) < 1e-12
