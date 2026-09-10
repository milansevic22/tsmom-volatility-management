"""Portfolio construction: passive benchmark, TSMOM, and VM-TSMOM.

Important methodological note
------------------------------
TSMOM and VM-TSMOM are built from *different* base portfolios, not from a
single base with an optional overlay:

- TSMOM applies asset-level inverse-volatility scaling (target volatility
  ``kappa``) to each contract before equal-weight averaging. This is the
  Moskowitz, Ooi and Pedersen (2012) cross-asset risk normalisation.
- VM-TSMOM instead scales a *signal-only, equal-weight* momentum portfolio
  (no per-asset volatility scaling) by the inverse of its own lagged
  portfolio-level realised variance, following Moreira and Muir (2017).
  A constant ``c`` rescales the result so its unconditional volatility
  matches the signal-only base.

Comparing TSMOM against VM-TSMOM therefore reflects both the effect of
portfolio-level variance timing and a difference in how the underlying base
portfolio is constructed. This is the construction used in the dissertation
and is preserved exactly here; see Section 4 of the dissertation and
``docs/validation.md`` for further discussion.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

DEFAULT_TARGET_VOL = 0.40


def _align_columns(*frames: pd.DataFrame) -> list[pd.DataFrame]:
    common = frames[0].columns
    for frame in frames[1:]:
        common = common.intersection(frame.columns)
    return [frame[common] for frame in frames]


def passive_benchmark(returns: pd.DataFrame) -> pd.Series:
    """Equal-weight passive benchmark: the cross-sectional mean return."""
    return returns.mean(axis=1, skipna=True)


def asset_positions(volatility: pd.DataFrame, target_vol: float = DEFAULT_TARGET_VOL) -> pd.DataFrame:
    """Inverse-volatility position size per asset, targeting ``target_vol`` annualised."""
    return target_vol / volatility


def tsmom_asset_returns(
    returns: pd.DataFrame,
    signal: pd.DataFrame,
    volatility: pd.DataFrame,
    target_vol: float = DEFAULT_TARGET_VOL,
) -> pd.DataFrame:
    """Per-asset TSMOM return contributions.

    Both the signal and the volatility-based position are lagged by one
    period relative to the return they are applied to, eliminating
    look-ahead bias.
    """
    returns, signal, volatility = _align_columns(returns, signal, volatility)
    position = asset_positions(volatility, target_vol)
    return signal.shift(1) * position.shift(1) * returns


def tsmom_portfolio(asset_returns: pd.DataFrame) -> pd.Series:
    """Equal-weight TSMOM portfolio return from per-asset contributions."""
    return asset_returns.mean(axis=1, skipna=True)


def signal_only_portfolio(returns: pd.DataFrame, signal: pd.DataFrame) -> pd.Series:
    """Equal-weight momentum portfolio *without* asset-level volatility scaling.

    This is the base portfolio that VM-TSMOM's variance-timing overlay is
    applied to, following Moreira and Muir (2017).
    """
    returns, signal = _align_columns(returns, signal)
    asset_returns = signal.shift(1) * returns
    return asset_returns.mean(axis=1, skipna=True)


def realized_variance(daily_returns: pd.DataFrame, monthly_signal: pd.DataFrame) -> pd.Series:
    """Monthly realised variance of the signal-only daily portfolio.

    Each day's signal-only portfolio return uses the momentum signal known
    at the start of that month (the prior month's signal). Realised
    variance for a month is the mean of squared daily portfolio returns
    within that month.
    """
    daily_returns, monthly_signal = _align_columns(daily_returns, monthly_signal)
    daily_returns = daily_returns.sort_index()
    daily_returns.index = pd.to_datetime(daily_returns.index)

    signal_lag = monthly_signal.shift(1).copy()
    signal_lag.index = signal_lag.index.to_period("M")
    signal_daily = signal_lag.reindex(daily_returns.index.to_period("M"))
    signal_daily.index = daily_returns.index

    daily_portfolio = (signal_daily * daily_returns).mean(axis=1, skipna=True)
    rv = daily_portfolio.groupby(daily_portfolio.index.to_period("M")).apply(lambda x: np.mean(x**2))
    rv.index = rv.index.to_timestamp("M")
    rv.name = "RV"
    return rv


@dataclass
class VolatilityManagedResult:
    returns: pd.Series
    weight: pd.Series
    scale_constant: float
    realized_variance: pd.Series


def volatility_managed_returns(base_returns: pd.Series, realized_var: pd.Series) -> VolatilityManagedResult:
    """Scale ``base_returns`` inversely by its own lagged realised variance.

    Following Moreira and Muir (2017): ``f^sigma_t = (c / RV_{t-1}) * f_t``,
    where ``c`` is chosen so that the managed series has the same
    unconditional volatility as the base series over the common sample.
    """
    data = pd.concat([base_returns.rename("base"), realized_var.rename("RV")], axis=1).dropna()
    vm_raw = data["base"] / data["RV"].shift(1)

    valid = pd.concat([data["base"], vm_raw.rename("vm_raw")], axis=1).dropna()
    scale_constant = valid["base"].std() / valid["vm_raw"].std()

    vm_returns = (scale_constant * vm_raw).dropna()
    weight = (scale_constant / data["RV"].shift(1)).reindex(vm_raw.index)

    return VolatilityManagedResult(
        returns=vm_returns,
        weight=weight,
        scale_constant=scale_constant,
        realized_variance=data["RV"],
    )


def build_vm_tsmom(
    returns: pd.DataFrame,
    daily_returns: pd.DataFrame,
    signal: pd.DataFrame,
) -> VolatilityManagedResult:
    """End-to-end VM-TSMOM construction: signal-only base -> realised variance -> managed returns."""
    base = signal_only_portfolio(returns, signal)
    rv = realized_variance(daily_returns, signal)
    return volatility_managed_returns(base, rv)


def portfolio_weights(signal: pd.DataFrame, volatility: pd.DataFrame, target_vol: float = DEFAULT_TARGET_VOL) -> pd.DataFrame:
    """Per-asset TSMOM portfolio weights (lagged signal x lagged position, divided by breadth).

    Dividing by the number of active contracts each month converts the raw
    signal-times-position exposure into a portfolio weight comparable
    across months with a varying investable universe.
    """
    signal, volatility = _align_columns(signal, volatility)
    position = asset_positions(volatility, target_vol)
    raw_weights = signal.shift(1) * position.shift(1)
    active_assets = raw_weights.notna().sum(axis=1)
    return raw_weights.div(active_assets, axis=0)


def vm_portfolio_weights(tsmom_weights: pd.DataFrame, vm_weight: pd.Series) -> pd.DataFrame:
    """Apply the VM-TSMOM scaling weight to TSMOM per-asset portfolio weights."""
    return tsmom_weights.mul(vm_weight.reindex(tsmom_weights.index), axis=0)
