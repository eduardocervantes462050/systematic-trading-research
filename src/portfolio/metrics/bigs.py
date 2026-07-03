import pandas as pd
from sqlalchemy.orm import Session

from data.models import Portfolio, PortfolioAsset, Asset
from data.repositories import save_portfolio_metrics
from services.market_data_service import load_portfolio_price_matrix


def calculate_big_single_position(weights_df: pd.DataFrame) -> float | None:
    """
    Big Single Position = largest portfolio weight
    """
    if weights_df.empty:
        return None

    w = weights_df["weight"].astype(float)

    if w.sum() == 0:
        return None

    # normalize just in case
    w = w / w.sum()

    return float(w.max())


def calculate_and_store_big_single_position(session: Session) -> list[dict]:
    """
    Value-weighted largest single position using SYMBOLS + WIDE price matrix (latest row).
    """

    portfolios = session.query(Portfolio).all()
    results = []

    for portfolio in portfolios:

        # -------------------------------------------------------
        # 1. Get holdings + asset symbols
        # -------------------------------------------------------
        rows = (
            session.query(PortfolioAsset, Asset)
            .join(Asset, PortfolioAsset.asset_id == Asset.asset_id)
            .filter(PortfolioAsset.portfolio_id == portfolio.portfolio_id)
            .all()
        )

        if not rows:
            continue

        holdings, assets = zip(*rows)
        asset_symbols = [a.symbol for a in assets]

        # -------------------------------------------------------
        # 2. Load PRICE MATRIX (wide format)
        # -------------------------------------------------------
        price_df = load_portfolio_price_matrix(session, asset_symbols)

        if price_df is None or price_df.empty:
            continue

        # -------------------------------------------------------
        # 3. Extract latest prices (LAST ROW)
        # -------------------------------------------------------
        latest_prices = price_df.iloc[-1].to_dict()

        # Remove timestamp key if it exists
        latest_prices.pop("price_date", None)

        # -------------------------------------------------------
        # 4. Build portfolio values
        # -------------------------------------------------------
        rows_out = []
        total_value = 0.0

        for h, a in rows:

            price = latest_prices.get(a.symbol)
            if price is None:
                continue

            value = float(h.quantity) * float(price)
            total_value += value

            rows_out.append(
                {
                    "symbol": a.symbol,
                    "value": value,
                }
            )

        if total_value == 0:
            continue

        # -------------------------------------------------------
        # 5. Convert to weights
        # -------------------------------------------------------
        weights_df = pd.DataFrame(rows_out)
        weights_df["weight"] = weights_df["value"] / total_value

        # -------------------------------------------------------
        # 6. Compute Big Single Position
        # -------------------------------------------------------
        big_single = calculate_big_single_position(weights_df)

        if big_single is None:
            continue

        # -------------------------------------------------------
        # 7. Store metric
        # -------------------------------------------------------
        save_portfolio_metrics(
            session,
            portfolio_id=portfolio.portfolio_id,
            metrics={"big_single_position": big_single},
            start_date=None,
            end_date=None,
        )

        results.append(
            {
                "portfolio": portfolio.name,
                "big_single_position": big_single,
            }
        )

    return results