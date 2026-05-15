# Quantitative Portfolio Report
**Date:** {{date}}  
**Portfolio Evaluated:** {{portfolio_name}}  
**Tickers Included:** {{tickers}}

---

## 1️⃣ Key Metrics

| Metric          | Value                          |
| --------------- | ------------------------------ |
| CAGR            | {{cagr}}                       |
| Sharpe Ratio    | {{sharpe}}                     |
| Max Drawdown    | {{max_drawdown}}               |
| Volatility      | {{volatility}}                 |
| Analysis Period | {{start_date}} to {{end_date}} |

*These metrics summarize the overall performance and risk profile of the recommended portfolio.*

---

## 2️⃣ Portfolio Composition

{{allocation_table}}

*Weights can be adjusted based on client preferences or risk tolerance.*

---

## 3️⃣ Portfolio Analysis

### Equity Curve
![Portfolio Equity Curve](figures/overall_equity_curve.png)

### Drawdown
![Portfolio Drawdown](figures/overall_drawdown.png)

{{portfolio_plots}}

---

## 4️⃣ Individual Ticker Insights

{{plots_per_ticker}}

*Each ticker section shows the relevant charts, features, or performance metrics.*

---

## 5️⃣ Recommendation

> Based on the metrics above, we recommend this portfolio for a **moderately aggressive investor**.  
> - Expected annual return (CAGR): {{cagr}}  
> - Risk-adjusted return (Sharpe): {{sharpe}}  
> - Maximum historical loss (Max Drawdown): {{max_drawdown}}  
> - Annualized Volatility: {{volatility}}

*Alternative scenarios (e.g., max Sharpe portfolio or min volatility portfolio) can be provided if desired.*

---

## 6️⃣ Data Sources

- Portfolio historical data: internal calculations / CSV files  
- Economic indicators: {{fred_series}} or other relevant sources  
- Plots generated from latest data analysis