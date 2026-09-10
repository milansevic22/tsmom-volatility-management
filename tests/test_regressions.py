import numpy as np
import pandas as pd

from tsmom.regressions import factor_regression, regression_summary_table


def test_factor_regression_recovers_known_loading():
    rng = np.random.default_rng(7)
    n = 300
    mkt = pd.Series(rng.normal(0.005, 0.04, n), name="MKT")
    noise = rng.normal(0, 0.001, n)
    true_beta = 0.5
    excess_returns = 0.001 + true_beta * mkt + noise

    model = factor_regression(excess_returns, pd.DataFrame({"MKT": mkt}))

    assert abs(model.params["MKT"] - true_beta) < 0.05


def test_factor_regression_drops_rows_with_missing_values():
    rng = np.random.default_rng(8)
    n = 50
    mkt = pd.Series(rng.normal(0, 0.03, n), name="MKT")
    excess_returns = 0.001 + 0.5 * mkt
    excess_returns.iloc[:5] = np.nan

    model = factor_regression(excess_returns, pd.DataFrame({"MKT": mkt}))

    assert model.nobs == n - 5


def test_regression_summary_table_reports_observations_and_r_squared():
    rng = np.random.default_rng(9)
    n = 100
    mkt = pd.Series(rng.normal(0, 0.03, n), name="MKT")
    excess_returns = 0.001 + 0.3 * mkt + rng.normal(0, 0.001, n)

    model = factor_regression(excess_returns, pd.DataFrame({"MKT": mkt}))
    table = regression_summary_table({"Strategy": model})

    assert table.loc["Observations", "Strategy"] == n
    assert "R-squared" in table.index
