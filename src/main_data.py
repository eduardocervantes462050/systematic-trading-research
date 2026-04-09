from __future__ import annotations
import json
import os
import pandas as pd
from data.database import build_db, bulk_insert_prices, get_session, upsert_asset
from data.features import FeatureEngineer
from data.fetch_data import DataFetcher
from utils.helpers import ensure_folder

_CONFIG_PATH = (
    r"C:\Users\eduar\Projects\Python\quant_project\config\project_config.json"
)


def _load_config(path: str) -> dict:
    with open(path, "r") as fh:
        return json.load(fh)


_config = _load_config(_CONFIG_PATH)

RAW_DATA_FOLDER: str = _config["folders"]["raw_data"]
INTERIM_DATA_FOLDER: str = _config["folders"]["interim_data"]
REPORTS_FOLDER: str = _config["folders"]["reports"]
BACKTESTS_FOLDER: str = _config["folders"]["backtests"]
TICKERS: list[str] = _config["tickers"]
FRED_API_KEY: str = _config["fred"]["api_key"]
FRED_SERIES_ID: str = _config["fred"]["series_id"]
FRED_URL: str = _config["fred"]["url"]
ENABLED_PLOT_GROUPS: list[str] = _config["enabled_plot_groups"]

ASSET_TYPES: dict[str, str] = {
    # Crypto
    "BTC-USD": "crypto",
    "ETH-USD": "crypto",
    "XRP-USD": "crypto",
    # Commodities (futures)
    "GC=F": "ETF",  # Gold
    "SI=F": "ETF",  # Silver
    "CL=F": "ETF",  # Crude oil
    # Forex / FX rates
    "EURUSD=X": "bond",
    "GBPUSD=X": "bond",
    "JPY=X": "bond",
    # Treasury yields
    "^TNX": "bond",  # 10-year
    "^TYX": "bond",  # 30-year
    "^IRX": "bond",  # 13-week
}


def get_asset_type(ticker: str) -> str:
    """Return the asset-class label for *ticker*.

    Falls back to ``"stock"`` for any symbol not listed in :data:`ASSET_TYPES`.
    """
    return ASSET_TYPES.get(ticker, "stock")


# ---------------------------------------------------------------------------
# Pipeline steps
# ---------------------------------------------------------------------------


def _step1_fetch_prices(
    fetcher: DataFetcher,
    session_factory,
) -> list[str]:
    """Step 1 — Download raw OHLCV data and persist close prices to the DB.

    For each ticker in :data:`TICKERS`:
    * **Skip** if a raw CSV already exists in :data:`RAW_DATA_FOLDER`.
    * Otherwise download via ``DataFetcher.get_price_data``, save to CSV, and
      insert the ``Close`` column into the database.

    Parameters
    ----------
    fetcher:
        Configured :class:`DataFetcher` instance.
    session_factory:
        SQLAlchemy session factory returned by :func:`build_db`.

    Returns
    -------
    list[str]
        Tickers for which the download failed (empty DataFrame returned).
    """
    print("Step 1: Fetching price data...")
    ensure_folder(RAW_DATA_FOLDER)

    tickers_to_fetch = []
    for ticker in TICKERS:
        path = os.path.join(RAW_DATA_FOLDER, f"{ticker}.csv")
        if os.path.exists(path):
            print(f"  Skipping {ticker} — already downloaded.")
        else:
            tickers_to_fetch.append(ticker)

    failed_tickers: list[str] = []

    if not tickers_to_fetch:
        print("  All tickers already downloaded.")
        return failed_tickers

    raw_data: dict[str, pd.DataFrame] = fetcher.get_price_data(
        tickers_to_fetch,
        start="2000-01-01",
        end="2025-12-31",
        batch_size=5,
        retries=3,
        delay=5,
    )
    # raw_data shape:
    #   {
    #       "AAPL": DataFrame,   # OHLCV columns, DatetimeIndex
    #       "MSFT": DataFrame,
    #       ...
    #   }

    for ticker, df in raw_data.items():
        if df.empty:
            print(f"  ⚠️  {ticker} — returned empty data, skipping.")
            failed_tickers.append(ticker)
            continue

        # Persist raw CSV
        csv_path = os.path.join(RAW_DATA_FOLDER, f"{ticker}.csv")
        df.to_csv(csv_path)
        print(f"  Saved {ticker}.csv ({len(df)} rows)")

        # Insert close prices into the DB
        with get_session(session_factory) as session:
            asset = upsert_asset(
                session,
                symbol=ticker,
                name=ticker,
                asset_type=get_asset_type(ticker),
            )
            df_prices = (
                df[["Close"]]
                .reset_index()
                .rename(columns={"index": "price_date", "Close": "price"})
                .dropna()
            )
            count = bulk_insert_prices(session, asset.asset_id, df_prices)
            print(f"    → {count} price rows inserted into DB for {ticker}")

    return failed_tickers


