"""
src/data/models/__init__.py

Imports all models so SQLAlchemy metadata is fully populated
before engine.py calls Base.metadata.create_all().
"""

from data.models.client import Client
from data.models.portfolio import Portfolio, PortfolioAsset, PortfolioEquityCurve, PortfolioMetrics, PortfolioAnalytics
from data.models.asset import Asset, AssetPrice
from data.models.transaction import Transaction
from data.models.optimized import OptimizedPortfolio, OptimizedPortfolioAsset, OptimizedPortfolioMetrics

__all__ = [
    "Client",
    "Portfolio",
    "PortfolioAsset",
    "PortfolioEquityCurve",
    "PortfolioMetrics",
    "PortfolioAnalytics",  
    "Asset",
    "AssetPrice",
    "Transaction",
    "OptimizedPortfolio",
    "OptimizedPortfolioAsset",
    "OptimizedPortfolioMetrics",
]