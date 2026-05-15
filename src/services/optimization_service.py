"""
src/services/optimization_service.py

Portfolio optimization orchestration layer.

Responsibilities
----------------
1. Load portfolio assets from DB
2. Generate portfolio analytics
    - expected returns
    - covariance matrix
3. Execute optimization strategy
4. Persist optimized portfolio
5. Persist weights
"""

import logging

from sqlalchemy.orm import Session

from data.models import (
    PortfolioAsset,
    Asset,
)

from data.repositories import (
    upsert_optimized_portfolio,
    save_weights,
)

from portfolio.weights.base import (
    BaseWeightGenerator,
)

from services.analytics_service import (
    generate_portfolio_analytics,
)

logger = logging.getLogger(__name__)


# =============================================================================
# PORTFOLIO ASSET LOADING
# =============================================================================

def load_portfolio_assets(
    session: Session,
    portfolio_id: str,
) -> list[str]:
    """
    Load asset symbols belonging to a portfolio.

    Parameters
    ----------
    session : Session
        SQLAlchemy DB session

    portfolio_id : str
        Portfolio UUID

    Returns
    -------
    list[str]
        Example:
            ["AAPL", "MSFT", "TLT"]
    """

    rows = (
        session.query(PortfolioAsset, Asset)
        .join(
            Asset,
            PortfolioAsset.asset_id == Asset.asset_id,
        )
        .filter(
            PortfolioAsset.portfolio_id == portfolio_id
        )
        .all()
    )

    assets = [
        asset.symbol
        for _, asset in rows
    ]

    if not assets:
        logger.warning(
            "No assets found for portfolio %s",
            portfolio_id,
        )

    return assets


# =============================================================================
# STRATEGY EXECUTION
# =============================================================================

def generate_weights(
    strategy: BaseWeightGenerator,
    assets: list[str],
    expected_returns,
    cov_matrix,
) -> dict[str, float]:
    """
    Execute optimization strategy.

    Parameters
    ----------
    strategy : BaseWeightGenerator
        Portfolio weighting strategy

    assets : list[str]
        Portfolio assets

    expected_returns :
        Expected returns vector (mu)

    cov_matrix :
        Covariance matrix (Sigma)

    Returns
    -------
    dict[str, float]
        Portfolio weights
    """

    return strategy.generate(
        returns=expected_returns,
        cov_matrix=cov_matrix,
        assets=assets,
    )


# =============================================================================
# MAIN OPTIMIZATION PIPELINE
# =============================================================================

def run_optimization(
    session: Session,
    portfolio_id: str,
    strategy: BaseWeightGenerator,
    method_name: str,
) -> dict[str, float]:
    """
    Full optimization pipeline.

    Flow
    ----
    portfolio
        ↓
    assets
        ↓
    analytics
        ↓
    strategy
        ↓
    weights
        ↓
    database persistence

    Parameters
    ----------
    session : Session
        SQLAlchemy session

    portfolio_id : str
        Portfolio UUID

    strategy : BaseWeightGenerator
        Optimization strategy

    method_name : str
        Strategy label persisted in DB

    Returns
    -------
    dict[str, float]
        Optimized weights
    """

    logger.info(
        "Starting optimization for portfolio %s",
        portfolio_id,
    )

    # -------------------------------------------------------------------------
    # 1. LOAD PORTFOLIO ASSETS
    # -------------------------------------------------------------------------

    assets = load_portfolio_assets(
        session=session,
        portfolio_id=portfolio_id,
    )

    if not assets:
        raise ValueError(
            f"No assets found for portfolio {portfolio_id}"
        )

    logger.info(
        "Loaded %s assets",
        len(assets),
    )

    # -------------------------------------------------------------------------
    # 2. GENERATE PORTFOLIO ANALYTICS
    # -------------------------------------------------------------------------

    expected_returns, cov_matrix = (
        generate_portfolio_analytics(
            session=session,
            assets=assets,
        )
    )

    logger.info(
        "Portfolio analytics generated successfully."
    )

    # -------------------------------------------------------------------------
    # 3. EXECUTE STRATEGY
    # -------------------------------------------------------------------------

    weights = generate_weights(
        strategy=strategy,
        assets=assets,
        expected_returns=expected_returns,
        cov_matrix=cov_matrix,
    )

    logger.info(
        "Optimization strategy executed successfully."
    )

    # -------------------------------------------------------------------------
    # 4. UPSERT OPTIMIZED PORTFOLIO
    # -------------------------------------------------------------------------

    optimized_portfolio = (
        upsert_optimized_portfolio(
            session=session,
            portfolio_id=portfolio_id,
            method=method_name,
        )
    )

    logger.info(
        "Optimized portfolio upserted."
    )

    # -------------------------------------------------------------------------
    # 5. SAVE WEIGHTS
    # -------------------------------------------------------------------------

    save_weights(
        session=session,
        optimized_portfolio_id=(
            optimized_portfolio.optimized_portfolio_id
        ),
        weights=weights,
    )

    logger.info(
        "Weights persisted successfully."
    )

    logger.info(
        "Optimization completed for portfolio %s",
        portfolio_id,
    )

    return weights