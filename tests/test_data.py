import numpy as np
import pandas as pd
import pytest

from tsmom.data import (
    compute_returns,
    load_bloomberg_index_monthly_return,
    load_fama_french_factors,
    load_momentum_factor,
    load_settlement_series,
    load_settlement_universe,
)

BLOOMBERG_SETTLEMENT_CSV = """Security,TEST1 Comdty,
Start Date,01/01/2020 00:00,
End Date,01/05/2020 00:00,
Period,M,
Currency,USD,

Date,PX_SETTLE
31/01/2020,100.0
29/02/2020,105.0
31/03/2020,110.0
"""

BLOOMBERG_INDEX_CSV = """Security,TEST_INDEX,
Start Date,01/01/2020 00:00,
End Date,01/03/2020 00:00,
Period,M,

Date,PX_LAST
31/01/2020,1000.0
29/02/2020,1050.0
31/03/2020,1100.0
"""


@pytest.fixture
def settlement_csv(tmp_path):
    path = tmp_path / "TEST1_Comdty_monthly_settlement.csv"
    path.write_text(BLOOMBERG_SETTLEMENT_CSV, encoding="utf-8")
    return path


@pytest.fixture
def index_csv(tmp_path):
    path = tmp_path / "TEST_INDEX_monthly.csv"
    path.write_text(BLOOMBERG_INDEX_CSV, encoding="utf-8")
    return path


def test_load_settlement_series_finds_header_row_dynamically(settlement_csv):
    series = load_settlement_series(settlement_csv, ticker="TEST1_Comdty")

    assert list(series.columns) == ["Date", "TEST1_Comdty"]
    assert series["TEST1_Comdty"].tolist() == [100.0, 105.0, 110.0]


def test_load_settlement_universe_merges_multiple_tickers(tmp_path):
    (tmp_path / "AAA_monthly_settlement.csv").write_text(BLOOMBERG_SETTLEMENT_CSV, encoding="utf-8")
    (tmp_path / "BBB_monthly_settlement.csv").write_text(BLOOMBERG_SETTLEMENT_CSV, encoding="utf-8")

    universe = load_settlement_universe(tmp_path, "_monthly_settlement.csv")

    assert list(universe.columns) == ["AAA", "BBB"]
    assert len(universe) == 3


def test_load_settlement_universe_raises_when_empty(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_settlement_universe(tmp_path, "_monthly_settlement.csv")


def test_compute_returns_filters_roll_outliers():
    prices = pd.DataFrame({"A": [100.0, 200.0, 202.0]})

    returns = compute_returns(prices, clip=0.8)

    assert pd.isna(returns["A"].iloc[1])  # 100% jump filtered out
    assert returns["A"].iloc[2] == pytest.approx(0.01)


def test_load_bloomberg_index_monthly_return(index_csv):
    monthly_return = load_bloomberg_index_monthly_return(index_csv)

    assert monthly_return.iloc[0] == pytest.approx(0.05)
    assert monthly_return.iloc[1] == pytest.approx(1100.0 / 1050.0 - 1)


def test_load_fama_french_factors_drops_trailing_annual_block(tmp_path):
    content = (
        "\n\n\n\n"
        ",Mkt-RF,SMB,HML,RF\n"
        "202001,   1.00,   0.50,  -0.20,   0.10\n"
        "202002,  -2.00,   0.10,   0.30,   0.10\n"
        "\n"
        "  Annual Factors: January-December  \n"
        "2020,  10.00,   2.00,  -1.00,   1.20\n"
    )
    path = tmp_path / "F-F_Research_Data_Factors.csv"
    path.write_text(content, encoding="utf-8")

    factors = load_fama_french_factors(path)

    assert len(factors) == 2
    assert factors["Mkt-RF"].iloc[0] == pytest.approx(0.01)


def test_load_momentum_factor_renames_to_umd(tmp_path):
    content = (
        "\n" * 13
        + ",Mom\n"
        + "202001,   0.57\n"
        + "202002,  -1.20\n"
    )
    path = tmp_path / "F-F_Momentum_Factor.csv"
    path.write_text(content, encoding="utf-8")

    umd = load_momentum_factor(path)

    assert list(umd.columns) == ["UMD"]
    assert umd["UMD"].iloc[0] == pytest.approx(0.0057)
