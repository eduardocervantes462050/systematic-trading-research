from __future__ import annotations

import json
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from data.models import PortfolioAnalytics, PortfolioAsset
from data.models.asset import Asset

from services.market_data_service import load_portfolio_price_matrix
from analytics.expected_returns import compute_expected_returns
from analytics.covariance import compute_covariance_matrix


# =============================================================================
# LOAD ASSETS (LOCAL - NO CIRCULAR IMPORT)
# =============================================================================

def _load_portfolio_assets(session: Session, portfolio_id: str) -> list[str]:
    """
    Internal helper to avoid circular imports.
    """

    rows = (
        session.query(PortfolioAsset, Asset)
        .join(Asset, PortfolioAsset.asset_id == Asset.asset_id)
        .filter(PortfolioAsset.portfolio_id == portfolio_id)
        .all()
    )

    return [asset.symbol for _, asset in rows]


# =============================================================================
# CACHE HELPERS
# =============================================================================

def _get_cached_analytics(
    session,
    portfolio_id: str,
    analytics_type: str,
):
    return (
        session.query(PortfolioAnalytics)
        .filter(
            PortfolioAnalytics.portfolio_id == portfolio_id,
            PortfolioAnalytics.analytics_type == analytics_type,
        )
        .first()
    )


def _save_analytics(
    session,
    portfolio_id: str,
    analytics_type: str,
    value,
):
    # pandas Series -> dict
    if isinstance(value, pd.Series):
        value = value.to_dict()

    # pandas DataFrame -> nested dict
    elif isinstance(value, pd.DataFrame):
        value = value.to_dict()

    # numpy arrays -> list
    elif isinstance(value, (np.ndarray, np.matrix)):
        value = value.tolist()

    session.add(
        PortfolioAnalytics(
            portfolio_id=portfolio_id,
            analytics_type=analytics_type,
            value=value,
        )
    )

    session.commit()


def _load_cached_value(record):
    if record is None:
        return None

    return record.value


# =============================================================================
# MAIN PIPELINE
# =============================================================================

def portfolio_analytics(
    session: Session,
    portfolio_id: str,
    use_cache: bool = True,
):
    """
    portfolio_id → assets → prices → mu + cov
    """

    # --------------------------------------------------
    # 1. CACHE CHECK
    # --------------------------------------------------
    if use_cache:
        mu_record = _get_cached_analytics(session, portfolio_id, "EXPECTED_RETURNS")
        cov_record = _get_cached_analytics(session, portfolio_id, "COVARIANCE")

        if mu_record and cov_record:
            return (
                _load_cached_value(mu_record),
                _load_cached_value(cov_record),
            )

    # --------------------------------------------------
    # 2. LOAD ASSETS (FIXED)
    # --------------------------------------------------
    assets = _load_portfolio_assets(session, portfolio_id)

    if not assets:
        raise ValueError(f"No assets found for portfolio {portfolio_id}")

    # --------------------------------------------------
    # 3. LOAD PRICES
    # --------------------------------------------------
    price_df = load_portfolio_price_matrix(
        session=session,
        assets=assets,
    )

    if price_df is None or price_df.empty:
        raise ValueError(f"No price data for portfolio {portfolio_id}")

    # --------------------------------------------------
    # 4. COMPUTE ANALYTICS
    # --------------------------------------------------
    mu = compute_expected_returns(price_df)
    cov = compute_covariance_matrix(price_df)

    # --------------------------------------------------
    # 5. CACHE RESULTS
    # --------------------------------------------------
    _save_analytics(session, portfolio_id, "EXPECTED_RETURNS", mu)
    _save_analytics(session, portfolio_id, "COVARIANCE", cov)

    return mu, cov