"""
src/services/optimization_service.py

Portfolio Optimization Service

Responsibilities
----------------
1. Load portfolio analytics
2. Run optimization strategy
3. Persist optimized portfolio
4. Persist optimized weights
"""

import logging

import pandas as pd
from sqlalchemy.orm import Session

from data.repositories import (
    upsert_optimized_portfolio,
    save_weights,
)

from portfolio.weights.base import BaseWeightGenerator

from services.analytics_service import (
    portfolio_analytics,
)

logger = logging.getLogger(__name__)


# =============================================================================
# STRATEGY EXECUTION
# =============================================================================

def generate_weights(
    strategy,
    expected_returns,
    cov_matrix,
):
    assets = list(expected_returns.index)

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
    analytics (cached or computed)
        ↓
    optimization strategy
        ↓
    optimized weights
        ↓
    database persistence
    """

    logger.info(
        "Starting optimization for portfolio %s",
        portfolio_id,
    )

    # -------------------------------------------------------------------------
    # 1. LOAD ANALYTICS
    # -------------------------------------------------------------------------

    expected_returns, cov_matrix = portfolio_analytics(
        session=session,
        portfolio_id=portfolio_id,
        use_cache=True,
    )

    # -------------------------------------------------------------------------
    # 2. REBUILD PANDAS OBJECTS IF LOADED FROM CACHE
    # -------------------------------------------------------------------------

    if isinstance(expected_returns, dict):
        expected_returns = pd.Series(expected_returns)

    if isinstance(cov_matrix, dict):
        cov_matrix = pd.DataFrame(cov_matrix)

    logger.info(
        "Portfolio analytics loaded successfully."
    )

    # -------------------------------------------------------------------------
    # 3. EXECUTE STRATEGY
    # -------------------------------------------------------------------------

    weights = generate_weights(
        strategy=strategy,
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