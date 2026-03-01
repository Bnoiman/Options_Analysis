import numpy as np
import pandas as pd

from data_loader import _normalize_ohlcv_columns


OHLCV = ["Open", "High", "Low", "Close", "Volume"]


def test_normalize_handles_flat_columns():
    idx = pd.date_range("2024-01-01", periods=3)
    raw = pd.DataFrame(
        {
            "Open": [10.0, 11.0, 12.0],
            "High": [11.0, 12.0, 13.0],
            "Low": [9.0, 10.0, 11.0],
            "Close": [10.5, 11.5, 12.5],
            "Volume": [1000, 1200, 1400],
        },
        index=idx,
    )

    result = _normalize_ohlcv_columns(raw, ticker="TQQQ")

    assert result.columns.tolist() == OHLCV
    assert len(result) == 3


def test_normalize_handles_multiindex_columns_case_insensitive_ticker():
    idx = pd.date_range("2024-01-01", periods=2)
    cols = pd.MultiIndex.from_product([OHLCV, ["tqqq"]])
    raw = pd.DataFrame(
        np.array([
            [10.0, 11.0, 9.0, 10.5, 1000],
            [11.0, 12.0, 10.5, 11.6, 1100],
        ]),
        index=idx,
        columns=cols,
    )

    result = _normalize_ohlcv_columns(raw, ticker="TQQQ")

    assert result.columns.tolist() == OHLCV
    assert len(result) == 2
    assert float(result.iloc[0]["Close"]) == 10.5


def test_normalize_returns_empty_when_required_columns_missing():
    idx = pd.date_range("2024-01-01", periods=2)
    raw = pd.DataFrame({"Open": [1, 2], "Close": [1.5, 2.5]}, index=idx)

    result = _normalize_ohlcv_columns(raw, ticker="TQQQ")

    assert result.empty
    assert result.columns.tolist() == OHLCV
