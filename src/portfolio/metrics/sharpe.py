import pandas as pd
from data.database import Portfolio, PortfolioMetrics
from portfolio.equity_curve import calculate_portfolio_equity_curve


def calculate_and_store_sharpe(session, risk_free_rate=0.04):
    portfolios = session.query(Portfolio).all()
    results = []

    for portfolio in portfolios:
        df = calculate_portfolio_equity_curve(
            session, portfolio.portfolio_id, portfolio.start_date
        )
        if df.empty or len(df) < 2:
            continue

        df = df.sort_values("Date")
        start_date = pd.to_datetime(df["Date"].iloc[0])
        end_date = pd.to_datetime(df["Date"].iloc[-1])

        # Daily returns
        df["daily_return"] = df["total_value"].pct_change()
        df = df.dropna(subset=["daily_return"])

        if len(df) < 2:
            continue

        # Annualized Sharpe formula
        excess_returns = df["daily_return"] - (risk_free_rate / 252)
        sharpe = float((excess_returns.mean() / excess_returns.std()) * (252**0.5))

        existing = (
            session.query(PortfolioMetrics)
            .filter(
                PortfolioMetrics.portfolio_id == portfolio.portfolio_id,
                PortfolioMetrics.metric_type == "SHARPE",
            )
            .first()
        )

        if existing:
            existing.value = sharpe
            existing.start_date = start_date
            existing.end_date = end_date
        else:
            metric = PortfolioMetrics(
                portfolio_id=portfolio.portfolio_id,
                metric_type="SHARPE",
                value=sharpe,
                start_date=start_date,
                end_date=end_date,
            )
            session.add(metric)

        results.append({"portfolio": portfolio.name, "sharpe": sharpe})

    session.commit()
    return results
