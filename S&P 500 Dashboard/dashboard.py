# S&P 500 Sector Performance Dashboard
# Built with Streamlit and yfinance
#
# Install dependencies:
# pip install streamlit yfinance pandas plotly
#
# Run the app:
# streamlit run dashboard.py

import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# ------------------------------------------------------------
# PAGE CONFIG
# ------------------------------------------------------------

st.set_page_config(
    page_title="S&P 500 Sector Analysis",
    page_icon="📈",
    layout="wide"
)

st.title("S&P 500 Sector Performance Dashboard")
st.markdown("Analyze risk-adjusted returns across S&P 500 sectors to inform portfolio allocation.")

# ------------------------------------------------------------
# SECTOR ETF TICKERS
# Each ticker represents one S&P 500 sector via SPDR ETFs
# ------------------------------------------------------------

SECTORS = {
    "Technology": "XLK",
    "Healthcare": "XLV",
    "Financials": "XLF",
    "Consumer Discretionary": "XLY",
    "Consumer Staples": "XLP",
    "Industrials": "XLI",
    "Energy": "XLE",
    "Utilities": "XLU",
    "Real Estate": "XLRE",
    "Materials": "XLB",
    "Communication Services": "XLC",
}

# ------------------------------------------------------------
# SIDEBAR CONTROLS
# ------------------------------------------------------------

st.sidebar.header("Settings")

period_options = {
    "1 Year": 365,
    "2 Years": 730,
    "3 Years": 1095,
    "5 Years": 1825,
}
selected_period = st.sidebar.selectbox("Time Period", list(period_options.keys()), index=2)
days_back = period_options[selected_period]

selected_sectors = st.sidebar.multiselect(
    "Sectors to Display",
    list(SECTORS.keys()),
    default=list(SECTORS.keys())
)

risk_free_rate = st.sidebar.slider(
    "Risk-Free Rate (%) for Sharpe Ratio",
    min_value=0.0,
    max_value=6.0,
    value=4.5,
    step=0.1
) / 100

# ------------------------------------------------------------
# DATA LOADING
# ------------------------------------------------------------

@st.cache_data(ttl=3600)
def load_sector_data(tickers, days):
    end = datetime.today()
    start = end - timedelta(days=days)
    raw = yf.download(list(tickers.values()), start=start, end=end, auto_adjust=True)["Close"]
    return raw

st.info("Loading market data from Yahoo Finance...")
ticker_map = {k: v for k, v in SECTORS.items() if k in selected_sectors}

if not ticker_map:
    st.warning("Please select at least one sector.")
    st.stop()

raw_prices = load_sector_data(ticker_map, days_back)

# Rename columns from ticker symbols back to sector names
reverse_map = {v: k for k, v in ticker_map.items()}
prices = raw_prices[[v for v in ticker_map.values() if v in raw_prices.columns]]
prices.columns = [reverse_map[col] for col in prices.columns]
prices = prices.dropna()

st.success("Data loaded.")

# ------------------------------------------------------------
# CALCULATE METRICS
# ------------------------------------------------------------

# Daily returns
daily_returns = prices.pct_change().dropna()

# Normalized price (base 100 at start of period)
normalized = (prices / prices.iloc[0]) * 100

# Total return over period
total_return = ((prices.iloc[-1] / prices.iloc[0]) - 1) * 100

# Annualized return
n_years = days_back / 365
annualized_return = ((prices.iloc[-1] / prices.iloc[0]) ** (1 / n_years) - 1) * 100

# Annualized volatility
annualized_vol = daily_returns.std() * (252 ** 0.5) * 100

# Sharpe ratio: (annualized return - risk free rate) / annualized volatility
sharpe = (annualized_return / 100 - risk_free_rate) / (annualized_vol / 100)

# Max drawdown
def max_drawdown(price_series):
    rolling_max = price_series.cummax()
    drawdown = (price_series - rolling_max) / rolling_max
    return drawdown.min() * 100

max_dd = prices.apply(max_drawdown)

# Summary table
summary = pd.DataFrame({
    "Total Return (%)": total_return.round(1),
    "Annualized Return (%)": annualized_return.round(1),
    "Volatility (%)": annualized_vol.round(1),
    "Sharpe Ratio": sharpe.round(2),
    "Max Drawdown (%)": max_dd.round(1),
}).sort_values("Sharpe Ratio", ascending=False)

# ------------------------------------------------------------
# SECTION 1: SUMMARY METRICS
# ------------------------------------------------------------

st.header("Sector Summary")

cols = st.columns(4)
top_sector = summary["Sharpe Ratio"].idxmax()
top_return = summary["Annualized Return (%)"].idxmax()
lowest_vol = summary["Volatility (%)"].idxmin()
best_drawdown = summary["Max Drawdown (%)"].idxmax()

cols[0].metric("Best Risk-Adjusted", top_sector, f"Sharpe {summary.loc[top_sector, 'Sharpe Ratio']:.2f}")
cols[1].metric("Highest Return", top_return, f"{summary.loc[top_return, 'Annualized Return (%)']:.1f}% ann.")
cols[2].metric("Lowest Volatility", lowest_vol, f"{summary.loc[lowest_vol, 'Volatility (%)']:.1f}% vol.")
cols[3].metric("Smallest Drawdown", best_drawdown, f"{summary.loc[best_drawdown, 'Max Drawdown (%)']:.1f}%")

