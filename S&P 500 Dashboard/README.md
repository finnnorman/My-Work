# S&P 500 Sector Performance Dashboard

**Tools:** Python, Streamlit, yfinance, Plotly  
**Skills:** Financial data analysis, interactive dashboard, risk metrics, portfolio modeling

---

## Business Question

Which S&P 500 sectors have delivered the best risk-adjusted returns, and how should an investor weight their portfolio based on historical performance?

---

## How to Run Locally

```bash
pip install streamlit yfinance pandas plotly
streamlit run dashboard.py
```

The app opens automatically in your browser at http://localhost:8501

---

## How to Deploy (Free)

1. Push this folder to a GitHub repo
2. Go to https://streamlit.io/cloud
3. Connect your GitHub repo and deploy — free hosting, shareable link

---

## Features

- Live market data pulled from Yahoo Finance (updates every hour)
- Sector performance indexed to a common baseline for fair comparison
- Risk vs. return scatter plot with Sharpe ratio sizing
- Adjustable risk-free rate for Sharpe calculation
- Portfolio simulator — drag sliders to model custom allocations
- Configurable time period (1, 2, 3, or 5 years)

---

## Metrics Explained

| Metric | What It Measures |
|---|---|
| Total Return | Raw price appreciation over the period |
| Annualized Return | Return normalized to a per-year rate |
| Volatility | Standard deviation of daily returns, annualized |
| Sharpe Ratio | Return per unit of risk (higher = better) |
| Max Drawdown | Worst peak-to-trough decline in the period |

---

## Data Source

SPDR Sector ETFs via Yahoo Finance (yfinance library). No API key required.

| Sector | Ticker |
|---|---|
| Technology | XLK |
| Healthcare | XLV |
| Financials | XLF |
| Consumer Discretionary | XLY |
| Consumer Staples | XLP |
| Industrials | XLI |
| Energy | XLE |
| Utilities | XLU |
| Real Estate | XLRE |
| Materials | XLB |
| Communication Services | XLC |

---

## Disclaimer

For educational and portfolio project purposes only. Not financial advice.
