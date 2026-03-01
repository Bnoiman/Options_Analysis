"""Streamlit ETF volatility analysis dashboard."""

from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
import streamlit as st

from charts import cumulative_return_chart, price_volume_chart, range_analysis_chart, volume_analysis_chart
from data_loader import DataRequest, load_ohlcv_data
from metrics import add_derived_metrics, annualized_volatility, calculate_summary_stats, maximum_drawdown, win_rate

st.set_page_config(page_title="ETF Volatility Dashboard", page_icon="📈", layout="wide")

st.markdown(
    """
    <style>
    .stApp { background-color: #0e1117; color: #f5f7fa; }
    div[data-testid="metric-container"] { background: #151a24; border: 1px solid #2f3542; padding: 12px; border-radius: 10px; }
    .dashboard-header {font-size: 2.0rem; font-weight: 700; margin-bottom: 0.2rem;}
    .dashboard-subheader {color: #98a6b3; margin-bottom: 1rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown("<div class='dashboard-header'>ETF Volatility Analysis Dashboard</div>", unsafe_allow_html=True)
st.markdown(
    "<div class='dashboard-subheader'>Professional OHLCV analytics with volatility diagnostics and export tools.</div>",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Controls")
    ticker = st.text_input("Ticker", value="TQQQ").upper().strip()

    default_end = date.today()
    default_start = default_end - timedelta(days=365 * 2)
    date_range = st.date_input("Date Range", value=(default_start, default_end), max_value=default_end)

    interval = st.selectbox("Interval", options=["Daily", "Weekly", "Monthly"], index=0)
    show_derived = st.toggle("Show Derived Metrics Table", value=True)
    show_moving_averages = st.toggle("Show Moving Averages (20/50)", value=True)
    log_scale = st.toggle("Log Scale Price", value=False)

    vol_threshold = st.slider(
        "High Volatility Threshold (Range_HL)",
        min_value=0.0,
        max_value=20.0,
        value=2.0,
        step=0.1,
    )

    st.divider()
    st.subheader("Future Expansion Hooks")
    st.caption("Configured placeholders for roadmap modules")
    st.checkbox("Multiple ticker overlay (placeholder)", value=False, disabled=True)
    st.checkbox("Strategy backtesting module (placeholder)", value=False, disabled=True)
    st.checkbox("Alert trigger framework (placeholder)", value=False, disabled=True)

if not ticker:
    st.warning("Please provide a ticker symbol.")
    st.stop()

if not isinstance(date_range, tuple) or len(date_range) != 2:
    st.warning("Please select a valid start and end date.")
    st.stop()

start_date, end_date = date_range
request = DataRequest(ticker=ticker, start_date=start_date, end_date=end_date + timedelta(days=1), interval=interval)

with st.spinner("Loading market data..."):
    ohlcv = load_ohlcv_data(request)

if ohlcv.empty:
    st.error("No data returned for this ticker/date range. Please adjust your filters.")
    st.stop()

analysis_df = add_derived_metrics(ohlcv)

# Section A
st.subheader("Section A: Price Chart")
st.plotly_chart(
    price_volume_chart(analysis_df, volatility_threshold=vol_threshold, show_ma=show_moving_averages, log_scale=log_scale),
    use_container_width=True,
)

# Section B
st.subheader("Section B: Range Analysis")
left, right = st.columns([2, 1])
with left:
    st.plotly_chart(range_analysis_chart(analysis_df), use_container_width=True)
with right:
    top10 = analysis_df.nlargest(10, "Range_HL")[["Open", "High", "Low", "Close", "Volume", "Range_HL", "Range_CO"]]
    st.markdown("**Top 10 Highest Volatility Days**")
    st.dataframe(top10.style.format({"Range_HL": "{:.2f}", "Range_CO": "{:.2f}", "Volume": "{:,.0f}"}), use_container_width=True)

# Section C
st.subheader("Section C: Volume Analysis")
col_v1, col_v2 = st.columns([2, 1])
with col_v1:
    st.plotly_chart(volume_analysis_chart(analysis_df), use_container_width=True)
with col_v2:
    corr = analysis_df[["Volume", "Range_HL"]].corr().iloc[0, 1]
    st.metric("Volume ↔ Range_HL Correlation", f"{corr:.3f}")
    st.line_chart(analysis_df[["Volume", "Volume_MA_10"]], height=280)

# Section D
st.subheader("Section D: Statistics Panel")
stats_cols = ["Range_HL", "Range_CO", "Volume", "Percent_Open"]
metrics_grid = st.columns(4)
for idx, col_name in enumerate(stats_cols):
    stats = calculate_summary_stats(analysis_df, col_name)
    with metrics_grid[idx]:
        st.metric(f"{col_name} Mean", f"{stats.mean_value:.4f}")
        st.caption(
            f"Max: {stats.max_value:.4f} | Min: {stats.min_value:.4f} | Std: {stats.std_dev:.4f}"
        )

extra = st.columns(3)
with extra[0]:
    st.metric("Annualized Volatility", f"{annualized_volatility(analysis_df):.2%}")
with extra[1]:
    st.metric("Maximum Drawdown", f"{maximum_drawdown(analysis_df):.2%}")
with extra[2]:
    st.metric("Win Rate (Close > Open)", f"{win_rate(analysis_df):.2%}")

# Advanced features
st.subheader("Advanced Features")
st.plotly_chart(cumulative_return_chart(analysis_df), use_container_width=True)

if show_derived:
    st.markdown("**Derived Metrics Table**")
    derived_columns = [
        "Range_CO",
        "Percent_Open",
        "Range_LO",
        "Range_HO",
        "Range_HL",
        "Volume_Change",
        "Gap",
        "Rolling_Volatility_10D",
        "Cum_Return",
    ]
    view_df = analysis_df[derived_columns].copy()
    st.dataframe(view_df, use_container_width=True)

export_df = analysis_df.reset_index().rename(columns={"index": "Date"})
csv_data = export_df.to_csv(index=False).encode("utf-8")
st.download_button(
    label="Export Filtered Dataset to CSV",
    data=csv_data,
    file_name=f"{ticker}_{interval.lower()}_volatility_dashboard.csv",
    mime="text/csv",
)
