"""
main.py

Main script for the quant-project pipeline:
1. Fetch historical price data for selected tickers
2. Perform feature engineering
3. Save processed data
4. Fetch FRED macroeconomic data
5. Plot features for analysis
6. Generate trading signals and run backtests (including walk-forward testing)

Author: Eduardo Cervantes Alarcón
Date: 2026-02-09
"""

import os
import pandas as pd
import yaml

from data.fetch_data import DataFetcher
from data.features import FeatureEngineer
from utils.visualizations import plot_all_tickers
from backtesting.backtest import backtest_all_tickers
from backtesting.walkforward import run_walkforward_all_tickers
from utils.reporting import generate_overall_equity_curve


# -------------------------------
# Configuration
# -------------------------------
TICKERS = [
    "AAPL",
    "BAC",
    "MSFT",
    "INTC",
    "WFC",
    "C",
    "GC=F",
    "SI=F",
    "CL=F",
    "BTC-USD",
    "ETH-USD",
    "XRP-USD",
    "EURUSD=X",
    "JPY=X",
    "GBPUSD=X",
    "PRLAX",
    "QASGX",
    "HISFX",
    "^TNX",
    "^IRX",
    "^TYX",
]

RAW_DATA_FOLDER = r"C:\Users\eduar\Projects\Python\quant-project\data\raw"
INTERIM_DATA_FOLDER = r"C:\Users\eduar\Projects\Python\quant-project\data\interim"
REPORTS_FOLDER = r"C:\Users\eduar\Projects\Python\quant-project\reports"
BACKTESTS_FOLDER = os.path.join(REPORTS_FOLDER, "backtests")

FRED_API_KEY = (
    "3fe2e620a3cf180bc8c1f2777203b20d"  # Consider using environment variables
)
FRED_SERIES_ID = "CPIAUCSL"
FRED_URL = "https://api.stlouisfed.org/fred/series/observations"

ENABLED_PLOT_GROUPS = [
    "price",
    "volume",
    "returns",
    "volatility",
    "momentum",
    "trend",
]  # Groups to visualize


# -------------------------------
# Helper Functions
# -------------------------------
def ensure_folder(path: str):
    """Create folder if it does not exist."""
    os.makedirs(path, exist_ok=True)


# -------------------------------
# Main Pipeline
# -------------------------------
def main():
    print("=== Quant Project Pipeline Started ===\n")

    # -------------------------------
    # Step 1: Download missing price data
    # -------------------------------
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
    else:
        print("All tickers already downloaded.")

    if failed_tickers:
        print(f"⚠️ Failed to download: {failed_tickers}")

    # -------------------------------
    # Step 2: Feature Engineering
    # -------------------------------
    print("\nStep 2: Performing feature engineering...")
    fe = FeatureEngineer()
    ensure_folder(INTERIM_DATA_FOLDER)
    data_with_features = fe.process_csv_folder(RAW_DATA_FOLDER)

    for ticker, df_features in data_with_features.items():
        path = os.path.join(INTERIM_DATA_FOLDER, f"{ticker}_features.csv")
        df_features.to_csv(path)
        print(f"Saved features for {ticker} ({len(df_features)} rows)")

    # -------------------------------
    # Step 3: Fetch FRED data
    # -------------------------------
    print("\nStep 3: Fetching FRED macroeconomic data...")
    try:
        fred_data = fetcher.get_fred_data(FRED_API_KEY, FRED_SERIES_ID, FRED_URL)
        fred_data_path = os.path.join(RAW_DATA_FOLDER, f"{FRED_SERIES_ID}.csv")
        fred_data.to_csv(fred_data_path)
        print(f"Saved FRED data to {fred_data_path} ({len(fred_data)} rows)")
    except Exception as e:
        print(f"Error fetching FRED data: {e}")

    import yaml

    # Load config
    with open("config/analysis_config.yaml") as f:
        analysis_cfg = yaml.safe_load(f)

    ANALYSIS_START = pd.to_datetime(analysis_cfg.get("start_date", "2000-01-01"))
    ANALYSIS_END = pd.to_datetime(analysis_cfg.get("end_date", "2025-12-31"))

    # Optional tickers override
    ANALYSIS_TICKERS = analysis_cfg.get(
        "tickers", None
    )  # None means use all downloaded tickers

    # Filter feature data by date range
    filtered_data = {}
    features_files = [
        f for f in os.listdir(INTERIM_DATA_FOLDER) if f.endswith("_features.csv")
    ]

    for file in features_files:
        ticker = os.path.basename(file).split("_")[0]
        if ANALYSIS_TICKERS and ticker not in ANALYSIS_TICKERS:
            continue
        df = pd.read_csv(
            os.path.join(INTERIM_DATA_FOLDER, file), index_col=0, parse_dates=True
        )
        df_filtered = df.loc[(df.index >= ANALYSIS_START) & (df.index <= ANALYSIS_END)]
        filtered_data[ticker] = df_filtered
        # Optional: save filtered version
        for ticker, df_filtered in filtered_data.items():
            df_filtered.to_csv(
                os.path.join(INTERIM_DATA_FOLDER, f"{ticker}_features_filtered.csv")
            )

    # -------------------------------
    # Step 4: Plot features
    # -------------------------------
    print("\nStep 4: Plotting features...")
    try:
        plot_all_tickers(
            features_dir=INTERIM_DATA_FOLDER,
            reports_dir=REPORTS_FOLDER,
            enabled_groups=ENABLED_PLOT_GROUPS,
        )
        print("Feature plots generated successfully.")
    except Exception as e:
        print(f"Error plotting features: {e}")

    # -------------------------------
    # Step 5: Backtesting
    # -------------------------------
    print("\nStep 5: Running backtests...")
    ensure_folder(BACKTESTS_FOLDER)

    try:
        backtest_all_tickers(INTERIM_DATA_FOLDER, BACKTESTS_FOLDER)
        print("Backtests completed successfully.")
    except Exception as e:
        print(f"Error during backtesting: {e}")

    # -------------------------------
    # Step 6: Walk-forward testing
    # -------------------------------
    print("\nStep 6: Running walk-forward tests...")
    try:
        run_walkforward_all_tickers(INTERIM_DATA_FOLDER, BACKTESTS_FOLDER)
        print("Walk-forward testing completed successfully.")
    except Exception as e:
        print(f"Error during walk-forward testing: {e}")

    # -------------------------------
    # Step 7: Overall equity curve
    # -------------------------------

    backtests_folder = "reports/backtests"
    figures_dir = "reports/figures"
    os.makedirs(figures_dir, exist_ok=True)

    # Get tickers dynamically from feature files
    features_folder = "data/interim"
    tickers_files = [
        f for f in os.listdir(features_folder) if f.endswith("_features_filtered.csv")
    ]
    tickers = [os.path.basename(f).split("_")[0] for f in tickers_files]

    # Generate overall equity curve and drawdown
    generate_overall_equity_curve(tickers, backtests_folder, figures_dir)

    print("\n=== Pipeline Finished ===")


if __name__ == "__main__":
    main()
