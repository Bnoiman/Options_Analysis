"""Data loading utilities for the ETF volatility dashboard."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import pandas as pd
import streamlit as st
import yfinance as yf


INTERVAL_MAP = {
    "Daily": "1d",
    "Weekly": "1wk",
    "Monthly": "1mo",
}

REQUIRED_COLUMNS = ["Open", "High", "Low", "Close", "Volume"]


@dataclass(frozen=True)
class DataRequest:
    """Container for data fetch parameters."""

    ticker: str
    start_date: date
    end_date: date
    interval: str


def _empty_ohlcv_frame() -> pd.DataFrame:
    """Return an empty dataframe with expected OHLCV columns."""

    return pd.DataFrame(columns=REQUIRED_COLUMNS)


def _normalize_ohlcv_columns(raw: pd.DataFrame, ticker: str) -> pd.DataFrame:
    """Normalize yfinance output into a single-level OHLCV schema.

    yfinance may return:
    - single-level columns (Open/High/Low/Close/Volume)
    - two-level MultiIndex columns (Price, Ticker)
    - occasionally columns with lowercase names
    """

    if raw.empty:
        return _empty_ohlcv_frame()

    data = raw.copy()

    # Handle multi-ticker/multi-index shaped output.
    if isinstance(data.columns, pd.MultiIndex):
        level_values = pd.Index(data.columns.get_level_values(-1)).astype(str)
        target = ticker.upper()
        ticker_matches = level_values.str.upper() == target

        # Try exact ticker (case-insensitive) in level 1 first.
        if ticker_matches.any():
            matched_ticker = level_values[ticker_matches][0]
            try:
                data = data.xs(matched_ticker, axis=1, level=-1)
            except (KeyError, ValueError):
                # Fall back to dropping ticker level if xs fails for any edge-case shape.
                data = data.droplevel(-1, axis=1)
        else:
            # Common single-ticker shape is (field, ticker) across columns.
            data = data.droplevel(-1, axis=1)

    # Make column matching resilient to casing and spacing.
    col_map = {str(c).strip().lower(): c for c in data.columns}
    selected = {}
    for target in REQUIRED_COLUMNS:
        source_col = col_map.get(target.lower())
        if source_col is not None:
            selected[target] = data[source_col]

    if len(selected) < len(REQUIRED_COLUMNS):
        return _empty_ohlcv_frame()

    normalized = pd.DataFrame(selected)
    normalized.index = pd.to_datetime(normalized.index).tz_localize(None)
    normalized = normalized.sort_index()
    normalized = normalized.dropna(subset=["Open", "High", "Low", "Close"])
    normalized["Volume"] = pd.to_numeric(normalized["Volume"], errors="coerce").fillna(0)
    return normalized


@st.cache_data(show_spinner=False, ttl=60 * 30)
def load_ohlcv_data(request: DataRequest) -> pd.DataFrame:
    """Fetch OHLCV data from Yahoo Finance and normalize schema.

    Parameters
    ----------
    request : DataRequest
        User-selected request parameters.

    Returns
    -------
    pd.DataFrame
        DataFrame indexed by date with Open/High/Low/Close/Volume columns.
    """

    interval = INTERVAL_MAP.get(request.interval, "1d")
    raw = yf.download(
        tickers=request.ticker,
        start=request.start_date,
        end=request.end_date,
        interval=interval,
        auto_adjust=False,
        progress=False,
        threads=False,
    )

    return _normalize_ohlcv_columns(raw=raw, ticker=request.ticker)
