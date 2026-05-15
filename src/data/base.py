"""
src/data/base.py

SQLAlchemy declarative base.
All ORM models inherit from Base defined here.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
