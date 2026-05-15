"""
src/portfolio/optimized_equity_curve.py

Builds an equity curve for an optimized portfolio using
stored weights + price history.

Unlike the regular equity curve (which uses quantities),
this normalizes to a $1 starting value and applies weights
as fixed percentage allocations.
"""

import pandas as pd
from sqlalchemy.orm import Session

from data.models import OptimizedPortfolio, Asset
from data.models.optimized import OptimizedPortfolioAsset
from data.repositories.optimized_repo import get_weights
from data.repositories.price_repo import get_price_history


def calculate_optimized_equity_curve(
    session: Session,
    optimized_portfolio_id,
    start_date=None,
    initial_value: float = 1.0,
) -> pd.DataFrame:
    """
    Build an equity curve for an optimized portfolio.

    Uses stored weights and price history to simulate
    a buy-and-hold portfolio starting at `initial_value`.

    Parameters
    ----------
    session : Session
    optimized_portfolio_id : UUID
    start_date : date, optional
        If None, uses earliest available price date.
    initial_value : float
        Starting portfolio value (default 1.0 for normalized curve)

    Returns
    -------
    pd.DataFrame
        Columns: Date, total_value
    """

    # 1. Load weights {"AAPL": 0.25, "MSFT": 0.25, ...}
    weights = get_weights(session, optimized_portfolio_id)
    if not weights:
        return pd.DataFrame()

    assets = list(weights.keys())

    # 2. Load price matrix (wide format: dates x symbols)
    price_df = get_price_history(session=session, assets=assets)
    if price_df.empty:
        return pd.DataFrame()

    price_df = price_df.astype(float)

    # 3. Filter by start_date
    if start_date is not None:
        price_df = price_df[price_df.index >= pd.Timestamp(start_date)]

    if price_df.empty:
        return pd.DataFrame()

    # 4. Normalize prices to 1.0 at start, apply weights
    #    Each asset contributes: weight * (price_t / price_0)
    normalized = price_df / price_df.iloc[0]
    weight_series = pd.Series(weights)
    portfolio_values = normalized.mul(weight_series).sum(axis=1) * initial_value

    # 5. Output in same format as calculate_portfolio_equity_curve
    result = portfolio_values.reset_index()
    result.columns = ["Date", "total_value"]
    return result