"""Time-series momentum signal construction."""

from __future__ import annotations

import numpy as np
import pandas as pd


def trailing_cumulative_return(returns: pd.DataFrame, lookback: int = 12) -> pd.DataFrame:
    """Rolling ``lookback``-period cumulative (compounded) return, per asset."""
    return (1 + returns).rolling(lookback).apply(np.prod, raw=True) - 1


def momentum_signal(returns: pd.DataFrame, lookback: int = 12) -> pd.DataFrame:
    """Time-series momentum signal: the sign of the trailing cumulative return.

    +1 for positive trailing performance, -1 for negative, 0 (no position)
    where the trailing return is exactly zero or undefined. The signal is
    contemporaneous with month ``t``; callers apply the one-month
    implementation lag (``signal.shift(1)``) when constructing positions to
    avoid look-ahead bias.
    """
    return np.sign(trailing_cumulative_return(returns, lookback))
