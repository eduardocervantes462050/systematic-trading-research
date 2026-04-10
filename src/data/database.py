"""
src/data/database.py

PostgreSQL database layer for the quantitative portfolio system.
Handles connection management, schema creation, and CRUD operations
for clients, portfolios, assets, transactions, and historical prices.
"""

import logging
from contextlib import contextmanager
from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID

import pandas as pd
import yaml
from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    create_engine,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Session, relationship, sessionmaker

logger = logging.getLogger(__name__)


# =============================================================================
# ENGINE & SESSION FACTORY
# =============================================================================


def get_engine(config_path: str = "config/settings.yaml"):
    """
    Build a SQLAlchemy engine from settings.yaml.

    Expected settings.yaml structure:
        database:
            host: localhost
            port: 5432
            name: portfolio_db
            user: postgres
            password: secret
            pool_size: 5
            max_overflow: 10
    """
    with open(config_path, "r") as f:
        cfg = yaml.safe_load(f)

    db = cfg["database"]
    url = (
        f"postgresql+psycopg2://{db['user']}:{db['password']}"
        f"@{db['host']}:{db['port']}/{db['name']}"
    )
    engine = create_engine(
        url,
        pool_size=db.get("pool_size", 5),
        max_overflow=db.get("max_overflow", 10),
        echo=db.get("echo", False),  # set True to log all SQL
    )
    logger.info(
        "Database engine created for %s:%s/%s", db["host"], db["port"], db["name"]
    )
    return engine


def get_session_factory(engine):
    """Return a configured sessionmaker bound to the given engine."""
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


@contextmanager
def get_session(session_factory):
    """
    Context manager that provides a transactional session scope.

    Usage:
        with get_session(SessionFactory) as session:
            session.add(some_object)
    """
    session: Session = session_factory()
    try:
        yield session
        session.commit()
    except SQLAlchemyError as exc:
        session.rollback()
        logger.error("Session rollback due to error: %s", exc)
        raise
    finally:
        session.close()


# =============================================================================
# ORM MODELS
# =============================================================================


class Base(DeclarativeBase):
    pass


class Client(Base):
    __tablename__ = "clients"

    client_id = Column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    name = Column(String(100), nullable=False)
    email = Column(String(150), nullable=False, unique=True)
    phone = Column(String(20))
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))

    portfolios = relationship(
        "Portfolio", back_populates="client", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("idx_clients_email", "email"),)

    def __repr__(self):
        return f"<Client(name={self.name!r}, email={self.email!r})>"


class Portfolio(Base):
    __tablename__ = "portfolios"

    portfolio_id = Column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    client_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("clients.client_id", ondelete="CASCADE"),
        nullable=False,
    )
    name = Column(String(100), nullable=False)
    risk_level = Column(String(20))
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    start_date = Column(DateTime, nullable=False)

    client = relationship("Client", back_populates="portfolios")
    portfolio_assets = relationship(
        "PortfolioAsset", back_populates="portfolio", cascade="all, delete-orphan"
    )
    transactions = relationship(
        "Transaction", back_populates="portfolio", cascade="all, delete-orphan"
    )

    equity_curves = relationship(
        "PortfolioEquityCurve", back_populates="portfolio", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "risk_level IN ('low', 'medium', 'high')", name="ck_portfolio_risk_level"
        ),
        Index("idx_portfolios_client_id", "client_id"),
    )

    def __repr__(self):
        return f"<Portfolio(name={self.name!r}, risk_level={self.risk_level!r})>"


class Asset(Base):
    __tablename__ = "assets"

    asset_id = Column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    name = Column(String(100), nullable=False)
    symbol = Column(String(10), nullable=False, unique=True)
    type = Column(String(50))
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))

    portfolio_assets = relationship("PortfolioAsset", back_populates="asset")
    transactions = relationship("Transaction", back_populates="asset")
    prices = relationship(
        "AssetPrice", back_populates="asset", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "type IN ('stock', 'crypto', 'bond', 'ETF')", name="ck_asset_type"
        ),
    )

    def __repr__(self):
        return f"<Asset(symbol={self.symbol!r}, type={self.type!r})>"


