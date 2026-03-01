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

main

@dataclass(frozen=True)
class DataRequest:
    """Container for data fetch parameters."""

    ticker: str
    start_date: date
    end_date: date
    interval: str


main
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

main
