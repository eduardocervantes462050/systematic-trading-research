"""
src/data/models/portfolio.py

Portfolio, PortfolioAsset, PortfolioEquityCurve, and PortfolioMetrics ORM models.
"""

from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    JSON,
    Numeric,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from data.base import Base


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
    metrics = relationship(
        "PortfolioMetrics", back_populates="portfolio", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "risk_level IN ('low', 'medium', 'high')", name="ck_portfolio_risk_level"
        ),
        Index("idx_portfolios_client_id", "client_id"),
    )

    def __repr__(self):
        return f"<Portfolio(name={self.name!r}, risk_level={self.risk_level!r})>"


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
        PG_UUID(as_uuid=True),
        ForeignKey("assets.asset_id"),
        nullable=False,
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


class PortfolioMetrics(Base):
    __tablename__ = "portfolio_metrics"

    metric_id = Column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    portfolio_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("portfolios.portfolio_id", ondelete="CASCADE"),
        nullable=False,
    )
    metric_type = Column(String, nullable=False)  # CAGR, VOLATILITY, SHARPE, DRAWDOWN
    value = Column(Numeric(20, 8), nullable=False)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    extra_data = Column(JSON, nullable=True)
    created_at = Column(
        DateTime,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    portfolio = relationship("Portfolio", back_populates="metrics")

    __table_args__ = (
        Index("idx_portfolio_metrics_portfolio", "portfolio_id"),
        Index("idx_portfolio_metrics_type", "metric_type"),
        UniqueConstraint(
            "portfolio_id",
            "metric_type",
            "start_date",
            "end_date",
            name="uq_portfolio_metric_window",
        ),
    )

    def __repr__(self):
        return (
            f"<PortfolioMetrics("
            f"type={self.metric_type!r}, "
            f"value={self.value!r})>"
        )


class PortfolioAnalytics(Base):
    __tablename__ = "portfolio_analytics"

    analytics_id = Column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    portfolio_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("portfolios.portfolio_id", ondelete="CASCADE"),
        nullable=False,
    )

    analytics_type = Column(
        String(50),
        nullable=False,
    )

    value = Column(
        JSON,
        nullable=False,
    )

    created_at = Column(
        DateTime,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    portfolio = relationship("Portfolio")

    __table_args__ = (
        Index(
            "idx_portfolio_analytics_portfolio",
            "portfolio_id",
        ),
    )
    