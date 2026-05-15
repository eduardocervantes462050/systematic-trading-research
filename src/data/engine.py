"""
src/data/engine.py

Database engine, session factory, and connection management.
"""

import logging
import os
import sys
from contextlib import contextmanager

import yaml
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

logger = logging.getLogger(__name__)


# =============================================================================
# ENGINE
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
        echo=db.get("echo", False),
    )
    logger.info(
        "Database engine created for %s:%s/%s", db["host"], db["port"], db["name"]
    )
    return engine


# =============================================================================
# SESSION FACTORY
# =============================================================================


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
# SCHEMA INITIALISATION
# =============================================================================


def _ensure_src_on_path() -> None:
    """
    Ensure src/ is on sys.path so data.models and data.base
    resolve correctly regardless of where the script is run from.

    src/data/engine.py is two levels deep inside src/, so:
        __file__ → src/data/engine.py
        parent   → src/data/
        parent   → src/             ← this is what we need on sys.path
    """
    src_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    )
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
        logger.debug("Added to sys.path: %s", src_path)


def init_db(engine) -> None:
    """
    Enable the pgcrypto extension and create all tables if they do not exist.
    Safe to call on every startup — uses CREATE IF NOT EXISTS semantics.

    NOTE: All models must be imported before this is called so SQLAlchemy's
    metadata knows about every table. models/__init__.py handles this.
    """
    _ensure_src_on_path()

    import data.models  # noqa: F401  — registers all models with Base.metadata
    from data.base import Base

    with engine.begin() as conn:
        conn.execute(text('CREATE EXTENSION IF NOT EXISTS "pgcrypto"'))
        logger.info("pgcrypto extension ensured.")

    Base.metadata.create_all(engine)
    logger.info("All tables created (or already exist).")


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