"""Metric calculations for ETF volatility dashboard."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

TRADING_DAYS_PER_YEAR = 252


@dataclass(frozen=True)
class SummaryStats:
    max_value: float
    min_value: float
    mean_value: float
    std_dev: float


def add_derived_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Add derived volatility and movement metrics."""

    data = df.copy()
    previous_close = data["Close"].shift(1)
    previous_volume = data["Volume"].shift(1)

    data["Range_CO"] = data["Close"] - data["Open"]
    data["Percent_Open"] = np.where(
        data["Open"] != 0,
        (data["Close"] - data["Open"]) / data["Open"],
        np.nan,
    )
    data["Range_LO"] = data["Low"] - data["Open"]
    data["Range_HO"] = data["High"] - data["Open"]
    data["Range_HL"] = data["High"] - data["Low"]
    data["Volume_Change"] = data["Volume"] - previous_volume
    data["Gap"] = data["Open"] - previous_close

    data["Returns"] = data["Close"].pct_change().fillna(0)
    data["Rolling_Volatility_10D"] = (
        data["Returns"].rolling(window=10).std() * np.sqrt(TRADING_DAYS_PER_YEAR)
    )
    data["Cum_Return"] = (1 + data["Returns"]).cumprod() - 1
    data["Volume_MA_10"] = data["Volume"].rolling(10).mean()

    return data


def calculate_summary_stats(df: pd.DataFrame, column: str) -> SummaryStats:
    """Compute summary statistics for a column."""

    series = pd.to_numeric(df[column], errors="coerce").dropna()
    if series.empty:
        return SummaryStats(np.nan, np.nan, np.nan, np.nan)
    return SummaryStats(
        max_value=float(series.max()),
        min_value=float(series.min()),
        mean_value=float(series.mean()),
        std_dev=float(series.std(ddof=1)),
    )


def annualized_volatility(df: pd.DataFrame) -> float:
    """Annualized volatility based on close-to-close returns."""

    returns = df["Close"].pct_change().dropna()
    if returns.empty:
        return float("nan")
    return float(returns.std(ddof=1) * np.sqrt(TRADING_DAYS_PER_YEAR))


def maximum_drawdown(df: pd.DataFrame) -> float:
    """Compute max drawdown using close prices."""

    if df.empty:
        return float("nan")
    wealth = (1 + df["Close"].pct_change().fillna(0)).cumprod()
    running_max = wealth.cummax()
    drawdown = wealth / running_max - 1
    return float(drawdown.min())


def win_rate(df: pd.DataFrame) -> float:
    """Percentage of periods where Close > Open."""

    if df.empty:
        return float("nan")
    wins = (df["Close"] > df["Open"]).mean()
    return float(wins)
