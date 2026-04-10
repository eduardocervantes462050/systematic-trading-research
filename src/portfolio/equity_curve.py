import pandas as pd
from data.database import PortfolioAsset, AssetPrice


def calculate_portfolio_equity_curve(session, portfolio_id):
    # 1. Get holdings
    holdings = session.query(PortfolioAsset).filter_by(portfolio_id=portfolio_id).all()

    if not holdings:
        return pd.DataFrame()

    asset_ids = [h.asset_id for h in holdings]

    # 2. Get price history
    prices = (
        session.query(AssetPrice)
        .filter(AssetPrice.asset_id.in_(asset_ids))
        .order_by(AssetPrice.price_date)
        .all()
    )

    if not prices:
        return pd.DataFrame()

    # 3. Build DataFrame
    df_prices = pd.DataFrame(
        [
            {"date": p.price_date, "asset_id": p.asset_id, "close": float(p.close)}
            for p in prices
        ]
    )

    pivot = df_prices.pivot(index="date", columns="asset_id", values="close")

    # 4. Holdings vector
    holdings_dict = {h.asset_id: float(h.quantity) for h in holdings}

    # 5. Portfolio value (vectorized)
    portfolio_values = pivot.mul(pd.Series(holdings_dict)).sum(axis=1)

    # 6. Output
    return portfolio_values.reset_index().rename(
        columns={"date": "Date", 0: "total_value"}
    )
