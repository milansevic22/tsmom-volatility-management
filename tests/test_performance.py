import numpy as np
import pandas as pd
import pytest

from tsmom.performance import (
    annualized_return,
    annualized_volatility,
    apply_transaction_costs,
    block_bootstrap_sharpe_test,
    max_drawdown,
    performance_summary,
    sharpe_ratio,
    turnover,
)


def test_annualized_return_and_volatility_scale_monthly_by_twelve():
    dates = pd.date_range("2020-01-31", periods=24, freq="ME")
    returns = pd.Series([0.01] * 24, index=dates)

    assert annualized_return(returns) == pytest.approx(0.12)
    assert annualized_volatility(returns) == pytest.approx(0.0)


def test_sharpe_ratio_of_constant_positive_return_is_infinite():
    dates = pd.date_range("2020-01-31", periods=24, freq="ME")
    returns = pd.Series([0.01] * 24, index=dates)

    assert np.isinf(sharpe_ratio(returns))


def test_max_drawdown_on_known_path():
    dates = pd.date_range("2020-01-31", periods=4, freq="ME")
    # Growth path: 100 -> 110 -> 88 -> 96.8 => trough at -20% from the peak of 110.
    returns = pd.Series([0.10, -0.20, 0.10], index=dates[1:])

    dd = max_drawdown(returns)

    assert dd == pytest.approx(-0.20)


def test_performance_summary_has_expected_columns_and_shape():
    dates = pd.date_range("2020-01-31", periods=36, freq="ME")
    rng = np.random.default_rng(4)
    returns = pd.DataFrame(
        {"Strategy1": rng.normal(0.005, 0.02, 36), "Strategy2": rng.normal(0.003, 0.03, 36)},
        index=dates,
    )

    summary = performance_summary(returns)

    assert set(summary.columns) == {"Annual Return", "Volatility", "Sharpe Ratio", "Max Drawdown"}
    assert list(summary.index) == ["Strategy1", "Strategy2"]


def test_turnover_is_half_absolute_weight_change():
    dates = pd.date_range("2020-01-31", periods=3, freq="ME")
    weights = pd.DataFrame({"A": [0.5, 1.0, 1.0], "B": [0.5, 0.0, 1.0]}, index=dates)

    result = turnover(weights)

    # Month 1: |1.0-0.5| + |0.0-0.5| = 1.0 -> /2 = 0.5
    # Month 2: |1.0-1.0| + |1.0-0.0| = 1.0 -> /2 = 0.5
    assert result.iloc[1] == pytest.approx(0.5)
    assert result.iloc[2] == pytest.approx(0.5)


def test_apply_transaction_costs_deducts_turnover_times_cost():
    dates = pd.date_range("2020-01-31", periods=3, freq="ME")
    gross = pd.Series([0.02, 0.02, 0.02], index=dates)
    turnover_series = pd.Series([1.0, 0.5, 2.0], index=dates)

    net = apply_transaction_costs(gross, turnover_series, cost_bps=10)

    assert net.tolist() == pytest.approx([0.02 - 0.0010, 0.02 - 0.0005, 0.02 - 0.0020])


def test_bootstrap_sharpe_test_is_deterministic_given_seed():
    rng = np.random.default_rng(5)
    r1 = pd.Series(rng.normal(0.01, 0.03, 120))
    r2 = pd.Series(rng.normal(0.005, 0.03, 120))

    diff_a, p_a = block_bootstrap_sharpe_test(r1, r2, n_boot=500, seed=42)
    diff_b, p_b = block_bootstrap_sharpe_test(r1, r2, n_boot=500, seed=42)

    assert diff_a == diff_b
    assert p_a == p_b


def test_bootstrap_sharpe_test_identical_series_gives_zero_difference():
    rng = np.random.default_rng(6)
    r1 = pd.Series(rng.normal(0.01, 0.03, 100))

    diff, p_value = block_bootstrap_sharpe_test(r1, r1, n_boot=200, seed=1)

    assert diff == pytest.approx(0.0)
    assert p_value == pytest.approx(1.0)
