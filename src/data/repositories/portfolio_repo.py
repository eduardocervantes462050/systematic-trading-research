"""
src/data/repositories/portfolio_repo.py

Portfolio, PortfolioAsset, PortfolioEquityCurve, and PortfolioMetrics database operations.
"""

import logging
from decimal import Decimal
from typing import Optional
from uuid import UUID

import pandas as pd
from sqlalchemy.orm import Session

from data.models import (
    Portfolio,
    PortfolioAsset,
    PortfolioEquityCurve,
    PortfolioMetrics,
)

logger = logging.getLogger(__name__)


# =============================================================================
# PORTFOLIO OPERATIONS
# =============================================================================


def create_portfolio(
    session: Session,
    client_id: UUID,
    name: str,
    risk_level: str = "medium",
    start_date=None,
) -> Portfolio:
    """Create and flush a new portfolio record."""
    portfolio = Portfolio(
        client_id=client_id,
        name=name,
        risk_level=risk_level,
        start_date=start_date,
    )
    session.add(portfolio)
    session.flush()
    logger.info("Created portfolio '%s' for client %s", name, client_id)
    return portfolio


def get_portfolio_by_id(session: Session, portfolio_id: UUID) -> Optional[Portfolio]:
    """Fetch a single portfolio by UUID. Returns None if not found."""
    return session.query(Portfolio).filter_by(portfolio_id=portfolio_id).first()


def get_portfolios_by_client(session: Session, client_id: UUID) -> list[Portfolio]:
    """Return all portfolios for a given client."""
    return session.query(Portfolio).filter_by(client_id=client_id).all()


def update_portfolio(
    session: Session,
    portfolio_id: UUID,
    name: str = None,
    risk_level: str = None,
) -> Optional[Portfolio]:
    """
    Update a portfolio's name or risk level.
    Only updates fields that are explicitly passed.
    """
    portfolio = get_portfolio_by_id(session, portfolio_id)
    if not portfolio:
        logger.warning("Portfolio %s not found", portfolio_id)
        return None
    if name is not None:
        portfolio.name = name
    if risk_level is not None:
        portfolio.risk_level = risk_level
    session.flush()
    logger.info("Updated portfolio %s", portfolio_id)
    return portfolio


def delete_portfolio(session: Session, portfolio_id: UUID) -> bool:
    """
    Delete a portfolio by UUID.
    Cascades to portfolio_assets, transactions, equity_curves via DB constraint.
    Returns True if deleted, False if not found.
    """
    portfolio = get_portfolio_by_id(session, portfolio_id)
    if not portfolio:
        logger.warning("Portfolio %s not found, nothing deleted", portfolio_id)
        return False
    session.delete(portfolio)
    session.flush()
    logger.info("Deleted portfolio %s", portfolio_id)
    return True


# =============================================================================
# PORTFOLIO ASSET (HOLDINGS) OPERATIONS
# =============================================================================


def upsert_holding(
    session: Session,
    portfolio_id: UUID,
    asset_id: UUID,
    quantity: Decimal,
    avg_price: Decimal = None,
) -> PortfolioAsset:
    """Update quantity/avg_price if the holding exists, insert if not."""
    holding = (
        session.query(PortfolioAsset)
        .filter_by(portfolio_id=portfolio_id, asset_id=asset_id)
        .first()
    )
    if holding:
        holding.quantity = quantity
        holding.avg_price = avg_price
        logger.info("Updated holding for asset %s in portfolio %s", asset_id, portfolio_id)
    else:
        holding = PortfolioAsset(
            portfolio_id=portfolio_id,
            asset_id=asset_id,
            quantity=quantity,
            avg_price=avg_price,
        )
        session.add(holding)
        session.flush()
        logger.info("Inserted holding for asset %s in portfolio %s", asset_id, portfolio_id)
    return holding


def get_holdings(session: Session, portfolio_id: UUID) -> list[PortfolioAsset]:
    """Return all holdings for a portfolio."""
    return (
        session.query(PortfolioAsset)
        .filter_by(portfolio_id=portfolio_id)
        .all()
    )


