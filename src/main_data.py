"""
data_pipeline.py
----------------
Steps 1-3 of the quant-project pipeline + DB persistence.
"""

import os
import json
import pandas as pd

from data.fetch_data import DataFetcher
from data.features import FeatureEngineer
from utils.helpers import ensure_folder
from data.database import build_db, get_session, upsert_asset, bulk_insert_prices

# ---------------------------------------------------------------------------
# Global config
# ---------------------------------------------------------------------------

_CONFIG_PATH = (
    r"C:\Users\eduar\Projects\Python\quant_project\config\project_config.json"
)

with open(_CONFIG_PATH, "r") as f:
    _config = json.load(f)

RAW_DATA_FOLDER = _config["folders"]["raw_data"]
INTERIM_DATA_FOLDER = _config["folders"]["interim_data"]
REPORTS_FOLDER = _config["folders"]["reports"]
BACKTESTS_FOLDER = _config["folders"]["backtests"]
TICKERS = _config["tickers"]
FRED_API_KEY = _config["fred"]["api_key"]
FRED_SERIES_ID = _config["fred"]["series_id"]
FRED_URL = _config["fred"]["url"]
ENABLED_PLOT_GROUPS = _config["enabled_plot_groups"]

# Asset type mapping — extend if needed
ASSET_TYPES = {
    "BTC-USD": "crypto",
    "ETH-USD": "crypto",
    "XRP-USD": "crypto",
    "GC=F": "ETF",
    "SI=F": "ETF",
    "CL=F": "ETF",
    "EURUSD=X": "bond",
    "GBPUSD=X": "bond",
    "JPY=X": "bond",
    "^TNX": "bond",
    "^TYX": "bond",
    "^IRX": "bond",
}


def get_asset_type(ticker: str) -> str:
    """Return asset type for a ticker, default to stock."""
    return ASSET_TYPES.get(ticker, "stock")


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------


