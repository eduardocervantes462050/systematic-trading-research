"""
src/data/repositories/client_repo.py

DB query functions for Client, Portfolio, PortfolioAsset, and Transaction.
All functions accept a SQLAlchemy Session and return ORM objects or None.
"""

from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy.orm import Session

from data.models.client import Client
from data.models.portfolio import Portfolio, PortfolioAsset
from data.models.transaction import Transaction
from data.models.asset import Asset


# ─────────────────────────────────────────────
# CLIENT
# ─────────────────────────────────────────────

def get_all_clients(session: Session) -> list[Client]:
    return session.query(Client).order_by(Client.name).all()


def get_client_by_id(session: Session, client_id: str) -> Optional[Client]:
    return session.query(Client).filter(Client.client_id == uuid.UUID(client_id)).first()


def get_client_by_email(session: Session, email: str) -> Optional[Client]:
    return session.query(Client).filter(Client.email == email).first()


def create_client(session: Session, name: str, email: str, phone: str | None = None) -> Client:
    client = Client(name=name, email=email, phone=phone)
    session.add(client)
    session.flush()  # get client_id without committing
    return client


def update_client(session: Session, client_id: str, **fields) -> Client:
    """
    Update any Client field by keyword argument.
    Allowed fields: name, email, phone
    """
    allowed = {"name", "email", "phone"}
    invalid = set(fields) - allowed
    if invalid:
        raise ValueError(f"Cannot update field(s): {invalid}. Allowed: {allowed}")

    client = get_client_by_id(session, client_id)
    if not client:
        raise LookupError(f"No client found with id={client_id}")

    for field, value in fields.items():
        setattr(client, field, value)

    session.flush()
    return client


def delete_client(session: Session, client_id: str) -> None:
    client = get_client_by_id(session, client_id)
    if not client:
        raise LookupError(f"No client found with id={client_id}")
    session.delete(client)
    session.flush()


# ─────────────────────────────────────────────
# PORTFOLIO
# ─────────────────────────────────────────────

def get_portfolios_by_client(session: Session, client_id: str) -> list[Portfolio]:
    return (
        session.query(Portfolio)
        .filter(Portfolio.client_id == uuid.UUID(client_id))
        .order_by(Portfolio.name)
        .all()
    )


def get_portfolio_by_id(session: Session, portfolio_id: str) -> Optional[Portfolio]:
    return session.query(Portfolio).filter(
        Portfolio.portfolio_id == uuid.UUID(portfolio_id)
    ).first()


def create_portfolio(
    session: Session,
    client_id: str,
    name: str,
    risk_level: str,
    start_date: str,  # ISO format: YYYY-MM-DD
) -> Portfolio:
    from datetime import datetime
    allowed_risk = {"low", "medium", "high"}
    if risk_level not in allowed_risk:
        raise ValueError(f"risk_level must be one of {allowed_risk}, got '{risk_level}'")

    portfolio = Portfolio(
        client_id=uuid.UUID(client_id),
        name=name,
        risk_level=risk_level,
        start_date=datetime.fromisoformat(start_date),
    )
    session.add(portfolio)
    session.flush()
    return portfolio


def update_portfolio(session: Session, portfolio_id: str, **fields) -> Portfolio:
    allowed = {"name", "risk_level"}
    invalid = set(fields) - allowed
    if invalid:
        raise ValueError(f"Cannot update field(s): {invalid}. Allowed: {allowed}")

    portfolio = get_portfolio_by_id(session, portfolio_id)
    if not portfolio:
        raise LookupError(f"No portfolio found with id={portfolio_id}")

    if "risk_level" in fields and fields["risk_level"] not in {"low", "medium", "high"}:
        raise ValueError("risk_level must be 'low', 'medium', or 'high'")

    for field, value in fields.items():
        setattr(portfolio, field, value)

    session.flush()
    return portfolio


# ─────────────────────────────────────────────
# POSITIONS  (PortfolioAsset)
# ─────────────────────────────────────────────

def get_positions_by_portfolio(session: Session, portfolio_id: str) -> list[PortfolioAsset]:
    return (
        session.query(PortfolioAsset)
        .filter(PortfolioAsset.portfolio_id == uuid.UUID(portfolio_id))
        .all()
    )


def get_position(session: Session, portfolio_id: str, symbol: str) -> Optional[PortfolioAsset]:
    asset = session.query(Asset).filter(Asset.symbol == symbol.upper()).first()
    if not asset:
        return None
    return (
        session.query(PortfolioAsset)
        .filter(
            PortfolioAsset.portfolio_id == uuid.UUID(portfolio_id),
            PortfolioAsset.asset_id == asset.asset_id,
        )
        .first()
    )


def upsert_position(
    session: Session,
    portfolio_id: str,
    symbol: str,
    quantity: float,
    avg_price: float,
) -> PortfolioAsset:
    """Create or overwrite a position for a given symbol in a portfolio."""
    asset = session.query(Asset).filter(Asset.symbol == symbol.upper()).first()
    if not asset:
        raise LookupError(f"Asset with symbol '{symbol.upper()}' not found in database")

    position = get_position(session, portfolio_id, symbol)
    if position:
        position.quantity = quantity
        position.avg_price = avg_price
    else:
        position = PortfolioAsset(
            portfolio_id=uuid.UUID(portfolio_id),
            asset_id=asset.asset_id,
            quantity=quantity,
            avg_price=avg_price,
        )
        session.add(position)

    session.flush()
    return position


def delete_position(session: Session, portfolio_id: str, symbol: str) -> None:
    position = get_position(session, portfolio_id, symbol)
    if not position:
        raise LookupError(
            f"No position for '{symbol.upper()}' in portfolio {portfolio_id}"
        )
    session.delete(position)
    session.flush()


# ─────────────────────────────────────────────
# TRANSACTIONS
# ─────────────────────────────────────────────

def get_transactions_by_portfolio(
    session: Session, portfolio_id: str
) -> list[Transaction]:
    return (
        session.query(Transaction)
        .filter(Transaction.portfolio_id == uuid.UUID(portfolio_id))
        .order_by(Transaction.transaction_date.desc())
        .all()
    )


def add_transaction(
    session: Session,
    portfolio_id: str,
    symbol: str,
    tx_type: str,
    quantity: float,
    price: float,
) -> Transaction:
    if tx_type not in {"buy", "sell"}:
        raise ValueError(f"Transaction type must be 'buy' or 'sell', got '{tx_type}'")

    asset = session.query(Asset).filter(Asset.symbol == symbol.upper()).first()
    if not asset:
        raise LookupError(f"Asset '{symbol.upper()}' not found in database")

    tx = Transaction(
        portfolio_id=uuid.UUID(portfolio_id),
        asset_id=asset.asset_id,
        type=tx_type,
        quantity=quantity,
        price=price,
    )
    session.add(tx)
    session.flush()
    return tx