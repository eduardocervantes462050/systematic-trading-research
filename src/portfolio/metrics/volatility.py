import pandas as pd
from data.database import Portfolio, PortfolioMetrics
from portfolio.equity_curve import calculate_portfolio_equity_curve


def calculate_and_store_volatility(session):
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

        # 2. Calculate daily returns
        df["daily_return"] = df["total_value"].pct_change()
        df = df.dropna(subset=["daily_return"])

        if len(df) < 2:
            continue

        start_date = pd.to_datetime(df["Date"].iloc[0])
        end_date = pd.to_datetime(df["Date"].iloc[-1])

        # 3. Annualized volatility formula (std of daily returns * sqrt(252))
        volatility = float(df["daily_return"].std() * (252**0.5))

        # 4. Check if exists
        existing = (
            session.query(PortfolioMetrics)
            .filter(
                PortfolioMetrics.portfolio_id == portfolio.portfolio_id,
                PortfolioMetrics.metric_type == "VOLATILITY",
            )
            .first()
        )

        if existing:
            existing.value = volatility
            existing.start_date = start_date
            existing.end_date = end_date
        else:
            metric = PortfolioMetrics(
                portfolio_id=portfolio.portfolio_id,
                metric_type="VOLATILITY",
                value=volatility,
                start_date=start_date,
                end_date=end_date,
            )
            session.add(metric)

        results.append({"portfolio": portfolio.name, "volatility": volatility})

    session.commit()
    return results
