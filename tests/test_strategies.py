import numpy as np
import pandas as pd
import pytest

from tsmom.signals import momentum_signal
from tsmom.strategies import (
    asset_positions,
    build_vm_tsmom,
    passive_benchmark,
    portfolio_weights,
    realized_variance,
    signal_only_portfolio,
    tsmom_asset_returns,
    tsmom_portfolio,
    vm_portfolio_weights,
    volatility_managed_returns,
)
from tsmom.volatility import ewma_daily_volatility, month_end_volatility


def test_passive_benchmark_is_cross_sectional_mean():
    dates = pd.date_range("2020-01-31", periods=3, freq="ME")
    returns = pd.DataFrame({"A": [0.1, 0.2, 0.3], "B": [0.3, 0.0, -0.1]}, index=dates)

    benchmark = passive_benchmark(returns)

    assert benchmark.tolist() == pytest.approx([0.2, 0.1, 0.1])


def test_asset_positions_scale_inversely_with_volatility():
    vol = pd.DataFrame({"A": [0.1, 0.2], "B": [0.4, 0.4]})
    positions = asset_positions(vol, target_vol=0.40)

    assert positions["A"].tolist() == pytest.approx([4.0, 2.0])
    assert positions["B"].tolist() == pytest.approx([1.0, 1.0])


def test_tsmom_asset_returns_use_one_month_lagged_signal_and_position():
    dates = pd.date_range("2020-01-31", periods=4, freq="ME")
    returns = pd.DataFrame({"A": [0.01, 0.02, -0.01, 0.03]}, index=dates)
    signal = pd.DataFrame({"A": [1.0, 1.0, -1.0, -1.0]}, index=dates)
    volatility = pd.DataFrame({"A": [0.2, 0.2, 0.2, 0.2]}, index=dates)

    asset_returns = tsmom_asset_returns(returns, signal, volatility, target_vol=0.40)

    # Month 0 has no prior signal/position to lag in from -> NaN.
    assert asset_returns["A"].iloc[0] is np.nan or pd.isna(asset_returns["A"].iloc[0])
    # Month 1 return uses month-0 signal (+1) and month-0 position (0.40/0.2=2.0).
    assert asset_returns["A"].iloc[1] == pytest.approx(1.0 * 2.0 * 0.02)
    # Month 3 return uses month-2 signal (-1) and month-2 position (2.0).
    assert asset_returns["A"].iloc[3] == pytest.approx(-1.0 * 2.0 * 0.03)


def test_tsmom_has_no_look_ahead_bias(synthetic_monthly_returns):
    """Changing a future return must not change today's TSMOM contribution."""
    returns = synthetic_monthly_returns
    signal = momentum_signal(returns, lookback=12)
    vol = pd.DataFrame(
        np.full(returns.shape, 0.15), index=returns.index, columns=returns.columns
    )

    baseline = tsmom_asset_returns(returns, signal, vol)

    perturbed_returns = returns.copy()
    perturbed_returns.iloc[-1] += 10.0  # drastically change the final observation only
    perturbed = tsmom_asset_returns(perturbed_returns, signal, vol)

    pd.testing.assert_frame_equal(baseline.iloc[:-1], perturbed.iloc[:-1])


def test_signal_only_portfolio_has_no_asset_level_vol_scaling():
    dates = pd.date_range("2020-01-31", periods=3, freq="ME")
    returns = pd.DataFrame({"A": [0.01, 0.02, 0.03], "B": [0.01, 0.02, 0.03]}, index=dates)
    signal = pd.DataFrame({"A": [1.0, 1.0, 1.0], "B": [1.0, 1.0, 1.0]}, index=dates)

    base = signal_only_portfolio(returns, signal)

    # With identical assets and a constant +1 signal, the portfolio equals
    # the current-month return multiplied by the one-month-lagged signal
    # (undefined in month 0, when there is no prior signal), with no
    # volatility scaling applied.
    expected = returns["A"].copy()
    expected.iloc[0] = np.nan
    pd.testing.assert_series_equal(base, expected, check_names=False)


def test_realized_variance_is_non_negative(synthetic_monthly_returns, synthetic_daily_returns):
    signal = momentum_signal(synthetic_monthly_returns, lookback=12)
    rv = realized_variance(synthetic_daily_returns, signal)

    assert (rv.dropna() >= 0).all()


def test_volatility_managed_returns_matches_base_volatility():
    dates = pd.date_range("2020-01-31", periods=60, freq="ME")
    rng = np.random.default_rng(3)
    base = pd.Series(rng.normal(0.005, 0.03, len(dates)), index=dates)
    realized_var = pd.Series(rng.uniform(0.0005, 0.002, len(dates)), index=dates)

    result = volatility_managed_returns(base, realized_var)

    common = pd.concat([base, result.returns], axis=1).dropna()
    assert common.iloc[:, 1].std() == pytest.approx(common.iloc[:, 0].std(), rel=1e-9)


def test_build_vm_tsmom_uses_signal_only_base_not_asset_scaled_tsmom(
    synthetic_monthly_returns, synthetic_daily_returns
):
    """VM-TSMOM's base is signal-only; it must differ from the asset-vol-scaled TSMOM base."""
    signal = momentum_signal(synthetic_monthly_returns, lookback=12)

    vol = month_end_volatility(ewma_daily_volatility(synthetic_daily_returns))
    tsmom_returns = tsmom_asset_returns(synthetic_monthly_returns, signal, vol)
    tsmom = tsmom_portfolio(tsmom_returns)

    vm_result = build_vm_tsmom(synthetic_monthly_returns, synthetic_daily_returns, signal)

    common = pd.concat([tsmom.rename("tsmom"), vm_result.returns.rename("vm")], axis=1).dropna()
    assert not np.allclose(common["tsmom"], common["vm"])


def test_portfolio_weights_and_vm_weights_produce_turnover_series(synthetic_monthly_returns, synthetic_daily_returns):
    signal = momentum_signal(synthetic_monthly_returns, lookback=12)
    vol = month_end_volatility(ewma_daily_volatility(synthetic_daily_returns))

    weights = portfolio_weights(signal, vol)
    vm_result = build_vm_tsmom(synthetic_monthly_returns, synthetic_daily_returns, signal)
    vm_weights = vm_portfolio_weights(weights, vm_result.weight)

    assert weights.shape == vm_weights.shape
    assert weights.dropna(how="all").shape[0] > 0