def main() -> None:
    print("=== Quant Project Pipeline Started ===\n")

    # Connect to DB once — reuse across all steps
    engine, SessionFactory = build_db()

    # ------------------------------------------------------------------
    # Step 1 — Download missing price data + save to DB
    # ------------------------------------------------------------------
    # ------------------------------------------------------------------

    # Step 1 — Download missing price data + save to DB
    # ------------------------------------------------------------------
    print("Step 1: Fetching price data...")

    fetcher = DataFetcher()
    ensure_folder(RAW_DATA_FOLDER)

    tickers_to_fetch = []
    for ticker in TICKERS:
        path = os.path.join(RAW_DATA_FOLDER, f"{ticker}.csv")
        if os.path.exists(path):
            print(f"Skipping {ticker}, already downloaded.")
        else:
            tickers_to_fetch.append(ticker)

    failed_tickers = []

    if tickers_to_fetch:
        raw_data = fetcher.get_price_data(
            tickers_to_fetch,
            start="2000-01-01",
            end="2025-12-31",
            batch_size=5,
            retries=3,
            delay=5,
        )

        for ticker, df in raw_data.items():
            if df.empty:
                print(f"Warning: {ticker} returned empty data.")
                failed_tickers.append(ticker)
            else:
                df.to_csv(os.path.join(RAW_DATA_FOLDER, f"{ticker}.csv"))
                print(f"Saved {ticker}.csv with {len(df)} rows")

                with get_session(SessionFactory) as session:
                    asset = upsert_asset(
                        session,
                        symbol=ticker,
                        name=ticker,
                        asset_type=get_asset_type(ticker),
                    )
                    df_prices = df[["Close"]].reset_index()
                    df_prices.columns = ["price_date", "price"]
                    df_prices = df_prices.dropna()
                    count = bulk_insert_prices(session, asset.asset_id, df_prices)
                    print(f"  → Inserted {count} price rows into DB for {ticker}")
    else:
        print("All tickers already downloaded.")

    # ── Load ALL existing CSVs into DB regardless ──────────────────────
    print("\nLoading all existing CSVs into DB...")
    for ticker in TICKERS:
        csv_path = os.path.join(RAW_DATA_FOLDER, f"{ticker}.csv")
        if not os.path.exists(csv_path):
            print(f"  ⚠️  No CSV found for {ticker}, skipping.")
            continue

        # peek at the first row to detect format
        with open(csv_path, "r") as f:
            first_line = f.readline().strip()

        # FORMAT A — yfinance multi-header: "Price,Close,High,Low,Open,Volume"
        if first_line.startswith("Price"):
            df = pd.read_csv(csv_path, header=0, skiprows=[1, 2])
            df = df.rename(columns={"Price": "price_date", "Close": "price"})

        # FORMAT B — clean header: "Date,Close,High,Low,Open,Volume"
        elif first_line.startswith("Date"):
            df = pd.read_csv(csv_path, index_col=0)
            df = df.reset_index()
            df = df.rename(columns={df.columns[0]: "price_date", "Close": "price"})

        else:
            print(
                f"  ⚠️  {ticker} — unrecognized format, skipping. First line: {first_line}"
            )
            continue

        # common cleaning for both formats
        df = df[["price_date", "price"]].dropna()
        df = df[pd.to_datetime(df["price_date"], errors="coerce").notna()]
        df["price_date"] = pd.to_datetime(df["price_date"], errors="coerce").dt.date
        df["price"] = pd.to_numeric(df["price"], errors="coerce")
        df = df.dropna()

        if df.empty:
            print(f"  ⚠️  {ticker} — no valid rows after cleaning, skipping.")
            continue

        with get_session(SessionFactory) as session:
            asset = upsert_asset(
                session, symbol=ticker, name=ticker, asset_type=get_asset_type(ticker)
            )
            count = bulk_insert_prices(session, asset.asset_id, df)
            print(f"  ✅ {ticker} — {count} new rows inserted into DB")

    if failed_tickers:
        print(f"⚠️  Failed to download: {failed_tickers}")

    # ------------------------------------------------------------------
    # Step 2 — Feature engineering (no DB changes needed here)
    # ------------------------------------------------------------------
    print("\nStep 2: Performing feature engineering...")

    fe = FeatureEngineer()
    ensure_folder(INTERIM_DATA_FOLDER)
    data_with_features = fe.process_csv_folder(RAW_DATA_FOLDER)

    for ticker, df_features in data_with_features.items():
        path = os.path.join(INTERIM_DATA_FOLDER, f"{ticker}_features.csv")
        df_features.to_csv(path)
        print(f"Saved features for {ticker} ({len(df_features)} rows)")

    # ------------------------------------------------------------------
    # Step 3 — Fetch FRED macroeconomic data + save to DB
    # ------------------------------------------------------------------
    print("\nStep 3: Fetching FRED macroeconomic data...")

    try:
        fred_data = fetcher.get_fred_data(FRED_API_KEY, FRED_SERIES_ID, FRED_URL)

        # ── Save CSV (original behaviour) ──────────────────────────
        fred_data_path = os.path.join(RAW_DATA_FOLDER, f"{FRED_SERIES_ID}.csv")
        fred_data.to_csv(fred_data_path)
        print(f"Saved FRED data to {fred_data_path} ({len(fred_data)} rows)")

        # ── Save to DB ──────────────────────────────────────────────
        with get_session(SessionFactory) as session:
            asset = upsert_asset(
                session,
                symbol=FRED_SERIES_ID,
                name=f"FRED: {FRED_SERIES_ID}",
                asset_type="bond",
            )
            df_fred = fred_data.reset_index()
            df_fred.columns = ["price_date", "price"]
            df_fred = df_fred.dropna()
            count = bulk_insert_prices(session, asset.asset_id, df_fred)
            print(f"  → Inserted {count} FRED rows into DB")

    except Exception as e:
        print(f"Error fetching FRED data: {e}")

    print("\n🎉 Pipeline complete!")


if __name__ == "__main__":
    main()