class PortfolioAsset(Base):
    __tablename__ = "portfolio_assets"

    id = Column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    portfolio_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("portfolios.portfolio_id", ondelete="CASCADE"),
        nullable=False,
    )
    asset_id = Column(
        PG_UUID(as_uuid=True), ForeignKey("assets.asset_id"), nullable=False
    )
    quantity = Column(Numeric(18, 6), nullable=False)
    avg_price = Column(Numeric(18, 2))

    portfolio = relationship("Portfolio", back_populates="portfolio_assets")
    asset = relationship("Asset", back_populates="portfolio_assets")

    __table_args__ = (
        UniqueConstraint("portfolio_id", "asset_id", name="unique_portfolio_asset"),
        Index("idx_portfolio_assets_portfolio", "portfolio_id"),
        Index("idx_portfolio_assets_asset", "asset_id"),
    )

    def __repr__(self):
        return f"<PortfolioAsset(quantity={self.quantity}, avg_price={self.avg_price})>"


class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id = Column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    portfolio_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("portfolios.portfolio_id", ondelete="CASCADE"),
        nullable=False,
    )
    asset_id = Column(
        PG_UUID(as_uuid=True), ForeignKey("assets.asset_id"), nullable=False
    )
    type = Column(String(10))
    quantity = Column(Numeric(18, 6), nullable=False)
    price = Column(Numeric(18, 2), nullable=False)
    transaction_date = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))

    portfolio = relationship("Portfolio", back_populates="transactions")
    asset = relationship("Asset", back_populates="transactions")

    __table_args__ = (
        CheckConstraint("type IN ('buy', 'sell')", name="ck_transaction_type"),
        Index("idx_transactions_portfolio", "portfolio_id"),
    )

    def __repr__(self):
        return f"<Transaction(type={self.type!r}, quantity={self.quantity}, price={self.price})>"


class AssetPrice(Base):
    __tablename__ = "asset_prices"

    id = Column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    asset_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("assets.asset_id", ondelete="CASCADE"),
        nullable=False,
    )

    # OHLCV
    price_date = Column(Date, nullable=False)
    open = Column(Numeric(18, 4))
    high = Column(Numeric(18, 4))
    low = Column(Numeric(18, 4))
    close = Column(Numeric(18, 4))
    volume = Column(Numeric(20, 2))

    # Returns
    return_ = Column("return", Numeric(18, 6))
    log_return = Column(Numeric(18, 6))
    cum_return = Column(Numeric(18, 6))

    # Volatility
    vol_20 = Column(Numeric(18, 6))
    vol_60 = Column(Numeric(18, 6))

    # Technical indicators
    rsi_14 = Column(Numeric(10, 4))
    macd = Column(Numeric(18, 6))
    macd_signal = Column(Numeric(18, 6))
    macd_hist = Column(Numeric(18, 6))

    # Risk metrics
    rolling_max = Column(Numeric(18, 4))
    drawdown = Column(Numeric(18, 6))

    # relationships
    asset = relationship("Asset", back_populates="prices")

    __table_args__ = (
        UniqueConstraint("asset_id", "price_date", name="unique_asset_date"),
        Index("idx_asset_prices_asset_date", "asset_id", "price_date"),
    )

    def __repr__(self):
        return f"<AssetPrice(close={self.close}, date={self.price_date})>"


# =============================================================================
# SCHEMA INITIALISATION
# =============================================================================


def init_db(engine) -> None:
    """
    Enable the pgcrypto extension and create all tables if they do not exist.
    Safe to call on every startup — uses CREATE IF NOT EXISTS semantics.
    """
    with engine.begin() as conn:
        conn.execute(text('CREATE EXTENSION IF NOT EXISTS "pgcrypto"'))
        logger.info("pgcrypto extension ensured.")

    Base.metadata.create_all(engine)
    logger.info("All tables created (or already exist).")


