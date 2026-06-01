from analytics.expected_returns import compute_expected_returns
from data.engine import build_db, get_session
from services.analytics_service import _load_portfolio_assets
from services.market_data_service import load_portfolio_price_matrix

engine, SessionFactory = build_db()

portfolio_id = "02eee7b7-514e-4968-84ed-a2ab868e4b54"

with get_session(SessionFactory) as session:
    assets = _load_portfolio_assets(session, portfolio_id)

print("Loaded:", assets)
price_df = load_portfolio_price_matrix(
        session=session,
        assets=assets,
    )

if price_df is None or price_df.empty:
        raise ValueError(f"No price data for portfolio {portfolio_id}")

mu = compute_expected_returns(price_df)

print("Expected Returns:", mu)