st.dataframe(summary, use_container_width=True)

# ------------------------------------------------------------
# SECTION 2: NORMALIZED PRICE CHART
# ------------------------------------------------------------

st.header(f"Sector Performance ({selected_period})")
st.caption("All sectors indexed to 100 at the start of the selected period.")

fig_line = px.line(
    normalized,
    labels={"value": "Indexed Return (Base 100)", "variable": "Sector", "index": "Date"},
    title=f"S&P 500 Sector Returns — {selected_period}"
)
fig_line.update_layout(height=450, legend_title="Sector")
st.plotly_chart(fig_line, use_container_width=True)

# ------------------------------------------------------------
# SECTION 3: RISK VS RETURN SCATTER
# ------------------------------------------------------------

st.header("Risk vs. Return")
st.caption("Each dot is a sector. The further right and up, the better the absolute return. Sharpe ratio reflects risk-adjusted performance.")

scatter_df = summary.reset_index().rename(columns={"index": "Sector"})
fig_scatter = px.scatter(
    scatter_df,
    x="Volatility (%)",
    y="Annualized Return (%)",
    text="Sector",
    size="Sharpe Ratio",
    color="Sharpe Ratio",
    color_continuous_scale="RdYlGn",
    title="Risk vs. Return by Sector"
)
fig_scatter.update_traces(textposition="top center")
fig_scatter.update_layout(height=500)
st.plotly_chart(fig_scatter, use_container_width=True)

# ------------------------------------------------------------
# SECTION 4: SHARPE RATIO BAR CHART
# ------------------------------------------------------------

st.header("Sharpe Ratio by Sector")
st.caption(f"Sharpe ratio uses a {risk_free_rate*100:.1f}% risk-free rate. Values above 1.0 are generally considered good.")

sorted_sharpe = summary["Sharpe Ratio"].sort_values(ascending=True)
colors = ["tomato" if v < 0 else "steelblue" for v in sorted_sharpe.values]

fig_bar = go.Figure(go.Bar(
    x=sorted_sharpe.values,
    y=sorted_sharpe.index,
    orientation="h",
    marker_color=colors
))
fig_bar.add_vline(x=0, line_dash="dash", line_color="gray")
fig_bar.update_layout(
    title="Sharpe Ratio by Sector",
    xaxis_title="Sharpe Ratio",
    height=420
)
st.plotly_chart(fig_bar, use_container_width=True)

# ------------------------------------------------------------
# SECTION 5: PORTFOLIO SIMULATOR
# ------------------------------------------------------------

st.header("Portfolio Simulator")
st.caption("Adjust sector weights to see the blended portfolio return and volatility.")

st.markdown("Set weights below (they will be normalized to sum to 100%):")

weight_cols = st.columns(3)
weights = {}
for i, sector in enumerate(selected_sectors):
    col = weight_cols[i % 3]
    weights[sector] = col.slider(sector, 0, 100, 100 // len(selected_sectors), key=sector)

total_weight = sum(weights.values())

if total_weight == 0:
    st.warning("Please assign weight to at least one sector.")
else:
    normalized_weights = {k: v / total_weight for k, v in weights.items()}

    portfolio_daily = (daily_returns * pd.Series(normalized_weights)).sum(axis=1)
    portfolio_ann_return = ((1 + portfolio_daily.mean()) ** 252 - 1) * 100
    portfolio_vol = portfolio_daily.std() * (252 ** 0.5) * 100
    portfolio_sharpe = (portfolio_ann_return / 100 - risk_free_rate) / (portfolio_vol / 100)

    p1, p2, p3 = st.columns(3)
    p1.metric("Portfolio Ann. Return", f"{portfolio_ann_return:.1f}%")
    p2.metric("Portfolio Volatility", f"{portfolio_vol:.1f}%")
    p3.metric("Portfolio Sharpe Ratio", f"{portfolio_sharpe:.2f}")

    # Portfolio cumulative return chart
    portfolio_cumulative = (1 + portfolio_daily).cumprod() * 100
    fig_port = px.line(
        portfolio_cumulative,
        labels={"value": "Portfolio Value (Base 100)", "index": "Date"},
        title="Custom Portfolio Performance"
    )
    fig_port.update_layout(showlegend=False, height=350)
    st.plotly_chart(fig_port, use_container_width=True)

# ------------------------------------------------------------
# SECTION 6: TAKEAWAYS
# ------------------------------------------------------------

st.header("Key Takeaways")
st.markdown(f"""
- **{top_sector}** delivered the best risk-adjusted return (Sharpe: {summary.loc[top_sector, 'Sharpe Ratio']:.2f}) over the {selected_period.lower()} period
- **{top_return}** led in raw annualized return at {summary.loc[top_return, 'Annualized Return (%)']:.1f}%, but check its volatility before overweighting
- **{lowest_vol}** offers the smoothest ride at {summary.loc[lowest_vol, 'Volatility (%)']:.1f}% volatility — useful for defensive allocations
- Sharpe ratios above 1.0 indicate sectors compensating investors adequately for risk taken
- Use the portfolio simulator above to model blended allocations before committing to a weighting strategy
""")

st.caption("Data sourced from Yahoo Finance via yfinance. For educational purposes only. Not financial advice.")
