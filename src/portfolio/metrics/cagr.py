import pandas as pd
from data.database import Portfolio, PortfolioMetrics
from portfolio.equity_curve import calculate_portfolio_equity_curve


def calculate_and_store_cagr(session):
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

        # 2. Extract values
        start_value = float(df["total_value"].iloc[0])
        end_value = float(df["total_value"].iloc[-1])
        start_date = pd.to_datetime(df["Date"].iloc[0])
        end_date = pd.to_datetime(df["Date"].iloc[-1])
        days = (end_date - start_date).days
        years = days / 365.25

        if years <= 0 or start_value == 0:
            continue

        # 3. CAGR formula
        cagr = (end_value / start_value) ** (1 / years) - 1

        # 4. Check if exists
        existing = (
            session.query(PortfolioMetrics)
            .filter(
                PortfolioMetrics.portfolio_id == portfolio.portfolio_id,
                PortfolioMetrics.metric_type == "CAGR",
            )
            .first()
        )

        if existing:
            existing.value = cagr
            existing.start_date = start_date
            existing.end_date = end_date
        else:
            metric = PortfolioMetrics(
                portfolio_id=portfolio.portfolio_id,
                metric_type="CAGR",
                value=cagr,
                start_date=start_date,
                end_date=end_date,
            )
            session.add(metric)

        results.append({"portfolio": portfolio.name, "cagr": cagr})

    session.commit()
    return results
