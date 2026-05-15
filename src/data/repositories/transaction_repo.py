"""
src/data/repositories/transaction_repo.py

Transaction database operations.
"""

import logging
from decimal import Decimal
from typing import Optional
from uuid import UUID

import pandas as pd
from sqlalchemy.orm import Session

from data.models import Transaction

logger = logging.getLogger(__name__)


# =============================================================================
# TRANSACTION OPERATIONS
# =============================================================================


def record_transaction(
    session: Session,
    portfolio_id: UUID,
    asset_id: UUID,
    tx_type: str,
    quantity: Decimal,
    price: Decimal,
) -> Transaction:
    """Record a single buy or sell transaction."""
    tx = Transaction(
        portfolio_id=portfolio_id,
        asset_id=asset_id,
        type=tx_type,
        quantity=quantity,
        price=price,
    )
    session.add(tx)
    session.flush()
    logger.info(
        "Recorded %s of %.4f units @ %.2f for portfolio %s",
        tx_type,
        quantity,
        price,
        portfolio_id,
    )
    return tx


def get_transactions(
    session: Session,
    portfolio_id: UUID,
    asset_id: UUID = None,
    tx_type: str = None,
    start_date: str = None,
    end_date: str = None,
) -> pd.DataFrame:
    """
    Return transactions for a portfolio as a DataFrame.
    All filters are optional:
        - asset_id   : filter by a specific asset
        - tx_type    : 'buy' or 'sell'
        - start_date : 'YYYY-MM-DD'
        - end_date   : 'YYYY-MM-DD'
    """
    query = (
        session.query(Transaction)
        .filter_by(portfolio_id=portfolio_id)
    )

    if asset_id:
        query = query.filter(Transaction.asset_id == asset_id)
    if tx_type:
        query = query.filter(Transaction.type == tx_type)
    if start_date:
        query = query.filter(Transaction.transaction_date >= start_date)
    if end_date:
        query = query.filter(Transaction.transaction_date <= end_date)

    rows = query.order_by(Transaction.transaction_date).all()

    if not rows:
        return pd.DataFrame()

    return pd.DataFrame(
        [
            {
                "transaction_id": r.transaction_id,
                "asset_id": r.asset_id,
                "type": r.type,
                "quantity": float(r.quantity),
                "price": float(r.price),
                "transaction_date": r.transaction_date,
            }
            for r in rows
        ]
    )


def get_transaction_by_id(
    session: Session,
    transaction_id: UUID,
) -> Optional[Transaction]:
    """Fetch a single transaction by UUID. Returns None if not found."""
    return session.query(Transaction).filter_by(transaction_id=transaction_id).first()


def delete_transaction(
    session: Session,
    transaction_id: UUID,
) -> bool:
    """
    Delete a transaction by UUID.
    Returns True if deleted, False if not found.
    """
    tx = get_transaction_by_id(session, transaction_id)
    if not tx:
        logger.warning("Transaction %s not found, nothing deleted", transaction_id)
        return False
    session.delete(tx)
    session.flush()
    logger.info("Deleted transaction %s", transaction_id)
    return True


def get_transaction_summary(
    session: Session,
    portfolio_id: UUID,
) -> pd.DataFrame:
    """
    Return a summary of total bought and sold per asset for a portfolio.

    Returns a DataFrame with columns:
        - asset_id
        - total_bought   (sum of quantity where type='buy')
        - total_sold     (sum of quantity where type='sell')
        - net_quantity   (total_bought - total_sold)
    """
    rows = (
        session.query(Transaction)
        .filter_by(portfolio_id=portfolio_id)
        .all()
    )

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(
        [
            {
                "asset_id": r.asset_id,
                "type": r.type,
                "quantity": float(r.quantity),
            }
            for r in rows
        ]
    )

    bought = (
        df[df["type"] == "buy"]
        .groupby("asset_id")["quantity"]
        .sum()
        .rename("total_bought")
    )
    sold = (
        df[df["type"] == "sell"]
        .groupby("asset_id")["quantity"]
        .sum()
        .rename("total_sold")
    )

    summary = pd.concat([bought, sold], axis=1).fillna(0)
    summary["net_quantity"] = summary["total_bought"] - summary["total_sold"]
    return summary.reset_index()