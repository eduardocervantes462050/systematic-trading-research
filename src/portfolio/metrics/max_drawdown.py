"""
src/portfolio/metrics/max_drawdown.py

Max Drawdown calculation and persistence.
"""

import logging

import pandas as pd
from sqlalchemy.orm import Session

from data.models import Portfolio
from data.repositories import save_portfolio_metrics
from portfolio.equity_curve import calculate_portfolio_equity_curve

logger = logging.getLogger(__name__)


def calculate_max_drawdown(df: pd.DataFrame) -> tuple[float, pd.Timestamp, pd.Timestamp] | None:
    """
    Pure math — no DB.
    Computes max drawdown from an equity curve DataFrame.

    Expected df columns:
        - Date
        - total_value

    Returns (max_drawdown, start_date, end_date) or None if data is insufficient.
    """
    if df.empty or len(df) < 2:
        return None

    df = df.sort_values("Date")

    start_date = pd.to_datetime(df["Date"].iloc[0])
    end_date = pd.to_datetime(df["Date"].iloc[-1])

    rolling_max = df["total_value"].cummax()
    drawdown = (df["total_value"] - rolling_max) / rolling_max
    max_drawdown = float(drawdown.min())

    return max_drawdown, start_date, end_date


def calculate_and_store_max_drawdown(session: Session) -> list[dict]:
    """
    Compute and upsert Max Drawdown for every portfolio in the DB.
    Returns a list of dicts: [{"portfolio": name, "max_drawdown": value}, ...]
    """
    portfolios = session.query(Portfolio).all()
    results = []

    for portfolio in portfolios:
        # 1. Build equity curve
        df = calculate_portfolio_equity_curve(
            session, portfolio.portfolio_id, portfolio.start_date
        )

        # 2. Compute max drawdown
        result = calculate_max_drawdown(df)
        if result is None:
            logger.warning(
                "Insufficient equity curve data for portfolio %s, skipping",
                portfolio.name,
            )
            continue

        max_drawdown, start_date, end_date = result

        # 3. Upsert via repo
        save_portfolio_metrics(
            session,
            portfolio_id=portfolio.portfolio_id,
            metrics={"MAX_DRAWDOWN": max_drawdown},
            start_date=start_date.date(),
            end_date=end_date.date(),
        )

        results.append({"portfolio": portfolio.name, "max_drawdown": max_drawdown})
        logger.info("Max Drawdown for %s: %.4f", portfolio.name, max_drawdown)

    return results