from data.engine import build_db, get_session
from data.models import Portfolio
from data.repositories.optimized_repo import get_optimized_portfolio_by_method
from Graphs.plot_equity_curve import plot_optimized_equity_curve

engine, SessionFactory = build_db()

with get_session(SessionFactory) as session:
    portfolio = session.query(Portfolio).filter_by(name="Global Multi-Asset Growth Portfolio").first()
    
    for method in ["equal_weight", "max_sharpe", "risk_parity"]:
        opt = get_optimized_portfolio_by_method(session, portfolio.portfolio_id, method)
        if not opt:
            print(f"No optimized portfolio found for method: {method}")
            continue
        plot_optimized_equity_curve(
            session,
            opt.optimized_portfolio_id,
            portfolio.name,
            method=method,
        )