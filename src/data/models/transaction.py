"""
src/data/models/transaction.py

Transaction ORM model.
"""

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from data.base import Base


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
        PG_UUID(as_uuid=True),
        ForeignKey("assets.asset_id"),
        nullable=False,
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