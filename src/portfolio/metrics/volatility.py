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
    if df.empty or len(df) < 2:
        return None

    df = df.sort_values("Date").copy()
    df["daily_return"] = df["total_value"].pct_change()
    df = df.dropna(subset=["daily_return"])

    if len(df) < 1:
        return None

    start_date = pd.to_datetime(df["Date"].iloc[0])
    end_date = pd.to_datetime(df["Date"].iloc[-1])

    volatility = float(df["daily_return"].std() * (252 ** 0.5))  # annualized

    return volatility, start_date, end_date