import numpy as np
import pandas as pd
import pytest

from tsmom.signals import momentum_signal, trailing_cumulative_return


def test_trailing_cumulative_return_matches_manual_compounding():
    dates = pd.date_range("2020-01-31", periods=13, freq="ME")
    monthly_return = 0.01
    returns = pd.DataFrame({"A": [monthly_return] * 13}, index=dates)

    cum = trailing_cumulative_return(returns, lookback=12)

    expected = (1 + monthly_return) ** 12 - 1
    assert cum.iloc[-1]["A"] == pytest.approx(expected)


def test_momentum_signal_is_sign_of_trailing_return():
    dates = pd.date_range("2020-01-31", periods=14, freq="ME")
    returns = pd.DataFrame({"UP": [0.02] * 14, "DOWN": [-0.02] * 14}, index=dates)

    signal = momentum_signal(returns, lookback=12)

    valid = signal.dropna()
    assert (valid["UP"] == 1).all()
    assert (valid["DOWN"] == -1).all()


def test_momentum_signal_first_lookback_months_are_nan():
    dates = pd.date_range("2020-01-31", periods=12, freq="ME")
    returns = pd.DataFrame({"A": np.linspace(0.01, 0.05, 12)}, index=dates)

    signal = momentum_signal(returns, lookback=12)

    assert signal["A"].iloc[:11].isna().all()
    assert signal["A"].iloc[11:].notna().all()
