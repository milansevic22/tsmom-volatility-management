import pandas as pd

from tsmom.utils import align_monthly, to_month_end, to_month_start


def test_to_month_end_normalises_arbitrary_day_of_month():
    dates = pd.to_datetime(["2020-01-15", "2020-02-03"])
    series = pd.Series([1, 2], index=dates)

    result = to_month_end(series)

    assert list(result.index) == [pd.Timestamp("2020-01-31"), pd.Timestamp("2020-02-29")]


def test_to_month_start_normalises_arbitrary_day_of_month():
    dates = pd.to_datetime(["2020-01-15", "2020-02-28"])
    series = pd.Series([1, 2], index=dates)

    result = to_month_start(series)

    assert list(result.index) == [pd.Timestamp("2020-01-01"), pd.Timestamp("2020-02-01")]


def test_align_monthly_restricts_to_common_dates():
    dates_a = pd.to_datetime(["2020-01-31", "2020-02-29", "2020-03-31"])
    dates_b = pd.to_datetime(["2020-02-15", "2020-03-20"])
    series_a = pd.Series([1, 2, 3], index=dates_a)
    series_b = pd.Series([10, 20], index=dates_b)

    aligned_a, aligned_b = align_monthly(series_a, series_b)

    assert list(aligned_a.index) == [pd.Timestamp("2020-02-29"), pd.Timestamp("2020-03-31")]
    assert aligned_a.tolist() == [2, 3]
    assert aligned_b.tolist() == [10, 20]
