"""Factor regressions with Newey-West HAC standard errors."""

from __future__ import annotations

import pandas as pd
import statsmodels.api as sm
from statsmodels.regression.linear_model import RegressionResultsWrapper

DEFAULT_HAC_LAGS = 12


def factor_regression(
    excess_returns: pd.Series,
    factors: pd.DataFrame,
    hac_lags: int = DEFAULT_HAC_LAGS,
) -> RegressionResultsWrapper:
    """OLS of excess returns on risk factors, with Newey-West HAC standard errors.

    Rows with any missing value in ``excess_returns`` or ``factors`` are
    dropped before estimation, matching how the strategy and factor series
    are merged elsewhere in the pipeline.
    """
    data = pd.concat([excess_returns.rename("y"), factors], axis=1).dropna()
    y = data["y"]
    X = sm.add_constant(data[factors.columns])
    return sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": hac_lags})


def regression_summary_table(models: dict[str, RegressionResultsWrapper]) -> pd.DataFrame:
    """Coefficient / standard-error / significance table across one or more fitted models."""

    def stars(p_value: float) -> str:
        if p_value < 0.01:
            return "***"
        if p_value < 0.05:
            return "**"
        if p_value < 0.1:
            return "*"
        return ""

    variables = list(next(iter(models.values())).params.index)
    rows = []
    for var in variables:
        coef_row = {"Variable": var}
        se_row = {"Variable": ""}
        for label, model in models.items():
            coef_row[label] = f"{model.params[var]:.4f}{stars(model.pvalues[var])}"
            se_row[label] = f"({model.bse[var]:.4f})"
        rows.append(coef_row)
        rows.append(se_row)

    obs_row = {"Variable": "Observations"}
    r2_row = {"Variable": "R-squared"}
    for label, model in models.items():
        obs_row[label] = int(model.nobs)
        r2_row[label] = round(model.rsquared, 4)
    rows.append(obs_row)
    rows.append(r2_row)

    return pd.DataFrame(rows).set_index("Variable")
