"""Chart constructors for ETF volatility dashboard."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


DARK_TEMPLATE = "plotly_dark"


def price_volume_chart(
    df: pd.DataFrame,
    volatility_threshold: float,
    show_ma: bool = True,
    log_scale: bool = False,
) -> go.Figure:
    """Candlestick + volume with high-volatility markers."""

    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        row_heights=[0.75, 0.25],
        vertical_spacing=0.03,
    )

    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            name="Price",
        ),
        row=1,
        col=1,
    )

    if show_ma:
        ma20 = df["Close"].rolling(20).mean()
        ma50 = df["Close"].rolling(50).mean()
        fig.add_trace(go.Scatter(x=df.index, y=ma20, mode="lines", name="MA 20"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=ma50, mode="lines", name="MA 50"), row=1, col=1)

    high_vol = df[df["Range_HL"] >= volatility_threshold]
    if not high_vol.empty:
        fig.add_trace(
            go.Scatter(
                x=high_vol.index,
                y=high_vol["High"],
                mode="markers",
                marker=dict(color="#ff4d6d", size=8, symbol="diamond"),
                name="High Volatility",
            ),
            row=1,
            col=1,
        )

    volume_colors = np.where(df["Close"] >= df["Open"], "#2ca02c", "#d62728")
    fig.add_trace(
        go.Bar(x=df.index, y=df["Volume"], name="Volume", marker_color=volume_colors, opacity=0.8),
        row=2,
        col=1,
    )

    fig.update_layout(template=DARK_TEMPLATE, height=700, margin=dict(l=20, r=20, t=40, b=20))
    fig.update_yaxes(title_text="Price", type="log" if log_scale else "linear", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)
    fig.update_xaxes(showspikes=True)
    return fig


def range_analysis_chart(df: pd.DataFrame) -> go.Figure:
    """Histogram and boxplot for range diagnostics."""

    fig = make_subplots(
        rows=2,
        cols=2,
        subplot_titles=("Range_HL Distribution", "Range_CO Distribution", "Range_HL Box", "Range_CO Box"),
    )

    fig.add_trace(go.Histogram(x=df["Range_HL"], name="Range_HL", nbinsx=40), row=1, col=1)
    fig.add_trace(go.Histogram(x=df["Range_CO"], name="Range_CO", nbinsx=40), row=1, col=2)
    fig.add_trace(go.Box(y=df["Range_HL"], name="Range_HL"), row=2, col=1)
    fig.add_trace(go.Box(y=df["Range_CO"], name="Range_CO"), row=2, col=2)

    fig.update_layout(template=DARK_TEMPLATE, height=700, margin=dict(l=20, r=20, t=40, b=20), showlegend=False)
    return fig


def volume_analysis_chart(df: pd.DataFrame) -> go.Figure:
    """Scatter chart for volume vs range with trend line."""

    corr = df[["Volume", "Range_HL"]].corr().iloc[0, 1]
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["Volume"],
            y=df["Range_HL"],
            mode="markers",
            marker=dict(size=7, color=df["Range_CO"], colorscale="RdBu", showscale=True),
            text=[idx.strftime("%Y-%m-%d") for idx in df.index],
            name="Observations",
        )
    )

    if len(df) > 1:
        slope, intercept = np.polyfit(df["Volume"], df["Range_HL"], 1)
        x_line = np.linspace(df["Volume"].min(), df["Volume"].max(), 100)
        y_line = slope * x_line + intercept
        fig.add_trace(go.Scatter(x=x_line, y=y_line, mode="lines", name="Trend", line=dict(color="#ffa600")))

    fig.update_layout(
        template=DARK_TEMPLATE,
        title=f"Volume vs Range_HL (Correlation: {corr:.3f})",
        xaxis_title="Volume",
        yaxis_title="Range_HL",
        height=500,
        margin=dict(l=20, r=20, t=50, b=20),
    )
    return fig


def cumulative_return_chart(df: pd.DataFrame) -> go.Figure:
    """Cumulative return + rolling volatility overlay."""

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Scatter(x=df.index, y=df["Cum_Return"] * 100, mode="lines", name="Cumulative Return %"),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["Rolling_Volatility_10D"] * 100,
            mode="lines",
            name="Rolling Vol 10D %",
            line=dict(dash="dot"),
        ),
        secondary_y=True,
    )
    fig.update_layout(template=DARK_TEMPLATE, height=420, margin=dict(l=20, r=20, t=40, b=20))
    fig.update_yaxes(title_text="Cum Return (%)", secondary_y=False)
    fig.update_yaxes(title_text="Rolling Vol (%)", secondary_y=True)
    return fig
