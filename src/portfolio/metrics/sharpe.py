"""
src/portfolio/metrics/sharpe.py

Sharpe Ratio calculation and persistence.
"""

import logging

import pandas as pd
from sqlalchemy.orm import Session

from data.models import Portfolio
from data.repositories import save_portfolio_metrics
from portfolio.equity_curve import calculate_portfolio_equity_curve

logger = logging.getLogger(__name__)

RISK_FREE_RATE = 0.04  # annualized, override via parameter as needed


def calculate_sharpe(
    df: pd.DataFrame,
    risk_free_rate: float = RISK_FREE_RATE,
) -> tuple[float, pd.Timestamp, pd.Timestamp] | None:
    """
    Pure math — no DB.
    Computes annualized Sharpe ratio from an equity curve DataFrame.

    Expected df columns:
        - Date
        - total_value

    Returns (sharpe, start_date, end_date) or None if data is insufficient.
    """
    if df.empty or len(df) < 2:
        return None

    df = df.sort_values("Date").copy()
    df["daily_return"] = df["total_value"].pct_change()
    df = df.dropna(subset=["daily_return"])

    if len(df) < 2:
        return None

    start_date = pd.to_datetime(df["Date"].iloc[0])
    end_date = pd.to_datetime(df["Date"].iloc[-1])

    excess_returns = df["daily_return"] - (risk_free_rate / 252)
    std = excess_returns.std()

    if abs(std) < 1e-8:
        logger.warning("Near-zero std dev, Sharpe undefined")
        return None

    sharpe = float((excess_returns.mean() / std) * (252 ** 0.5))

    return sharpe, start_date, end_date


def calculate_and_store_sharpe(
    session: Session,
    risk_free_rate: float = RISK_FREE_RATE,
) -> list[dict]:
    """
    Compute and upsert Sharpe Ratio for every portfolio in the DB.
    Returns a list of dicts: [{"portfolio": name, "sharpe": value}, ...]
    """
    portfolios = session.query(Portfolio).all()
    results = []

    for portfolio in portfolios:
        # 1. Build equity curve
        df = calculate_portfolio_equity_curve(
            session, portfolio.portfolio_id, portfolio.start_date
        )

        # 2. Compute Sharpe
        result = calculate_sharpe(df, risk_free_rate)
        if result is None:
            logger.warning(
                "Insufficient equity curve data for portfolio %s, skipping",
                portfolio.name,
            )
            continue

        sharpe, start_date, end_date = result

        # 3. Upsert via repo
        save_portfolio_metrics(
            session,
            portfolio_id=portfolio.portfolio_id,
            metrics={"SHARPE": sharpe},
            start_date=start_date.date(),
            end_date=end_date.date(),
            extra_data={"risk_free_rate": risk_free_rate},
        )

        results.append({"portfolio": portfolio.name, "sharpe": sharpe})
        logger.info("Sharpe for %s: %.4f", portfolio.name, sharpe)

    return results