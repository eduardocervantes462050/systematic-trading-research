"""
Run metrics for all optimized portfolios.
Usage:
    python -m portfolio.metrics.run_optimized_metrics
"""
from data.engine import build_db, get_session
from portfolio.metrics.optimized_metrics import (
    calculate_and_store_optimized_cagr,
    calculate_and_store_optimized_volatility,
    calculate_and_store_optimized_max_drawdown,
    calculate_and_store_optimized_sharpe,
)

engine, SessionFactory = build_db()

with get_session(SessionFactory) as session:

    print("\n── CAGR ──────────────────────────────────")
    for r in calculate_and_store_optimized_cagr(session):
        print(f"  {r['portfolio']} → {r['cagr']:.2%}")

    print("\n── Volatility ────────────────────────────")
    for r in calculate_and_store_optimized_volatility(session):
        print(f"  {r['portfolio']} → {r['volatility']:.2%}")

    print("\n── Max Drawdown ──────────────────────────")
    for r in calculate_and_store_optimized_max_drawdown(session):
        print(f"  {r['portfolio']} → {r['max_drawdown']:.2%}")

    print("\n── Sharpe Ratio ──────────────────────────")
    for r in calculate_and_store_optimized_sharpe(session):
        print(f"  {r['portfolio']} → {r['sharpe']:.2f}")