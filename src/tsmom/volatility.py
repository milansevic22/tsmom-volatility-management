"""Ex-ante volatility estimation.

Follows Moskowitz, Ooi and Pedersen (2012): an exponentially weighted
moving average of squared daily returns, annualised, sampled at month-end.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

EWMA_DELTA = 60 / 61
TRADING_DAYS_PER_YEAR = 261


def ewma_daily_volatility(
    daily_returns: pd.DataFrame,
    delta: float = EWMA_DELTA,
    trading_days: int = TRADING_DAYS_PER_YEAR,
) -> pd.DataFrame:
    """Annualised EWMA volatility estimate from daily returns.

    ``delta`` is the decay parameter (weight retained per day); the
    equivalent ``pandas.ewm`` smoothing factor is ``alpha = 1 - delta``.
    """
    alpha = 1 - delta
    ewma_mean = daily_returns.ewm(alpha=alpha, adjust=False).mean()
    ewma_var = ((daily_returns - ewma_mean) ** 2).ewm(alpha=alpha, adjust=False).mean()
    return np.sqrt(trading_days * ewma_var)


def month_end_volatility(daily_volatility: pd.DataFrame) -> pd.DataFrame:
    """Sample the daily volatility estimate at the last observation of each month."""
    return daily_volatility.resample("ME").last()
