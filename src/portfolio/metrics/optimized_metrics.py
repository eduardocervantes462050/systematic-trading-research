"""
src/portfolio/metrics/optimized_metrics.py

Compute and persist CAGR, Volatility, Max Drawdown, and Sharpe
for all optimized portfolios in the DB.

Reuses the pure-math functions from the existing metrics modules
and persists via save_optimized_metrics → optimized_portfolio_metrics table.
"""

import logging

from sqlalchemy.orm import Session

from data.models.optimized import OptimizedPortfolio
from data.repositories.optimized_repo import save_optimized_metrics
from portfolio.optimized_equity_curve import calculate_optimized_equity_curve

# reuse pure math — no duplication
from portfolio.metrics.cagr import calculate_cagr
from portfolio.metrics.volatility import calculate_volatility
from portfolio.metrics.max_drawdown import calculate_max_drawdown
from portfolio.metrics.sharpe import calculate_sharpe, RISK_FREE_RATE

logger = logging.getLogger(__name__)


# =============================================================================
# HELPERS
# =============================================================================

def _get_all_optimized_portfolios(session: Session) -> list[OptimizedPortfolio]:
    return (
        session.query(OptimizedPortfolio)
        .order_by(OptimizedPortfolio.created_at)
        .all()
    )


def _build_curve(session, opt):
    """Build equity curve for a single optimized portfolio."""
    return calculate_optimized_equity_curve(
        session=session,
        optimized_portfolio_id=opt.optimized_portfolio_id,
    )


def _label(opt) -> str:
    return f"{opt.name} ({opt.optimization_method})"


# =============================================================================
# INDIVIDUAL METRIC FUNCTIONS
# =============================================================================

def calculate_and_store_optimized_cagr(session: Session) -> list[dict]:
    """Compute and persist CAGR for all optimized portfolios."""
    results = []
    for opt in _get_all_optimized_portfolios(session):
        df = _build_curve(session, opt)
        result = calculate_cagr(df)
        if result is None:
            logger.warning("Skipping CAGR for %s — insufficient data", _label(opt))
            continue
        cagr, start_date, end_date = result
        save_optimized_metrics(
            session,
            optimized_portfolio_id=opt.optimized_portfolio_id,
            metrics={"CAGR": cagr},
            start_date=start_date.date(),
            end_date=end_date.date(),
        )
        results.append({"portfolio": _label(opt), "cagr": cagr})
        logger.info("CAGR for %s: %.4f", _label(opt), cagr)
    return results


def calculate_and_store_optimized_volatility(session: Session) -> list[dict]:
    """Compute and persist annualized volatility for all optimized portfolios."""
    results = []
    for opt in _get_all_optimized_portfolios(session):
        df = _build_curve(session, opt)
        result = calculate_volatility(df)
        if result is None:
            logger.warning("Skipping Volatility for %s — insufficient data", _label(opt))
            continue
        volatility, start_date, end_date = result
        save_optimized_metrics(
            session,
            optimized_portfolio_id=opt.optimized_portfolio_id,
            metrics={"VOLATILITY": volatility},
            start_date=start_date.date(),
            end_date=end_date.date(),
        )
        results.append({"portfolio": _label(opt), "volatility": volatility})
        logger.info("Volatility for %s: %.4f", _label(opt), volatility)
    return results


def calculate_and_store_optimized_max_drawdown(session: Session) -> list[dict]:
    """Compute and persist max drawdown for all optimized portfolios."""
    results = []
    for opt in _get_all_optimized_portfolios(session):
        df = _build_curve(session, opt)
        result = calculate_max_drawdown(df)
        if result is None:
            logger.warning("Skipping Max Drawdown for %s — insufficient data", _label(opt))
            continue
        max_drawdown, start_date, end_date = result
        save_optimized_metrics(
            session,
            optimized_portfolio_id=opt.optimized_portfolio_id,
            metrics={"MAX_DRAWDOWN": max_drawdown},
            start_date=start_date.date(),
            end_date=end_date.date(),
        )
        results.append({"portfolio": _label(opt), "max_drawdown": max_drawdown})
        logger.info("Max Drawdown for %s: %.4f", _label(opt), max_drawdown)
    return results


def calculate_and_store_optimized_sharpe(
    session: Session,
    risk_free_rate: float = RISK_FREE_RATE,
) -> list[dict]:
    """Compute and persist Sharpe ratio for all optimized portfolios."""
    results = []
    for opt in _get_all_optimized_portfolios(session):
        df = _build_curve(session, opt)
        result = calculate_sharpe(df, risk_free_rate)
        if result is None:
            logger.warning("Skipping Sharpe for %s — insufficient data", _label(opt))
            continue
        sharpe, start_date, end_date = result
        save_optimized_metrics(
            session,
            optimized_portfolio_id=opt.optimized_portfolio_id,
            metrics={"SHARPE": sharpe},
            start_date=start_date.date(),
            end_date=end_date.date(),
            extra_data={"risk_free_rate": risk_free_rate},
        )
        results.append({"portfolio": _label(opt), "sharpe": sharpe})
        logger.info("Sharpe for %s: %.4f", _label(opt), sharpe)
    return results


# =============================================================================
# RUN ALL METRICS AT ONCE
# =============================================================================

def calculate_and_store_all_optimized_metrics(
    session: Session,
    risk_free_rate: float = RISK_FREE_RATE,
) -> dict:
    """
    Compute and persist all metrics for all optimized portfolios.

    Returns
    -------
    dict with keys: cagr, volatility, max_drawdown, sharpe
    """
    return {
        "cagr":         calculate_and_store_optimized_cagr(session),
        "volatility":   calculate_and_store_optimized_volatility(session),
        "max_drawdown": calculate_and_store_optimized_max_drawdown(session),
        "sharpe":       calculate_and_store_optimized_sharpe(session, risk_free_rate),
    }