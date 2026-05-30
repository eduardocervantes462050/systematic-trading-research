"""
src/services/client_service.py

Business logic for client intake operations.
All functions open/close their own session via the passed SessionFactory,
matching the pattern used in optimization_service.py.
"""

from __future__ import annotations

from data.engine import get_session
import data.repositories.client_repo as repo


# ─────────────────────────────────────────────
# CLIENT
# ─────────────────────────────────────────────

def list_clients(SessionFactory) -> list[dict]:
    with get_session(SessionFactory) as session:
        clients = repo.get_all_clients(session)
        return [
            {
                "client_id": str(c.client_id),
                "name": c.name,
                "email": c.email,
                "phone": c.phone or "—",
                "created_at": str(c.created_at)[:10],
            }
            for c in clients
        ]


def show_client(SessionFactory, client_id: str) -> dict:
    with get_session(SessionFactory) as session:
        client = repo.get_client_by_id(session, client_id)
        if not client:
            raise LookupError(f"No client found with id={client_id}")
        portfolios = repo.get_portfolios_by_client(session, client_id)
        return {
            "client_id": str(client.client_id),
            "name": client.name,
            "email": client.email,
            "phone": client.phone or "—",
            "created_at": str(client.created_at)[:10],
            "portfolios": [
                {
                    "portfolio_id": str(p.portfolio_id),
                    "name": p.name,
                    "risk_level": p.risk_level,
                    "start_date": str(p.start_date)[:10],
                }
                for p in portfolios
            ],
        }


def add_client(SessionFactory, name: str, email: str, phone: str | None) -> dict:
    with get_session(SessionFactory) as session:
        existing = repo.get_client_by_email(session, email)
        if existing:
            raise ValueError(f"A client with email '{email}' already exists.")
        client = repo.create_client(session, name=name, email=email, phone=phone)
        session.commit()
        return {"client_id": str(client.client_id), "name": client.name, "email": client.email}


def correct_client(SessionFactory, client_id: str, field: str, value: str) -> dict:
    with get_session(SessionFactory) as session:
        client = repo.update_client(session, client_id, **{field: value})
        session.commit()
        return {"client_id": str(client.client_id), "updated": field, "new_value": value}


def remove_client(SessionFactory, client_id: str) -> None:
    with get_session(SessionFactory) as session:
        repo.delete_client(session, client_id)
        session.commit()


# ─────────────────────────────────────────────
# PORTFOLIO
# ─────────────────────────────────────────────

def add_portfolio(
    SessionFactory,
    client_id: str,
    name: str,
    risk_level: str,
    start_date: str,
) -> dict:
    with get_session(SessionFactory) as session:
        portfolio = repo.create_portfolio(
            session,
            client_id=client_id,
            name=name,
            risk_level=risk_level,
            start_date=start_date,
        )
        session.commit()
        return {
            "portfolio_id": str(portfolio.portfolio_id),
            "name": portfolio.name,
            "risk_level": portfolio.risk_level,
        }


def update_portfolio(SessionFactory, portfolio_id: str, field: str, value: str) -> dict:
    with get_session(SessionFactory) as session:
        portfolio = repo.update_portfolio(session, portfolio_id, **{field: value})
        session.commit()
        return {
            "portfolio_id": str(portfolio.portfolio_id),
            "updated": field,
            "new_value": value,
        }


def list_portfolios(SessionFactory, client_id: str) -> list[dict]:
    with get_session(SessionFactory) as session:
        portfolios = repo.get_portfolios_by_client(session, client_id)
        return [
            {
                "portfolio_id": str(p.portfolio_id),
                "name": p.name,
                "risk_level": p.risk_level,
                "start_date": str(p.start_date)[:10],
            }
            for p in portfolios
        ]


# ─────────────────────────────────────────────
# POSITIONS
# ─────────────────────────────────────────────

def list_positions(SessionFactory, portfolio_id: str) -> list[dict]:
    with get_session(SessionFactory) as session:
        positions = repo.get_positions_by_portfolio(session, portfolio_id)
        return [
            {
                "symbol": p.asset.symbol,
                "name": p.asset.name,
                "quantity": float(p.quantity),
                "avg_price": float(p.avg_price) if p.avg_price else None,
                "market_value": (
                    round(float(p.quantity) * float(p.avg_price), 2)
                    if p.avg_price
                    else None
                ),
            }
            for p in positions
        ]


