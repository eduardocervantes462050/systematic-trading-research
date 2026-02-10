# src/backtesting/walkforward.py
import os
import pandas as pd
import matplotlib.pyplot as plt

from backtesting.backtest import backtest_strategy
from backtesting.signals import generate_signals  # your existing signal function


def run_walkforward_all_tickers(
    features_folder, results_folder, train_end="2020-12-31"
):
    """
    Run walk-forward testing on all tickers in features_folder.
    Generates train and out-of-sample backtests and saves plots + metrics.

    Parameters:
    -----------
    features_folder: str
        Path to folder containing feature-engineered CSVs
    results_folder: str
        Path to save equity curves and metrics
    train_end: str
        Date to split train/test (YYYY-MM-DD)
    """
    os.makedirs(results_folder, exist_ok=True)

    metrics_list = []

    for file in os.listdir(features_folder):
        if not file.endswith(".csv"):
            continue

        ticker = file.replace("_features_filtered.csv", "")
        print(f"\n=== Processing {ticker} ===")
        path = os.path.join(features_folder, file)
        df = pd.read_csv(path, index_col=0, parse_dates=True)

        # Split into train / out-of-sample
        train_df = df.loc[:train_end].copy()
        test_df = df.loc[train_end:].copy()

        # Train backtest
        train_df = generate_signals(train_df)
        train_df = backtest_strategy(train_df)

        # Out-of-sample backtest
        test_df = generate_signals(test_df)
        test_df = backtest_strategy(test_df)

        # Save equity curve plots
        plt.figure(figsize=(10, 5))
        plt.plot(train_df["equity"], label="Train")
        plt.plot(test_df["equity"], label="Out-of-Sample")
        plt.title(f"{ticker} Equity Curve")
        plt.xlabel("Date")
        plt.ylabel("Equity")
        plt.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(results_folder, f"{ticker}_equity.png"))
        plt.close()

        # Save metrics
        metrics_list.append(
            {
                "Ticker": ticker,
                "Train Total Return": train_df["equity"].iloc[-1] - 1,
                "Train Max Drawdown": train_df["drawdown"].min(),
                "Train Sharpe": (
                    train_df["net_return"].mean() / train_df["net_return"].std()
                )
                * (252**0.5),
                "Test Total Return": test_df["equity"].iloc[-1] - 1,
                "Test Max Drawdown": test_df["drawdown"].min(),
                "Test Sharpe": (
                    test_df["net_return"].mean() / test_df["net_return"].std()
                )
                * (252**0.5),
            }
        )

    # Save metrics CSV
    metrics_df = pd.DataFrame(metrics_list)
    metrics_df.to_csv(
        os.path.join(results_folder, "walkforward_metrics.csv"), index=False
    )
    print(f"\nWalk-forward testing completed! Metrics saved to {results_folder}")
