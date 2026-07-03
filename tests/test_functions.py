from analytics.expected_returns import compute_expected_returns
from data.engine import build_db, get_session
from data.repositories.portfolio_repo import get_holdings
from services.market_data_service import load_portfolio_price_matrix

engine, SessionFactory = build_db()

portfolio_id = "02eee7b7-514e-4968-84ed-a2ab868e4b54"

with get_session(SessionFactory) as session:
    assets = get_holdings(session, portfolio_id)
    print("Loaded:", assets)