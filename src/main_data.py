import os
import json

from data.fetch_data import DataFetcher
from data.features import FeatureEngineer
from utils.helpers import ensure_folder

path = r"C:\Users\eduar\Projects\Python\quant_project\config\project_config.json"

with open(path, "r") as f:
    config = json.load(f)

# Access folders
RAW_DATA_FOLDER = config["folders"]["raw_data"]
INTERIM_DATA_FOLDER = config["folders"]["interim_data"]
REPORTS_FOLDER = config["folders"]["reports"]
BACKTESTS_FOLDER = config["folders"]["backtests"]

# Access tickers and other settings
TICKERS = config["tickers"]
FRED_API_KEY = config["fred"]["api_key"]
FRED_SERIES_ID = config["fred"]["series_id"]
FRED_URL = config["fred"]["url"]
ENABLED_PLOT_GROUPS = config["enabled_plot_groups"]


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


if __name__ == "__main__":
    main()