def set_position(
    SessionFactory,
    portfolio_id: str,
    symbol: str,
    quantity: float,
    avg_price: float,
) -> dict:
    """
    Directly overwrite a position without recording a transaction.
    Use this only for corrections/fixes. For normal intake use transaction add.
    """
    with get_session(SessionFactory) as session:
        position = repo.upsert_position(
            session,
            portfolio_id=portfolio_id,
            symbol=symbol,
            quantity=quantity,
            avg_price=avg_price,
        )
        session.commit()
        return {
            "symbol": symbol.upper(),
            "quantity": float(position.quantity),
            "avg_price": float(position.avg_price),
        }


def remove_position(SessionFactory, portfolio_id: str, symbol: str) -> None:
    with get_session(SessionFactory) as session:
        # Auto-record a sell transaction for the full quantity before deleting
        existing = repo.get_position(session, portfolio_id, symbol)
        if existing and float(existing.quantity) > 0:
            repo.add_transaction(
                session,
                portfolio_id=portfolio_id,
                symbol=symbol,
                tx_type="sell",
                quantity=float(existing.quantity),
                price=float(existing.avg_price) if existing.avg_price else 0.0,
            )
        repo.delete_position(session, portfolio_id, symbol)
        session.commit()


# ─────────────────────────────────────────────
# TRANSACTIONS
# ─────────────────────────────────────────────

def list_transactions(SessionFactory, portfolio_id: str) -> list[dict]:
    with get_session(SessionFactory) as session:
        txs = repo.get_transactions_by_portfolio(session, portfolio_id)
        return [
            {
                "transaction_id": str(t.transaction_id),
                "symbol": t.asset.symbol,
                "type": t.type,
                "quantity": float(t.quantity),
                "price": float(t.price),
                "total": round(float(t.quantity) * float(t.price), 2),
                "date": str(t.transaction_date)[:10],
            }
            for t in txs
        ]


def record_transaction(
    SessionFactory,
    portfolio_id: str,
    symbol: str,
    tx_type: str,
    quantity: float,
    price: float,
) -> dict:
    """
    Record a transaction AND update the position in portfolio_assets.
    - buy  → increases quantity, recalculates weighted avg price
    - sell → decreases quantity; removes position if qty reaches 0
    This is the single source of truth for all position changes.
    """
    with get_session(SessionFactory) as session:
        tx = repo.add_transaction(
            session,
            portfolio_id=portfolio_id,
            symbol=symbol,
            tx_type=tx_type,
            quantity=quantity,
            price=price,
        )

        # Update position to reflect the transaction
        existing = repo.get_position(session, portfolio_id, symbol)

        if tx_type == "buy":
            if existing:
                # Recalculate weighted average price
                old_qty   = float(existing.quantity)
                old_cost  = old_qty * float(existing.avg_price)
                new_cost  = quantity * price
                new_qty   = old_qty + quantity
                new_avg   = (old_cost + new_cost) / new_qty
            else:
                new_qty = quantity
                new_avg = price
            repo.upsert_position(session, portfolio_id, symbol, new_qty, new_avg)

        elif tx_type == "sell":
            if existing:
                new_qty = float(existing.quantity) - quantity
                if new_qty <= 0.0001:
                    repo.delete_position(session, portfolio_id, symbol)
                else:
                    repo.upsert_position(
                        session, portfolio_id, symbol,
                        new_qty, float(existing.avg_price)
                    )

        session.commit()
        return {
            "transaction_id": str(tx.transaction_id),
            "symbol": symbol.upper(),
            "type": tx_type,
            "quantity": float(tx.quantity),
            "price": float(tx.price),
            "total": round(float(tx.quantity) * float(tx.price), 2),
        }


# ─────────────────────────────────────────────
# REBALANCE HELPERS
# ─────────────────────────────────────────────