def delete_holding(
    session: Session,
    portfolio_id: UUID,
    asset_id: UUID,
) -> bool:
    """
    Delete a single holding from a portfolio.
    Returns True if deleted, False if not found.
    """
    holding = (
        session.query(PortfolioAsset)
        .filter_by(portfolio_id=portfolio_id, asset_id=asset_id)
        .first()
    )
    if not holding:
        logger.warning(
            "Holding for asset %s in portfolio %s not found", asset_id, portfolio_id
        )
        return False
    session.delete(holding)
    session.flush()
    logger.info("Deleted holding for asset %s in portfolio %s", asset_id, portfolio_id)
    return True


# =============================================================================
# EQUITY CURVE OPERATIONS
# =============================================================================


def save_equity_curve(
    session: Session,
    portfolio_id: UUID,
    df: pd.DataFrame,
) -> int:
    """
    Save equity curve into DB.
    Skips existing (portfolio_id, date) rows.

    Expected df columns:
        - Date
        - total_value
    """
    if df is None or df.empty:
        return 0

    existing_dates = {
        r[0]
        for r in session.query(PortfolioEquityCurve.date)
        .filter(PortfolioEquityCurve.portfolio_id == portfolio_id)
        .all()
    }

    records = []
    for _, row in df.iterrows():
        dt = pd.to_datetime(row["Date"]).date()
        if dt in existing_dates:
            continue
        value = row["total_value"]
        if pd.isna(value):
            continue
        records.append(
            PortfolioEquityCurve(
                portfolio_id=portfolio_id,
                date=dt,
                total_value=Decimal(str(value)),
            )
        )

    if records:
        session.bulk_save_objects(records)
        session.flush()

    logger.info(
        "Inserted %d equity curve rows for portfolio %s",
        len(records),
        portfolio_id,
    )
    return len(records)


def get_equity_curve(
    session: Session,
    portfolio_id: UUID,
    start: str = None,
    end: str = None,
) -> pd.DataFrame:
    """
    Fetch equity curve for a portfolio as a DataFrame.
    Optional start/end filters as 'YYYY-MM-DD' strings.
    """
    query = (
        session.query(PortfolioEquityCurve)
        .filter_by(portfolio_id=portfolio_id)
    )
    if start:
        query = query.filter(PortfolioEquityCurve.date >= start)
    if end:
        query = query.filter(PortfolioEquityCurve.date <= end)

    rows = query.order_by(PortfolioEquityCurve.date).all()

    if not rows:
        return pd.DataFrame()

    return pd.DataFrame(
        [{"date": r.date, "total_value": float(r.total_value)} for r in rows]
    ).set_index("date")


# =============================================================================
# PORTFOLIO METRICS OPERATIONS
# =============================================================================


def save_portfolio_metrics(
    session: Session,
    portfolio_id: UUID,
    metrics: dict,
    start_date=None,
    end_date=None,
    extra_data: dict = None,
) -> None:
    """
    Upsert metrics into portfolio_metrics.
    If a row with the same (portfolio_id, metric_type, start_date, end_date)
    exists, it gets overwritten.
    """
    for metric_type, value in metrics.items():
        existing = (
            session.query(PortfolioMetrics)
            .filter_by(
                portfolio_id=portfolio_id,
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
                PortfolioMetrics(
                    portfolio_id=portfolio_id,
                    metric_type=metric_type,
                    value=Decimal(str(round(value, 8))),
                    start_date=start_date,
                    end_date=end_date,
                    extra_data=extra_data,
                )
            )
            logger.info("Inserted metric %s = %.6f", metric_type, value)

    logger.info("Saved %d metrics for portfolio %s", len(metrics), portfolio_id)


def get_portfolio_metrics(
    session: Session,
    portfolio_id: UUID,
    metric_type: str = None,
) -> list[PortfolioMetrics]:
    """
    Fetch metrics for a portfolio.
    Optionally filter by metric_type (e.g. 'SHARPE', 'VOLATILITY').
    """
    query = session.query(PortfolioMetrics).filter_by(portfolio_id=portfolio_id)
    if metric_type:
        query = query.filter_by(metric_type=metric_type)
    return query.order_by(PortfolioMetrics.created_at).all()


from sqlalchemy.orm import Session
from data.models import Portfolio


def get_portfolio_id_by_name(session: Session, name: str) -> str:
    portfolio = (
        session.query(Portfolio)
        .filter(Portfolio.name == name)
        .first()
    )

    if not portfolio:
        raise ValueError(f"Portfolio not found: {name}")

    return portfolio.portfolio_id