def _step2_engineer_features(
    session_factory,
) -> None:
    print("\nStep 2: Performing feature engineering...")
    ensure_folder(INTERIM_DATA_FOLDER)

    fe = FeatureEngineer()
    data_with_features: dict[str, pd.DataFrame] = fe.process_csv_folder(RAW_DATA_FOLDER)

    # --- Save enriched CSVs to disk ----------------------------------------
    for ticker, df_features in data_with_features.items():
        out_path = os.path.join(INTERIM_DATA_FOLDER, f"{ticker}_features.csv")
        df_features.to_csv(out_path)
        print(f"  Saved {ticker}_features.csv ({len(df_features)} rows)")

    # --- Load ALL interim CSVs into the DB -----------------------------------
    # This covers tickers that were already on disk before this run so the DB
    # stays in sync even on partial / incremental runs.
    print("\n  Loading all interim CSVs into DB...")
    for ticker in TICKERS:
        csv_path = os.path.join(INTERIM_DATA_FOLDER, f"{ticker}_features.csv")

        if not os.path.exists(csv_path):
            print(f"    ⚠️  No features CSV found for {ticker}, skipping.")
            continue

        df = pd.read_csv(csv_path)

        if df is None:
            print(f"    ⚠️  {ticker} — unrecognised CSV format, skipping.")
            continue

        if df.empty:
            print(f"    ⚠️  {ticker} — no valid rows after cleaning, skipping.")
            continue

        with get_session(session_factory) as session:
            asset = upsert_asset(
                session,
                symbol=ticker,
                name=ticker,
                asset_type=get_asset_type(ticker),
            )
            count = bulk_insert_prices(session, asset.asset_id, df)
            print(f"    ✅ {ticker} — {count} new rows inserted into DB")


def _step3_fetch_fred(
    fetcher: DataFetcher,
    session_factory,
) -> None:
    """Step 3 — Fetch a FRED macro time-series and persist it.

    Downloads the series identified by :data:`FRED_SERIES_ID`, saves it as a
    raw CSV, and inserts it into the database as a synthetic asset so it can
    be joined with equity/crypto price data in downstream analyses.

    Parameters
    ----------
    fetcher:
        Configured :class:`DataFetcher` instance.
    session_factory:
        SQLAlchemy session factory returned by :func:`build_db`.
    """
    print("\nStep 3: Fetching FRED macroeconomic data...")

    try:
        fred_data: pd.DataFrame = fetcher.get_fred_data(
            FRED_API_KEY, FRED_SERIES_ID, FRED_URL
        )

        # Save CSV
        fred_csv_path = os.path.join(RAW_DATA_FOLDER, f"{FRED_SERIES_ID}.csv")
        fred_data.to_csv(fred_csv_path)
        print(f"  Saved FRED data → {fred_csv_path} ({len(fred_data)} rows)")

        # Insert into DB
        with get_session(session_factory) as session:
            asset = upsert_asset(
                session,
                symbol=FRED_SERIES_ID,
                name=f"FRED: {FRED_SERIES_ID}",
                asset_type="bond",
            )
            df_fred = (
                fred_data.reset_index()
                .rename(
                    columns={
                        fred_data.index.name or "index": "price_date",
                        fred_data.columns[0]: "price",
                    }
                )
                .dropna()
            )
            count = bulk_insert_prices(session, asset.asset_id, df_fred)
            print(f"    → {count} FRED rows inserted into DB")

    except Exception as exc:
        print(f"  ❌ Error fetching FRED data: {exc}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Run all three pipeline steps in sequence."""
    print("=== Quant Project Pipeline Started ===\n")

    engine, session_factory = build_db()
    fetcher = DataFetcher()

    failed_tickers = _step1_fetch_prices(fetcher, session_factory)
    _step2_engineer_features(session_factory)
    # _step3_fetch_fred(fetcher, session_factory)

    if failed_tickers:
        print(f"\n⚠️  Tickers that failed to download: {failed_tickers}")

    # print("\n🎉 Pipeline complete!")


if __name__ == "__main__":
    main()