# =============================================================================
# CLIENT OPERATIONS
# =============================================================================


def create_client(session: Session, name: str, email: str, phone: str = None) -> Client:
    client = Client(name=name, email=email, phone=phone)
    session.add(client)
    session.flush()  # get client_id before commit
    logger.info("Created client: %s (%s)", name, email)
    return client


def get_client_by_email(session: Session, email: str) -> Optional[Client]:
    return session.query(Client).filter_by(email=email).first()


def get_all_clients(session: Session) -> list[Client]:
    return session.query(Client).order_by(Client.created_at).all()


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
    portfolio = Portfolio(
        client_id=client_id, name=name, risk_level=risk_level, start_date=start_date
    )
    session.add(portfolio)
    session.flush()
    logger.info("Created portfolio '%s' for client %s", name, client_id)
    return portfolio


def get_portfolios_by_client(session: Session, client_id: UUID) -> list[Portfolio]:
    return session.query(Portfolio).filter_by(client_id=client_id).all()


# =============================================================================
# ASSET OPERATIONS
# =============================================================================


def upsert_asset(session: Session, symbol: str, name: str, asset_type: str) -> Asset:
    """Insert asset if it doesn't exist; return existing record otherwise."""
    asset = session.query(Asset).filter_by(symbol=symbol).first()
    if asset is None:
        asset = Asset(symbol=symbol, name=name, type=asset_type)
        session.add(asset)
        session.flush()
        logger.info("Inserted new asset: %s (%s)", symbol, asset_type)
    return asset


def get_asset_by_symbol(session: Session, symbol: str) -> Optional[Asset]:
    return session.query(Asset).filter_by(symbol=symbol).first()


# =============================================================================
# PORTFOLIO HOLDINGS OPERATIONS
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
        logger.info(
            "Updated holding for asset %s in portfolio %s", asset_id, portfolio_id
        )
    else:
        holding = PortfolioAsset(
            portfolio_id=portfolio_id,
            asset_id=asset_id,
            quantity=quantity,
            avg_price=avg_price,
        )
        session.add(holding)
        session.flush()
        logger.info(
            "Inserted holding for asset %s in portfolio %s", asset_id, portfolio_id
        )
    return holding


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


def get_transactions(session: Session, portfolio_id: UUID) -> pd.DataFrame:
    """Return all transactions for a portfolio as a DataFrame."""
    rows = (
        session.query(Transaction)
        .filter_by(portfolio_id=portfolio_id)
        .order_by(Transaction.transaction_date)
        .all()
    )
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


# =============================================================================
# ASSET PRICE OPERATIONS
# =============================================================================


def bulk_insert_prices(session: Session, asset_id: UUID, price_df: pd.DataFrame) -> int:
    """
    Insert full OHLCV + indicators into asset_prices.
    Skips existing (asset_id, price_date).
    Returns number of inserted rows.
    """

    # Normalize dates once (faster + cleaner)
    price_df = price_df.copy()
    price_df["price_date"] = pd.to_datetime(price_df["Date"]).dt.date

    # Load existing dates
    existing = {
        r[0]
        for r in session.query(AssetPrice.price_date).filter(
            AssetPrice.asset_id == asset_id
        )
    }

    new_records = []

    for _, row in price_df.iterrows():
        if row["price_date"] in existing:
            continue

        new_records.append(
            AssetPrice(
                asset_id=asset_id,
                # OHLCV
                open=Decimal(str(row["Open"])) if pd.notna(row.get("Open")) else None,
                high=Decimal(str(row["High"])) if pd.notna(row.get("High")) else None,
                low=Decimal(str(row["Low"])) if pd.notna(row.get("Low")) else None,
                close=(
                    Decimal(str(row["Close"])) if pd.notna(row.get("Close")) else None
                ),
                volume=(
                    Decimal(str(row["Volume"])) if pd.notna(row.get("Volume")) else None
                ),
                # Returns
                return_=row.get("return"),
                log_return=row.get("log_return"),
                cum_return=row.get("cum_return"),
                # Volatility
                vol_20=row.get("vol_20"),
                vol_60=row.get("vol_60"),
                # Indicators
                rsi_14=row.get("rsi_14"),
                macd=row.get("macd"),
                macd_signal=row.get("macd_signal"),
                macd_hist=row.get("macd_hist"),
                # Risk metrics
                rolling_max=row.get("rolling_max"),
                drawdown=row.get("drawdown"),
                # Date
                price_date=row["price_date"],
            )
        )

    if new_records:
        session.bulk_save_objects(new_records)
        session.flush()

    logger.info(
        "Inserted %d new price records for asset %s",
        len(new_records),
        asset_id,
    )

    return len(new_records)


