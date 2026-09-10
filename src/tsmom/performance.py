"""Performance statistics, transaction costs, and Sharpe-ratio robustness testing."""

from __future__ import annotations

import numpy as np
import pandas as pd

PERIODS_PER_YEAR = 12


def annualized_return(returns: pd.Series | pd.DataFrame, periods_per_year: int = PERIODS_PER_YEAR):
    return returns.mean() * periods_per_year


def annualized_volatility(returns: pd.Series | pd.DataFrame, periods_per_year: int = PERIODS_PER_YEAR):
    return returns.std() * np.sqrt(periods_per_year)


def sharpe_ratio(returns: pd.Series | pd.DataFrame, periods_per_year: int = PERIODS_PER_YEAR):
    return annualized_return(returns, periods_per_year) / annualized_volatility(returns, periods_per_year)


def cumulative_growth(returns: pd.Series | pd.DataFrame, start_value: float = 100.0):
    """Growth of an initial investment, compounding period returns."""
    return start_value * (1 + returns).cumprod()


def drawdown(returns: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    growth = (1 + returns).cumprod()
    return growth / growth.cummax() - 1


def max_drawdown(returns: pd.Series | pd.DataFrame):
    return drawdown(returns).min()


def performance_summary(returns: pd.DataFrame, periods_per_year: int = PERIODS_PER_YEAR) -> pd.DataFrame:
    """Annualised return, volatility, Sharpe ratio, and max drawdown for each column."""
    return pd.DataFrame(
        {
            "Annual Return": annualized_return(returns, periods_per_year),
            "Volatility": annualized_volatility(returns, periods_per_year),
            "Sharpe Ratio": sharpe_ratio(returns, periods_per_year),
            "Max Drawdown": max_drawdown(returns),
        }
    )


def turnover(weights: pd.DataFrame) -> pd.Series:
    """One-way monthly portfolio turnover: half the sum of absolute weight changes."""
    return weights.diff().abs().sum(axis=1) / 2


def apply_transaction_costs(gross_returns: pd.Series, turnover_series: pd.Series, cost_bps: float) -> pd.Series:
    """Net returns after deducting a per-unit-turnover cost, in basis points."""
    cost = cost_bps / 10_000
    return gross_returns - cost * turnover_series


def block_bootstrap_sharpe_test(
    r1: pd.Series,
    r2: pd.Series,
    n_boot: int = 10_000,
    seed: int = 42,
) -> tuple[float, float]:
    """Circular block bootstrap test of H0: Sharpe(r1) == Sharpe(r2).

    Follows Ledoit and Wolf (2008), with block length ``sqrt(T)`` per
    Politis and Romano (1994). Returns the observed Sharpe-ratio difference
    and a two-sided bootstrap p-value.
    """
    rng = np.random.RandomState(seed)
    r1_arr, r2_arr = np.asarray(r1), np.asarray(r2)
    n_obs = len(r1_arr)
    block_size = max(int(np.sqrt(n_obs)), 1)
    n_blocks = int(np.ceil(n_obs / block_size))

    obs_diff = sharpe_ratio(pd.Series(r1_arr)) - sharpe_ratio(pd.Series(r2_arr))

    r1_centered = r1_arr - r1_arr.mean()
    r2_centered = r2_arr - r2_arr.mean()

    boot_diffs = np.empty(n_boot)
    for i in range(n_boot):
        starts = rng.randint(0, n_obs, size=n_blocks)
        idx = np.concatenate([np.arange(s, s + block_size) % n_obs for s in starts])[:n_obs]
        boot_diffs[i] = sharpe_ratio(pd.Series(r1_centered[idx])) - sharpe_ratio(pd.Series(r2_centered[idx]))

    p_value = np.mean(np.abs(boot_diffs) >= np.abs(obs_diff))
    return float(obs_diff), float(p_value)
