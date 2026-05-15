"""
src/data/models/optimized.py

OptimizedPortfolio, OptimizedPortfolioAsset, and OptimizedPortfolioMetrics ORM models.
"""

from sqlalchemy import (
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


class OptimizedPortfolio(Base):
    __tablename__ = "optimized_portfolios"

    optimized_portfolio_id = Column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    portfolio_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("portfolios.portfolio_id", ondelete="CASCADE"),
        nullable=False,
    )
    name = Column(String(100), nullable=False)
    optimization_method = Column(
        String(50),
        nullable=False,
    )  # e.g. "equal_weight", "max_sharpe", "min_variance", "risk_parity"
    target_risk_level = Column(
        String(20),
        nullable=True,
    )  # optional: low / medium / high
    expected_return = Column(Numeric(10, 6), nullable=True)
    expected_volatility = Column(Numeric(10, 6), nullable=True)
    sharpe_ratio = Column(Numeric(10, 6), nullable=True)
    created_at = Column(
        DateTime,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    portfolio = relationship("Portfolio")
    assets = relationship(
        "OptimizedPortfolioAsset",
        back_populates="optimized_portfolio",
        cascade="all, delete-orphan",
    )
    metrics = relationship(
        "OptimizedPortfolioMetrics",
        back_populates="optimized_portfolio",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_optimized_portfolio_portfolio_id", "portfolio_id"),
    )

    def __repr__(self):
        return (
            f"<OptimizedPortfolio("
            f"name={self.name!r}, "
            f"method={self.optimization_method!r})>"
        )


class OptimizedPortfolioAsset(Base):
    __tablename__ = "optimized_portfolio_assets"

    id = Column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    optimized_portfolio_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("optimized_portfolios.optimized_portfolio_id", ondelete="CASCADE"),
        nullable=False,
    )
    asset_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("assets.asset_id", ondelete="CASCADE"),
        nullable=False,
    )
    weight = Column(Numeric(8, 6), nullable=False)  # e.g. 0.25 = 25%

    optimized_portfolio = relationship(
        "OptimizedPortfolio",
        back_populates="assets",
    )
    asset = relationship("Asset")

    __table_args__ = (
        UniqueConstraint(
            "optimized_portfolio_id",
            "asset_id",
            name="uq_optimized_portfolio_asset",
        ),
        Index("idx_opt_portfolio_assets_portfolio", "optimized_portfolio_id"),
        Index("idx_opt_portfolio_assets_asset", "asset_id"),
    )

    def __repr__(self):
        return f"<OptimizedPortfolioAsset(weight={self.weight})>"


class OptimizedPortfolioMetrics(Base):
    __tablename__ = "optimized_portfolio_metrics"

    metric_id = Column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    optimized_portfolio_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("optimized_portfolios.optimized_portfolio_id", ondelete="CASCADE"),
        nullable=False,
    )
    metric_type = Column(
        String,
        nullable=False,
    )  # SHARPE, EXPECTED_RETURN, VOLATILITY, MAX_DRAWDOWN, SORTINO
    value = Column(Numeric(20, 8), nullable=False)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    extra_data = Column(JSON, nullable=True)  # e.g. {"risk_free_rate": 0.04}
    created_at = Column(
        DateTime,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    optimized_portfolio = relationship(
        "OptimizedPortfolio",
        back_populates="metrics",
    )

    __table_args__ = (
        Index("idx_opt_portfolio_metrics_portfolio", "optimized_portfolio_id"),
        Index("idx_opt_portfolio_metrics_type", "metric_type"),
        UniqueConstraint(
            "optimized_portfolio_id",
            "metric_type",
            "start_date",
            "end_date",
            name="uq_opt_portfolio_metric_window",
        ),
    )

    def __repr__(self):
        return (
            f"<OptimizedPortfolioMetrics("
            f"type={self.metric_type!r}, "
            f"value={self.value!r})>"
        )