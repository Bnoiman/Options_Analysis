import pandas as pd

from metrics import (
    add_derived_metrics,
    annualized_volatility,
    calculate_summary_stats,
    maximum_drawdown,
    win_rate,
)


def _sample_df() -> pd.DataFrame:
    idx = pd.date_range("2024-01-01", periods=5)
    return pd.DataFrame(
        {
            "Open": [10, 11, 12, 11, 13],
            "High": [11, 12, 13, 12, 14],
            "Low": [9, 10, 11, 10, 12],
            "Close": [10.5, 11.5, 11.8, 11.2, 13.5],
            "Volume": [1000, 1200, 1100, 1500, 1800],
        },
        index=idx,
    )


def test_add_derived_metrics_creates_expected_columns():
    df = add_derived_metrics(_sample_df())

    required_cols = {
        "Range_CO",
        "Percent_Open",
        "Range_LO",
        "Range_HO",
        "Range_HL",
        "Volume_Change",
        "Gap",
        "Rolling_Volatility_10D",
        "Cum_Return",
        "Volume_MA_10",
    }
    assert required_cols.issubset(df.columns)


def test_summary_and_risk_metrics_return_numbers():
    df = add_derived_metrics(_sample_df())

    stats = calculate_summary_stats(df, "Range_HL")
    assert stats.max_value >= stats.min_value
    assert stats.std_dev >= 0

    assert isinstance(annualized_volatility(df), float)
    assert isinstance(maximum_drawdown(df), float)
    assert 0 <= win_rate(df) <= 1
