import logging
from sqlalchemy.orm import Session

from data.database import (
    PortfolioAsset,
    Asset,
    OptimizedPortfolio,
    OptimizedPortfolioAsset,
)

from portfolio.weights.equal_weight import EqualWeight

logger = logging.getLogger(__name__)


# =========================================================
# 1. DATA LOADING
# =========================================================


def load_portfolio_assets(session: Session, portfolio_id: str):
    """
    Fetch asset symbols from a real portfolio in DB.
    """
    rows = (
        session.query(PortfolioAsset, Asset)
        .join(Asset, PortfolioAsset.asset_id == Asset.asset_id)
        .filter(PortfolioAsset.portfolio_id == portfolio_id)
        .all()
    )

    assets = [asset.symbol for _, asset in rows]

    if not assets:
        logger.warning("No assets found for portfolio %s", portfolio_id)

    return assets


# =========================================================
# 2. STRATEGY LAYER
# =========================================================


def generate_equal_weights(assets):
    """
    Calls EqualWeight strategy.
    (Pure math layer — no DB here)
    """
    strategy = EqualWeight()

    weights = strategy.generate(returns=None, cov_matrix=None, assets=assets)

    return weights


# =========================================================
# 3. DATABASE: CREATE OPTIMIZED PORTFOLIO
# =========================================================


def create_optimized_portfolio(session: Session, portfolio_id: str, method: str):
    """
    Creates a new optimized portfolio record.
    """
    opt = OptimizedPortfolio(
        portfolio_id=portfolio_id,
        name=f"{method}_portfolio",
        optimization_method=method,
    )

    session.add(opt)
    session.flush()  # get ID before commit

    logger.info("Created optimized portfolio (%s) for %s", method, portfolio_id)

    return opt


# =========================================================
# 4. DATABASE: SAVE WEIGHTS
# =========================================================


def save_weights(session: Session, optimized_portfolio_id: str, weights: dict):
    """
    Store weights in DB.
    Each asset becomes a row.
    """
    for symbol, weight in weights.items():

        asset = session.query(Asset).filter_by(symbol=symbol).first()

        if not asset:
            logger.warning("Asset not found: %s", symbol)
            continue

        row = OptimizedPortfolioAsset(
            optimized_portfolio_id=optimized_portfolio_id,
            asset_id=asset.asset_id,
            weight=weight,
        )

        session.add(row)

    session.commit()

    logger.info(
        "Saved %d weights for optimized portfolio %s",
        len(weights),
        optimized_portfolio_id,
    )


# =========================================================
# 5. MAIN SERVICE (ORCHESTRATION)
# =========================================================


def run_equal_weight_optimization(session: Session, portfolio_id: str):
    """
    FULL PIPELINE:
    DB → assets → strategy → optimized portfolio → DB
    """

    # 1. Load portfolio assets
    assets = load_portfolio_assets(session, portfolio_id)

    if not assets:
        raise ValueError(f"No assets found for portfolio {portfolio_id}")

    # 2. Generate weights
    weights = generate_equal_weights(assets)

    # 3. Create optimized portfolio
    opt_portfolio = create_optimized_portfolio(
        session, portfolio_id, method="equal_weight"
    )

    # 4. Save weights
    save_weights(session, opt_portfolio.optimized_portfolio_id, weights)

    logger.info("Equal weight optimization completed for %s", portfolio_id)

    return weights
