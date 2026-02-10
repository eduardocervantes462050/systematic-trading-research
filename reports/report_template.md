# Quant Project Report

**Author:** Eduardo Cervantes Alarcón  
**Date:** {{date}}

---

## 1. Executive Summary
- Strategy: Momentum + Macro-aware
- Instruments: {{tickers}}
- Time period: {{start_date}} – {{end_date}}
- Key metrics:
  - CAGR: {{cagr}}
  - Sharpe: {{sharpe}}
  - Max Drawdown: {{max_drawdown}}

---

## 2. Market Overview
- Market data for selected instruments
- Macroeconomic data: {{fred_series}}

---

## 3. Overall Figures

### Equity Curve
![Equity Curve](figures/equity_curve.png)

### Feature Correlation
![Feature Correlation](figures/feature_corr.png)

### Price Series
![Price Series](figures/price_series.png)

### Macro Series
![Macro Series](figures/macro_series.png)

### Backtest & Drawdown
![Backtest Equity](figures/backtest_equity.png)
![Drawdown](figures/drawdown.png)

---

## 4. Feature Engineering Summary
- Technical: Returns, RSI, MACD, Volatility
- Macro: CPI, Rates, Regimes

---

## 5. Ticker-Specific Plots

{{plots_per_ticker}}

> **Note:** This section automatically includes all tickers and their figures.  
> PNG files are detected based on naming convention: `TICKER.png`, `TICKER_returns_hist.png`, `TICKER_rolling_stats.png`, `TICKER_signals.png`.

---

## 6. Conclusions
- Summary of results per ticker
- Strategy robustness
- Next steps
