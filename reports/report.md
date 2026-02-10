# Quant Project Report

**Author:** Eduardo Cervantes Alarcón  
**Date:** 2026-02-09

---

## 1. Executive Summary
- Strategy: Momentum + Macro-aware
- Instruments: AAPL, BAC
- Time period: 2000-01-01 – 2025-12-31
- Key metrics:
  - CAGR: 12.5%
  - Sharpe: 1.45
  - Max Drawdown: -15%

---

## 2. Market Overview
- Market data for selected instruments
- Macroeconomic data: CPIAUCSL

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

## AAPL

![AAPL_filtered.png](figures/AAPL_filtered.png)

![AAPL_filtered_returns_hist.png](figures/AAPL_filtered_returns_hist.png)

## BAC

![BAC_filtered.png](figures/BAC_filtered.png)

![BAC_filtered_returns_hist.png](figures/BAC_filtered_returns_hist.png)



> **Note:** This section automatically includes all tickers and their figures.  
> PNG files are detected based on naming convention: `TICKER.png`, `TICKER_returns_hist.png`, `TICKER_rolling_stats.png`, `TICKER_signals.png`.

---

## 6. Conclusions
- Summary of results per ticker
- Strategy robustness
- Next steps
