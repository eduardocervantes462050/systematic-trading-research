"""
src/data/repositories/client_repo.py

Client database operations.
"""

import logging
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from data.models import Client

logger = logging.getLogger(__name__)


# =============================================================================
# CLIENT OPERATIONS
# =============================================================================


def create_client(
    session: Session,
    name: str,
    email: str,
    phone: str = None,
) -> Client:
    """Create and flush a new client record."""
    client = Client(name=name, email=email, phone=phone)
    session.add(client)
    session.flush()
    logger.info("Created client: %s (%s)", name, email)
    return client


def get_client_by_email(session: Session, email: str) -> Optional[Client]:
    """Fetch a single client by email. Returns None if not found."""
    return session.query(Client).filter_by(email=email).first()


def get_client_by_id(session: Session, client_id: UUID) -> Optional[Client]:
    """Fetch a single client by UUID. Returns None if not found."""
    return session.query(Client).filter_by(client_id=client_id).first()


def get_all_clients(session: Session) -> list[Client]:
    """Return all clients ordered by creation date."""
    return session.query(Client).order_by(Client.created_at).all()


def update_client(
    session: Session,
    client_id: UUID,
    name: str = None,
    phone: str = None,
) -> Optional[Client]:
    """
    Update a client's name or phone number.
    Only updates fields that are explicitly passed.
    """
    client = get_client_by_id(session, client_id)
    if not client:
        logger.warning("Client %s not found", client_id)
        return None
    if name is not None:
        client.name = name
    if phone is not None:
        client.phone = phone
    session.flush()
    logger.info("Updated client %s", client_id)
    return client


def delete_client(session: Session, client_id: UUID) -> bool:
    """
    Delete a client by UUID.
    Cascades to portfolios via DB constraint.
    Returns True if deleted, False if not found.
    """
    client = get_client_by_id(session, client_id)
    if not client:
        logger.warning("Client %s not found, nothing deleted", client_id)
        return False
    session.delete(client)
    session.flush()
    logger.info("Deleted client %s", client_id)
    return True