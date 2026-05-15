import pandas as pd

from sqlalchemy.orm import Session

from data.models import Asset, AssetPrice


def get_price_history(
    session: Session,
    assets: list[str],
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """
    Load historical prices for multiple assets
    and return a price matrix.

    Output:
        index   -> dates
        columns -> asset symbols
        values  -> prices
    """

    query = (
        session.query(
            Asset.symbol,
            AssetPrice.price_date,
            AssetPrice.close,
        )
        .join(
            Asset,
            AssetPrice.asset_id == Asset.asset_id,
        )
        .filter(
            Asset.symbol.in_(assets)
        )
    )

    if start_date:
        query = query.filter(
            AssetPrice.price_date >= start_date
        )

    if end_date:
        query = query.filter(
            AssetPrice.price_date <= end_date
        )

    rows = query.all()

    if not rows:
        raise ValueError(
            f"No price data found for assets: {assets}"
        )

    df = pd.DataFrame(
        rows,
        columns=[
            "symbol",
            "price_date",
            "price",
        ],
    )

    # Pivot into matrix form
    price_df = df.pivot(
        index="price_date",
        columns="symbol",
        values="price",
    )

    # Clean missing values
    price_df = (
        price_df
        .sort_index()
        .ffill()
        .dropna()
    )

    return price_df