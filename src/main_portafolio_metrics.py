from data.database import build_db, get_session
from portfolio.metrics.cagr import calculate_and_store_cagr
from portfolio.metrics.volatility import calculate_and_store_volatility
from portfolio.metrics.max_drawdown import calculate_and_store_max_drawdown
from portfolio.metrics.sharpe import calculate_and_store_sharpe

engine, SessionFactory = build_db()

with get_session(SessionFactory) as session:
    # CAGR
    cagr_results = calculate_and_store_cagr(session)
    for r in cagr_results:
        print(f"{r['portfolio']} → CAGR: {r['cagr']:.2%}")

    # Volatility
    vol_results = calculate_and_store_volatility(session)
    for r in vol_results:
        print(f"{r['portfolio']} → Volatility: {r['volatility']:.2%}")

    # Max Drawdown
    dd_results = calculate_and_store_max_drawdown(session)
    for r in dd_results:
        print(f"{r['portfolio']} → Max Drawdown: {r['max_drawdown']:.2%}")

    # Sharpe
    sharpe_results = calculate_and_store_sharpe(session)
    for r in sharpe_results:
        print(f"{r['portfolio']} → Sharpe: {r['sharpe']:.2f}")
