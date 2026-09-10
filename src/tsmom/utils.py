"""Small shared helpers for aligning monthly time series."""

from __future__ import annotations

import pandas as pd


def to_month_end(frame: pd.DataFrame | pd.Series) -> pd.DataFrame | pd.Series:
    """Normalise a datetime index to month-end timestamps."""
    frame = frame.copy()
    frame.index = pd.to_datetime(frame.index).to_period("M").to_timestamp("M")
    return frame


def to_month_start(frame: pd.DataFrame | pd.Series) -> pd.DataFrame | pd.Series:
    """Normalise a datetime index to month-start timestamps.

    Strategy return series carry a month-end index throughout, but the
    factor-regression datasets (Fama-French factors, MSCI/BOND/GSCI
    benchmark returns) are keyed on month-start dates. This aligns a
    month-end-indexed series onto the month-start convention before
    merging it with factor data.
    """
    frame = frame.copy()
    frame.index = pd.to_datetime(frame.index).to_period("M").to_timestamp()
    return frame


def align_monthly(*frames: pd.DataFrame | pd.Series) -> list[pd.DataFrame | pd.Series]:
    """Normalise each frame's index to month-end and restrict all to their common dates.

    Used before combining returns, signals, and volatility estimates that
    may have been resampled or lagged slightly differently.
    """
    normalized = [to_month_end(frame).sort_index() for frame in frames]
    common_index = normalized[0].index
    for frame in normalized[1:]:
        common_index = common_index.intersection(frame.index)
    return [frame.reindex(common_index) for frame in normalized]
