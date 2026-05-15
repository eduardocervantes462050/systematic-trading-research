"""
src/data/models/asset.py

Asset and AssetPrice ORM models.
"""

from decimal import Decimal
from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from data.base import Base


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