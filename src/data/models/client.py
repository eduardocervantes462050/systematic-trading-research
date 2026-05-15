"""
src/data/models/client.py

Client ORM model.
"""

from sqlalchemy import (
    Column,
    DateTime,
    Index,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from data.base import Base


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