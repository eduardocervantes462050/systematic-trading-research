"""
src/data/repositories/optimized_repo.py

OptimizedPortfolio, OptimizedPortfolioAsset, and OptimizedPortfolioMetrics
database operations.
"""

import logging
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from data.models import (
    Asset,
    OptimizedPortfolio,
    OptimizedPortfolioAsset,
    OptimizedPortfolioMetrics,
)

logger = logging.getLogger(__name__)


# =============================================================================
# OPTIMIZED PORTFOLIO OPERATIONS
# =============================================================================


def create_optimized_portfolio(
    session: Session,
    portfolio_id: UUID,
    method: str,
    name: str = None,
    target_risk_level: str = None,
) -> OptimizedPortfolio:
    """Create and flush a new optimized portfolio record."""
    opt = OptimizedPortfolio(
        portfolio_id=portfolio_id,
        name=name or f"{method}_portfolio",
        optimization_method=method,
        target_risk_level=target_risk_level,
    )
    session.add(opt)
    session.flush()
    logger.info("Created optimized portfolio (%s) for portfolio %s", method, portfolio_id)
    return opt


def get_optimized_portfolio_by_id(
    session: Session,
    optimized_portfolio_id: UUID,
) -> Optional[OptimizedPortfolio]:
    """Fetch a single optimized portfolio by UUID."""
    return (
        session.query(OptimizedPortfolio)
        .filter_by(optimized_portfolio_id=optimized_portfolio_id)
        .first()
    )


def get_optimized_portfolios_by_portfolio(
    session: Session,
    portfolio_id: UUID,
) -> list[OptimizedPortfolio]:
    """Return all optimized portfolios for a given portfolio_id."""
    return (
        session.query(OptimizedPortfolio)
        .filter_by(portfolio_id=portfolio_id)
        .order_by(OptimizedPortfolio.created_at)
        .all()
    )


def get_optimized_portfolio_by_method(
    session: Session,
    portfolio_id: UUID,
    method: str,
) -> Optional[OptimizedPortfolio]:
    """
    Fetch the most recent optimized portfolio for a given
    portfolio_id and optimization method.
    """
    return (
        session.query(OptimizedPortfolio)
        .filter_by(portfolio_id=portfolio_id, optimization_method=method)
        .order_by(OptimizedPortfolio.created_at.desc())
        .first()
    )


def upsert_optimized_portfolio(
    session: Session,
    portfolio_id: UUID,
    method: str,
    name: str = None,
    target_risk_level: str = None,
) -> OptimizedPortfolio:
    """
    Return existing optimized portfolio for this method if it exists,
    wiping its weights so they can be rewritten.
    Creates a new one if it doesn't exist.
    """
    existing = get_optimized_portfolio_by_method(session, portfolio_id, method)

    if existing:
        # wipe old weights so save_weights can rewrite them cleanly
        session.query(OptimizedPortfolioAsset).filter_by(
            optimized_portfolio_id=existing.optimized_portfolio_id
        ).delete()
        session.flush()
        logger.info(
            "Wiped weights for existing optimized portfolio (%s) for portfolio %s",
            method,
            portfolio_id,
        )
        return existing

    return create_optimized_portfolio(
        session, portfolio_id, method, name, target_risk_level
    )


def update_optimized_portfolio_stats(
    session: Session,
    optimized_portfolio_id: UUID,
    expected_return: float = None,
    expected_volatility: float = None,
    sharpe_ratio: float = None,
) -> Optional[OptimizedPortfolio]:
    """
    Update the summary stats on the optimized portfolio record itself.
    Call this after metrics are computed.
    """
    opt = get_optimized_portfolio_by_id(session, optimized_portfolio_id)
    if not opt:
        logger.warning("OptimizedPortfolio %s not found", optimized_portfolio_id)
        return None
    if expected_return is not None:
        opt.expected_return = Decimal(str(round(expected_return, 6)))
    if expected_volatility is not None:
        opt.expected_volatility = Decimal(str(round(expected_volatility, 6)))
    if sharpe_ratio is not None:
        opt.sharpe_ratio = Decimal(str(round(sharpe_ratio, 6)))
    session.flush()
    logger.info("Updated stats for optimized portfolio %s", optimized_portfolio_id)
    return opt