def get_price_history(
    session: Session, symbol: str, start: str = None, end: str = None
) -> pd.DataFrame:
    """
    Fetch historical prices for a symbol as a DataFrame.
    Optional start/end filters as 'YYYY-MM-DD' strings.
    """
    asset = get_asset_by_symbol(session, symbol)
    if asset is None:
        logger.warning("Asset '%s' not found in database.", symbol)
        return pd.DataFrame()

    query = session.query(AssetPrice).filter_by(asset_id=asset.asset_id)

    if start:
        query = query.filter(AssetPrice.price_date >= start)
    if end:
        query = query.filter(AssetPrice.price_date <= end)

    rows = query.order_by(AssetPrice.price_date).all()

    return (
        pd.DataFrame(
            [{"price_date": r.price_date, "price": float(r.price)} for r in rows]
        ).set_index("price_date")
        if rows
        else pd.DataFrame()
    )


# =============================================================================
# QUICK-START HELPER
# =============================================================================


def build_db(config_path: str = "config/settings.yaml"):
    """
    Convenience function that wires everything up in one call.

    Returns:
        engine, SessionFactory

    Usage:
        engine, SessionFactory = build_db()
        with get_session(SessionFactory) as session:
            clients = get_all_clients(session)
    """
    engine = get_engine(config_path)
    init_db(engine)
    session_factory = get_session_factory(engine)
    return engine, session_factory


# =============================================================================
# Portfolio Equity Curves
# =============================================================================
# =============================================================================
# Portfolio Equity Curves
# =============================================================================


class PortfolioEquityCurve(Base):
    __tablename__ = "portfolio_equity_curves"

    curve_id = Column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    portfolio_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("portfolios.portfolio_id", ondelete="CASCADE"),
        nullable=False,
    )

    date = Column(Date, nullable=False)
    total_value = Column(Numeric(20, 6), nullable=False)

    created_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    portfolio = relationship("Portfolio", back_populates="equity_curves")

    __table_args__ = (
        Index(
            "idx_portfolio_equity_curves_portfolio_date",
            "portfolio_id",
            "date",
        ),
        UniqueConstraint(
            "portfolio_id",
            "date",
            name="uq_portfolio_date",
        ),
    )

    def __repr__(self):
        return (
            f"<PortfolioEquityCurve("
            f"portfolio_id={self.portfolio_id!r}, "
            f"date={self.date!r}, "
            f"total_value={self.total_value!r})>"
        )


# =============================================================================
# SAVE EQUITY CURVE (FIXED + SAFE)
# =============================================================================


def save_equity_curve(session: Session, portfolio_id, df: pd.DataFrame):
    """
    Save equity curve into DB.

    Expected df columns:
        - Date
        - total_value
    """

    if df is None or df.empty:
        return 0

    # Load existing dates (prevents duplicates)
    existing_dates = {
        r[0]
        for r in session.query(PortfolioEquityCurve.date)
        .filter(PortfolioEquityCurve.portfolio_id == portfolio_id)
        .all()
    }

    records = []
    inserted = 0

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
        inserted += 1

    if records:
        session.bulk_save_objects(records)
        session.flush()

    logger.info(
        "Inserted %d equity curve rows for portfolio %s",
        inserted,
        portfolio_id,
    )

    return inserted
