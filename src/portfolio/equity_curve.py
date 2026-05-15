import pandas as pd
from data.models import PortfolioAsset, AssetPrice, Portfolio


def calculate_portfolio_equity_curve(session, portfolio_id, start_date=None):

    # 1. Get portfolio
    portfolio = session.query(Portfolio).filter_by(portfolio_id=portfolio_id).first()
    if not portfolio:
        return pd.DataFrame()

    # 2. If no start_date passed → fallback to portfolio.start_date
    if start_date is None:
        start_date = portfolio.start_date

    # 3. Get holdings
    holdings = session.query(PortfolioAsset).filter_by(portfolio_id=portfolio_id).all()
    if not holdings:
        return pd.DataFrame()

    asset_ids = [h.asset_id for h in holdings]

    # 4. Get price history filtered by start_date
    prices = (
        session.query(AssetPrice)
        .filter(AssetPrice.asset_id.in_(asset_ids), AssetPrice.price_date >= start_date)
        .order_by(AssetPrice.price_date)
        .all()
    )

    if not prices:
        return pd.DataFrame()

    # 5. Build DataFrame
    df_prices = pd.DataFrame(
        [
            {"date": p.price_date, "asset_id": p.asset_id, "close": float(p.close)}
            for p in prices
        ]
    )

    pivot = df_prices.pivot(index="date", columns="asset_id", values="close")

    # 6. Holdings vector
    holdings_dict = {h.asset_id: float(h.quantity) for h in holdings}

    # 7. Portfolio value
    portfolio_values = pivot.mul(pd.Series(holdings_dict)).sum(axis=1)

    # 8. Output
    result = portfolio_values.reset_index()
    result.columns = ["Date", "total_value"]

    return result
