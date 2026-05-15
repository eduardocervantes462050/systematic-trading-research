from data.engine import build_db, get_session
from data.models import Portfolio
from data.repositories.optimized_repo import get_optimized_portfolio_by_method
from Graphs.plot_equity_curve import plot_multiple_optimized_equity_curves

engine, SessionFactory = build_db()

with get_session(SessionFactory) as session:
    portfolio = session.query(Portfolio).filter_by(name="Global Multi-Asset Growth Portfolio").first()

    methods = ["equal_weight", "max_sharpe", "risk_parity"]
    opts = []
    for m in methods:
        opt = get_optimized_portfolio_by_method(session, portfolio.portfolio_id, m)
        if opt:
            opts.append((opt.optimized_portfolio_id, m.replace("_", " ").title()))

    plot_multiple_optimized_equity_curves(
        session,
        opts,
        title="Strategy Comparison — Global Multi-Asset Growth Portfolio",
        filename="Global_Multi-Asset_strategy_comparison",
    )