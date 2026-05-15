"""
src/data/repositories/asset_repo.py

Asset and AssetPrice database operations.
"""

import logging
from decimal import Decimal
from typing import Optional
from uuid import UUID

import pandas as pd
from sqlalchemy.orm import Session

from data.models import Asset, AssetPrice

logger = logging.getLogger(__name__)


# =============================================================================
# ASSET OPERATIONS
# =============================================================================


def upsert_asset(session: Session, symbol: str, name: str, asset_type: str) -> Asset:
    """Insert asset if it doesn't exist; return existing record otherwise."""
    asset = session.query(Asset).filter_by(symbol=symbol).first()
    if asset is None:
        asset = Asset(symbol=symbol, name=name, type=asset_type)
        session.add(asset)
        session.flush()
        logger.info("Inserted new asset: %s (%s)", symbol, asset_type)
    return asset


def get_asset_by_symbol(session: Session, symbol: str) -> Optional[Asset]:
    return session.query(Asset).filter_by(symbol=symbol).first()


def get_assets_by_symbols(session: Session, symbols: list[str]) -> dict[str, Asset]:
    """
    Batch fetch assets by symbol list.
    Returns a dict keyed by symbol for O(1) lookups.
    """
    assets = session.query(Asset).filter(Asset.symbol.in_(symbols)).all()
    return {a.symbol: a for a in assets}


# =============================================================================
# ASSET PRICE OPERATIONS
# =============================================================================


def bulk_insert_prices(session: Session, asset_id: UUID, price_df: pd.DataFrame) -> int:
    """
    Insert full OHLCV + indicators into asset_prices.
    Skips existing (asset_id, price_date) rows.
    Returns number of inserted rows.
    """
    price_df = price_df.copy()
    price_df["price_date"] = pd.to_datetime(price_df["Date"]).dt.date

    existing = {
        r[0]
        for r in session.query(AssetPrice.price_date).filter(
            AssetPrice.asset_id == asset_id
        )
    }

    new_records = []

    for _, row in price_df.iterrows():
        if row["price_date"] in existing:
            continue

        new_records.append(
            AssetPrice(
                asset_id=asset_id,
                price_date=row["price_date"],
                # OHLCV
                open=Decimal(str(row["Open"])) if pd.notna(row.get("Open")) else None,
                high=Decimal(str(row["High"])) if pd.notna(row.get("High")) else None,
                low=Decimal(str(row["Low"])) if pd.notna(row.get("Low")) else None,
                close=Decimal(str(row["Close"])) if pd.notna(row.get("Close")) else None,
                volume=Decimal(str(row["Volume"])) if pd.notna(row.get("Volume")) else None,
                # Returns
                return_=row.get("return"),
                log_return=row.get("log_return"),
                cum_return=row.get("cum_return"),
                # Volatility
                vol_20=row.get("vol_20"),
                vol_60=row.get("vol_60"),
                # Technical indicators
                rsi_14=row.get("rsi_14"),
                macd=row.get("macd"),
                macd_signal=row.get("macd_signal"),
                macd_hist=row.get("macd_hist"),
                # Risk metrics
                rolling_max=row.get("rolling_max"),
                drawdown=row.get("drawdown"),
            )
        )

    if new_records:
        session.bulk_save_objects(new_records)
        session.flush()

    logger.info(
        "Inserted %d new price records for asset %s",
        len(new_records),
        asset_id,
    )
    return len(new_records)


def get_price_history(
    session: Session,
    symbol: str,
    start: str = None,
    end: str = None,
) -> pd.DataFrame:
    """
    Fetch historical prices for a symbol as a DataFrame.
    Optional start/end filters as 'YYYY-MM-DD' strings.
    """
    asset = get_asset_by_symbol(session, symbol)
    if asset is None:
        logger.warning("Asset '%s' not found in database.", symbol)
        return pd.DataFrame()

    query = (
        session.query(AssetPrice)
        .filter_by(asset_id=asset.asset_id)
    )
    if start:
        query = query.filter(AssetPrice.price_date >= start)
    if end:
        query = query.filter(AssetPrice.price_date <= end)

    rows = query.order_by(AssetPrice.price_date).all()

    if not rows:
        return pd.DataFrame()

    return pd.DataFrame(
        [{"price_date": r.price_date, "close": float(r.close)} for r in rows]
    ).set_index("price_date")