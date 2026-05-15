import pandas as pd
from data.database import Portfolio, PortfolioMetrics
from portfolio.equity_curve import calculate_portfolio_equity_curve


def calculate_and_store_max_drawdown(session):
    portfolios = session.query(Portfolio).all()
    results = []

    for portfolio in portfolios:
        # 1. Build equity curve
        df = calculate_portfolio_equity_curve(
            session, portfolio.portfolio_id, portfolio.start_date
        )
        if df.empty or len(df) < 2:
            continue

        df = df.sort_values("Date")

        start_date = pd.to_datetime(df["Date"].iloc[0])
        end_date = pd.to_datetime(df["Date"].iloc[-1])

        # 2. Max drawdown formula
        rolling_max = df["total_value"].cummax()
        drawdown = (df["total_value"] - rolling_max) / rolling_max
        max_drawdown = float(drawdown.min())

        # 3. Check if exists
        existing = (
            session.query(PortfolioMetrics)
            .filter(
                PortfolioMetrics.portfolio_id == portfolio.portfolio_id,
                PortfolioMetrics.metric_type == "MAX_DRAWDOWN",
            )
            .first()
        )

        if existing:
            existing.value = max_drawdown
            existing.start_date = start_date
            existing.end_date = end_date
        else:
            metric = PortfolioMetrics(
                portfolio_id=portfolio.portfolio_id,
                metric_type="MAX_DRAWDOWN",
                value=max_drawdown,
                start_date=start_date,
                end_date=end_date,
            )
            session.add(metric)

        results.append({"portfolio": portfolio.name, "max_drawdown": max_drawdown})

    session.commit()
    return results
