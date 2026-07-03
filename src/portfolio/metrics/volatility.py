"""
src/portfolio/metrics/volatility.py

Annualized Volatility calculation and persistence.
"""

import logging

import pandas as pd
from sqlalchemy.orm import Session

from data.models import Portfolio
from data.repositories import save_portfolio_metrics
from portfolio.equity_curve import calculate_portfolio_equity_curve

logger = logging.getLogger(__name__)


def calculate_volatility(df: pd.DataFrame) -> tuple[float, pd.Timestamp, pd.Timestamp] | None:
    """
    Pure math — no DB access.

    Computes annualized volatility from an equity curve.

    Expected df columns:
        - Date
        - total_value

    Returns:
        (volatility, start_date, end_date) or None
    """
    if df.empty or len(df) < 2:
        return None

    df = df.sort_values("Date").copy()

    df["daily_return"] = df["total_value"].pct_change()
    df = df.dropna(subset=["daily_return"])

    if df.empty:
        return None

    start_date = pd.to_datetime(df["Date"].iloc[0])
    end_date = pd.to_datetime(df["Date"].iloc[-1])

    volatility = float(df["daily_return"].std() * (252 ** 0.5))

    return volatility, start_date, end_date


def calculate_and_store_volatility(session: Session) -> list[dict]:
    """
    Compute and store annualized volatility for all portfolios.

    Returns:
        [{"portfolio": name, "volatility": value}, ...]
    """

    portfolios = session.query(Portfolio).all()
    results = []

    for portfolio in portfolios:

        # 1. Build equity curve
        df = calculate_portfolio_equity_curve(
            session,
            portfolio.portfolio_id,
            portfolio.start_date,
        )

        # 2. Compute volatility
        result = calculate_volatility(df)

        if result is None:
            logger.warning(
                "Insufficient data for volatility - portfolio %s",
                portfolio.name,
            )
            continue

        volatility, start_date, end_date = result

        # 3. Persist (MATCHING YOUR CAGR STYLE)
        save_portfolio_metrics(
            session,
            portfolio_id=portfolio.portfolio_id,
            metrics={"volatility": volatility},
            start_date=start_date.date(),
            end_date=end_date.date(),
        )

        results.append(
            {
                "portfolio": portfolio.name,
                "volatility": volatility,
            }
        )

        logger.info(
            "Volatility for %s: %.4f",
            portfolio.name,
            volatility,
        )

    return results