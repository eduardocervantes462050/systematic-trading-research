"""
src/portfolio/metrics/cagr.py

CAGR (Compound Annual Growth Rate) calculation and persistence.
"""

import logging

import pandas as pd
from sqlalchemy.orm import Session

from data.models import Portfolio
from data.repositories import save_portfolio_metrics
from portfolio.equity_curve import calculate_portfolio_equity_curve

logger = logging.getLogger(__name__)


def calculate_cagr(df: pd.DataFrame) -> tuple[float, pd.Timestamp, pd.Timestamp] | None:
    """
    Pure math — no DB.
    Computes CAGR from an equity curve DataFrame.

    Expected df columns:
        - Date
        - total_value

    Returns (cagr, start_date, end_date) or None if data is insufficient.
    """
    if df.empty or len(df) < 2:
        return None

    df = df.sort_values("Date")

    start_value = float(df["total_value"].iloc[0])
    end_value = float(df["total_value"].iloc[-1])
    start_date = pd.to_datetime(df["Date"].iloc[0])
    end_date = pd.to_datetime(df["Date"].iloc[-1])

    days = (end_date - start_date).days
    years = days / 365.25

    if years <= 0 or start_value == 0:
        return None

    cagr = (end_value / start_value) ** (1 / years) - 1
    return cagr, start_date, end_date


def calculate_and_store_cagr(session: Session) -> list[dict]:
    """
    Compute and upsert CAGR for every portfolio in the DB.
    Returns a list of dicts: [{"portfolio": name, "cagr": value}, ...]
    """
    portfolios = session.query(Portfolio).all()
    results = []

    for portfolio in portfolios:
        # 1. Build equity curve
        df = calculate_portfolio_equity_curve(
            session, portfolio.portfolio_id, portfolio.start_date
        )

        # 2. Compute CAGR
        result = calculate_cagr(df)
        if result is None:
            logger.warning(
                "Insufficient equity curve data for portfolio %s, skipping",
                portfolio.name,
            )
            continue

        cagr, start_date, end_date = result

        # 3. Upsert via repo — no direct model construction here
        save_portfolio_metrics(
            session,
            portfolio_id=portfolio.portfolio_id,
            metrics={"CAGR": cagr},
            start_date=start_date.date(),
            end_date=end_date.date(),
        )

        results.append({"portfolio": portfolio.name, "cagr": cagr})
        logger.info("CAGR for %s: %.4f", portfolio.name, cagr)

    # commit is handled by get_session() in the entry point script
    return results