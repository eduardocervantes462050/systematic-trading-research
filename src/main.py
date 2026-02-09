from data.fetch_data import DataFetcher
from data.features import (
    FeatureEngineer,
)  # assuming your class is in feature_engineer.py
import os
import pandas as pd

from utils.visualizations import plot_all_tickers


def main():
    print("Starting data fetch…")

    fetcher = DataFetcher()
    stocks = [
        "AAPL",
        # "MSFT",
        # "INTC",
        # "WFC",
        "BAC",
        # "C",
        # "GC=F",
        # "SI=F",
        # "CL=F",
        # "BTC-USD",
        # "ETH-USD",
        # "XRP-USD",
        # "EURUSD=X",
        # "JPY=X",
        # "GBPUSD=X",
        # "PRLAX",
        # "QASGX",
        # "HISFX",
        # "^TNX",
        # "^IRX",
        # "^TYX",
    ]

    folder = r"C:\Users\eduar\Projects\Python\quant-project\data\raw"
    os.makedirs(folder, exist_ok=True)

    # Step 1: Download missing tickers
    tickers_to_fetch = []
    for ticker in stocks:
        path = os.path.join(folder, f"{ticker}.csv")
        if os.path.exists(path):
            print(f"Skipping {ticker}, already downloaded.")
        else:
            tickers_to_fetch.append(ticker)

    if tickers_to_fetch:
        raw = fetcher.get_price_data(
            tickers_to_fetch,
            start="2000-01-01",
            end="2025-12-31",
            batch_size=5,
            retries=3,
            delay=5,
        )

        for ticker, df in raw.items():
            if not df.empty:
                df.to_csv(os.path.join(folder, f"{ticker}.csv"))
                print(f"Saved {ticker}.csv with {len(df)} rows")
    else:
        print("All tickers already downloaded.")

    print("\nStep 2: Feature Engineering")
    fe = FeatureEngineer()
    data_with_features = fe.process_csv_folder(folder)

    print("\nStep 3: Save feature-engineered CSVs")
    features_folder = r"C:\Users\eduar\Projects\Python\quant-project\data\interim"
    os.makedirs(features_folder, exist_ok=True)
    for ticker, df_features in data_with_features.items():
        path = os.path.join(features_folder, f"{ticker}_features.csv")
        df_features.to_csv(path)
        print(f"Saved features for {ticker}, {len(df_features)} rows")
    print("All tickers processed with features!")
    print("\nStep 4: Save get fred data")
    API_KEY = "3fe2e620a3cf180bc8c1f2777203b20d"
    SERIES_ID = "CPIAUCSL"
    url = "https://api.stlouisfed.org/fred/series/observations"
    freddata = fetcher.get_fred_data(API_KEY, SERIES_ID, url)
    freddata.to_csv(os.path.join(folder, f"{SERIES_ID}.csv"))
    print(f"Saved {SERIES_ID}.csv with {len(freddata)} rows")

    #     FEATURE_GROUPS = {
    #     "price": ["Close"],
    #     "returns": ["return", "log_return", "cum_return"],
    #     "volatility": ["vol_20", "vol_60", "drawdown"],
    #     "momentum": ["rsi_14"],
    #     "trend": ["macd", "macd_signal", "macd_hist"],
    # }
    enabled_groups = ["price", "volume"]

    plot_all_tickers(
        features_dir=r"C:\Users\eduar\Projects\Python\quant-project\data\interim",
        reports_dir=r"C:\Users\eduar\Projects\Python\quant-project\reports",
        enabled_groups=enabled_groups,
    )

    print("\nStep 5: Generate signals and backtest")

    from backtesting.backtest import backtest_all_tickers

    features_folder = r"C:\Users\eduar\Projects\Python\quant-project\data\interim"
    results_folder = r"C:\Users\eduar\Projects\Python\quant-project\reports\backtests"

    backtest_all_tickers(features_folder, results_folder)

    from backtesting.walkforward import run_walkforward_all_tickers

    features_folder = "data/interim"
    results_folder = "reports/backtests"

    run_walkforward_all_tickers(features_folder, results_folder)


if __name__ == "__main__":
    main()