def delete_optimized_portfolio(
    session: Session,
    optimized_portfolio_id: UUID,
) -> bool:
    """
    Delete an optimized portfolio by UUID.
    Cascades to assets and metrics via DB constraint.
    Returns True if deleted, False if not found.
    """
    opt = get_optimized_portfolio_by_id(session, optimized_portfolio_id)
    if not opt:
        logger.warning("OptimizedPortfolio %s not found, nothing deleted", optimized_portfolio_id)
        return False
    session.delete(opt)
    session.flush()
    logger.info("Deleted optimized portfolio %s", optimized_portfolio_id)
    return True


# =============================================================================
# OPTIMIZED PORTFOLIO ASSET (WEIGHTS) OPERATIONS
# =============================================================================


def save_weights(
    session: Session,
    optimized_portfolio_id: UUID,
    weights: dict,
) -> None:
    """
    Batch insert weights into optimized_portfolio_assets.
    One row per asset. Fetches all assets in a single query.
    """
    symbols = list(weights.keys())
    assets = session.query(Asset).filter(Asset.symbol.in_(symbols)).all()
    asset_map = {a.symbol: a for a in assets}

    missing = set(symbols) - set(asset_map)
    if missing:
        logger.warning("Assets not found, skipping: %s", missing)

    rows = [
        OptimizedPortfolioAsset(
            optimized_portfolio_id=optimized_portfolio_id,
            asset_id=asset_map[symbol].asset_id,
            weight=Decimal(str(round(weight, 6))),
        )
        for symbol, weight in weights.items()
        if symbol in asset_map
    ]

    session.add_all(rows)
    session.flush()
    logger.info(
        "Saved %d weights for optimized portfolio %s",
        len(rows),
        optimized_portfolio_id,
    )


def get_weights(
    session: Session,
    optimized_portfolio_id: UUID,
) -> dict[str, float]:
    """
    Fetch weights for an optimized portfolio.
    Returns a dict keyed by asset symbol: {"AAPL": 0.25, ...}
    """
    rows = (
        session.query(OptimizedPortfolioAsset, Asset)
        .join(Asset, OptimizedPortfolioAsset.asset_id == Asset.asset_id)
        .filter(OptimizedPortfolioAsset.optimized_portfolio_id == optimized_portfolio_id)
        .all()
    )
    return {asset.symbol: float(opa.weight) for opa, asset in rows}


# =============================================================================
# OPTIMIZED PORTFOLIO METRICS OPERATIONS
# =============================================================================


def save_optimized_metrics(
    session: Session,
    optimized_portfolio_id: UUID,
    metrics: dict,
    start_date=None,
    end_date=None,
    extra_data: dict = None,
) -> None:
    """
    Upsert metrics into optimized_portfolio_metrics.
    If a row with the same (optimized_portfolio_id, metric_type,
    start_date, end_date) exists, it gets overwritten.
    """
    for metric_type, value in metrics.items():
        existing = (
            session.query(OptimizedPortfolioMetrics)
            .filter_by(
                optimized_portfolio_id=optimized_portfolio_id,
                metric_type=metric_type,
                start_date=start_date,
                end_date=end_date,
            )
            .first()
        )
        if existing:
            existing.value = Decimal(str(round(value, 8)))
            existing.extra_data = extra_data
            logger.info("Updated metric %s = %.6f", metric_type, value)
        else:
            session.add(
                OptimizedPortfolioMetrics(
                    optimized_portfolio_id=optimized_portfolio_id,
                    metric_type=metric_type,
                    value=Decimal(str(round(value, 8))),
                    start_date=start_date,
                    end_date=end_date,
                    extra_data=extra_data,
                )
            )
            logger.info("Inserted metric %s = %.6f", metric_type, value)

    logger.info(
        "Saved %d metrics for optimized portfolio %s",
        len(metrics),
        optimized_portfolio_id,
    )


def get_optimized_metrics(
    session: Session,
    optimized_portfolio_id: UUID,
    metric_type: str = None,
) -> list[OptimizedPortfolioMetrics]:
    """
    Fetch metrics for an optimized portfolio.
    Optionally filter by metric_type (e.g. 'SHARPE', 'VOLATILITY').
    """
    query = (
        session.query(OptimizedPortfolioMetrics)
        .filter_by(optimized_portfolio_id=optimized_portfolio_id)
    )
    if metric_type:
        query = query.filter_by(metric_type=metric_type)
    return query.order_by(OptimizedPortfolioMetrics.created_at).all()