def get_latest_optimized_weights(SessionFactory, portfolio_id: str) -> tuple[dict[str, float], str]:
    """
    Return (weights_dict, opt_name) from the most recent OptimizedPortfolio run.
    weights_dict maps symbol -> weight (float).
    Returns ({}, "") if nothing found.
    """
    from data.models.optimized import OptimizedPortfolio, OptimizedPortfolioAsset
    from data.models.asset import Asset
    import uuid

    with get_session(SessionFactory) as session:
        opt = (
            session.query(OptimizedPortfolio)
            .filter(OptimizedPortfolio.portfolio_id == uuid.UUID(portfolio_id))
            .order_by(OptimizedPortfolio.created_at.desc())
            .first()
        )
        if not opt:
            return {}, ""

        rows = (
            session.query(OptimizedPortfolioAsset, Asset)
            .join(Asset, OptimizedPortfolioAsset.asset_id == Asset.asset_id)
            .filter(OptimizedPortfolioAsset.optimized_portfolio_id == opt.optimized_portfolio_id)
            .all()
        )
        weights = {asset.symbol: float(opa.weight) for opa, asset in rows}
        return weights, opt.name


def get_latest_prices(SessionFactory, symbols: list[str]) -> dict[str, float]:
    """
    Return {symbol: latest_close} for each symbol from asset_prices.
    """
    from data.models.asset import Asset, AssetPrice
    from sqlalchemy import func

    with get_session(SessionFactory) as session:
        prices = {}
        for symbol in symbols:
            asset = session.query(Asset).filter(Asset.symbol == symbol.upper()).first()
            if not asset:
                continue
            latest = (
                session.query(AssetPrice)
                .filter(AssetPrice.asset_id == asset.asset_id)
                .order_by(AssetPrice.price_date.desc())
                .first()
            )
            if latest and latest.close:
                prices[symbol.upper()] = float(latest.close)
        return prices


# ─────────────────────────────────────────────
# POSITION HISTORY
# ─────────────────────────────────────────────

def get_position_history(SessionFactory, portfolio_id: str, as_of_date: str) -> list[dict]:
    """
    Reconstruct portfolio positions as of a given date by replaying
    all transactions up to and including that date.

    Returns a list of {symbol, quantity, avg_price, total_cost} dicts.
    Positions with zero quantity (fully sold) are excluded.
    """
    from data.models.transaction import Transaction
    from data.models.asset import Asset
    import uuid
    from datetime import datetime

    # Support both date-only (YYYY-MM-DD) and full datetime (YYYY-MM-DD HH:MM:SS)
    try:
        cutoff = datetime.fromisoformat(as_of_date)
    except ValueError:
        raise ValueError(f"Invalid datetime format: '{as_of_date}'. Use YYYY-MM-DD or YYYY-MM-DD HH:MM:SS")
    # If only a date was given (no time), default to end of that day
    if cutoff.hour == 0 and cutoff.minute == 0 and cutoff.second == 0 and 'T' not in as_of_date and ' ' not in as_of_date:
        cutoff = cutoff.replace(hour=23, minute=59, second=59)

    with get_session(SessionFactory) as session:
        txs = (
            session.query(Transaction, Asset)
            .join(Asset, Transaction.asset_id == Asset.asset_id)
            .filter(
                Transaction.portfolio_id == uuid.UUID(portfolio_id),
                Transaction.transaction_date <= cutoff,
            )
            .order_by(Transaction.transaction_date.asc())
            .all()
        )

        # Replay: track qty and weighted avg price per symbol
        holdings: dict[str, dict] = {}
        for tx, asset in txs:
            sym = asset.symbol
            qty = float(tx.quantity)
            price = float(tx.price)

            if sym not in holdings:
                holdings[sym] = {"quantity": 0.0, "total_cost": 0.0}

            if tx.type == "buy":
                holdings[sym]["total_cost"] += qty * price
                holdings[sym]["quantity"]   += qty
            elif tx.type == "sell":
                # Reduce cost basis proportionally
                if holdings[sym]["quantity"] > 0:
                    avg = holdings[sym]["total_cost"] / holdings[sym]["quantity"]
                    holdings[sym]["total_cost"] -= qty * avg
                holdings[sym]["quantity"] -= qty

        # Build result — exclude zero/negative positions
        result = []
        for sym, h in sorted(holdings.items()):
            qty = round(h["quantity"], 6)
            if qty <= 0.0001:
                continue
            avg_price = (h["total_cost"] / qty) if qty > 0 else 0.0
            result.append({
                "symbol":     sym,
                "quantity":   qty,
                "avg_price":  round(avg_price, 2),
                "total_cost": round(h["total_cost"], 2),
            })

        return result
    