import os
import pandas as pd
import matplotlib.pyplot as plt
from backtesting.signals import generate_signals


def backtest_strategy(df, cost=0.0005):
    df = df.copy()
    df["position"] = 0
    df["position"] = df["signal"].replace(-1, 0)  # convert sell signals to 0
    df["position"] = df["signal"].replace(-1, 0).astype(float)  # make numeric
    df.loc[df["position"] == 0, "position"] = pd.NA  # temporary NA for ffill
    df["position"] = df["position"].ffill().fillna(0)

    df["asset_return"] = df["Close"].pct_change()
    df["strategy_return"] = df["position"].shift(1) * df["asset_return"]

    df["trade"] = df["position"].diff().abs()
    df["cost"] = df["trade"] * cost
    df["net_return"] = df["strategy_return"] - df["cost"]

    df["equity"] = (1 + df["net_return"]).cumprod()
    df["equity_peak"] = df["equity"].cummax()
    df["drawdown"] = df["equity"] / df["equity_peak"] - 1

    return df


def plot_equity_with_signals(df, ticker, results_folder):
    """
    Plot equity curve with positions and signals
    """
    fig, axes = plt.subplots(
        3, 1, figsize=(14, 12), sharex=True, gridspec_kw={"height_ratios": [2, 1, 1]}
    )

    # -------------------
    # 1️⃣ Price + Signals
    # -------------------
    axes[0].plot(df.index, df["Close"], label="Close", color="black")

    # Buy/sell markers from signals
    axes[0].scatter(
        df.index[df["signal"] == 1],
        df.loc[df["signal"] == 1, "Close"],
        marker="^",
        color="green",
        label="Buy Signal",
    )
    axes[0].scatter(
        df.index[df["signal"] == -1],
        df.loc[df["signal"] == -1, "Close"],
        marker="v",
        color="red",
        label="Sell Signal",
    )

    axes[0].set_ylabel("Price")
    axes[0].set_title(f"{ticker} Price + Signals")
    axes[0].legend()

    # -------------------
    # 2️⃣ Position (0 or 1)
    # -------------------
    axes[1].step(df.index, df["position"], where="post", color="blue")
    axes[1].set_ylabel("Position")
    axes[1].set_title("Strategy Position (0=flat, 1=long)")

    # -------------------
    # 3️⃣ Equity Curve
    # -------------------
    axes[2].plot(df.index, df["equity"], color="purple")
    axes[2].set_ylabel("Equity")
    axes[2].set_title("Equity Curve")
    axes[2].set_xlabel("Date")

    plt.tight_layout()
    plt.savefig(os.path.join(results_folder, f"{ticker}_equity_signals.png"))
    plt.close()


def backtest_all_tickers(features_folder, results_folder):
    os.makedirs(results_folder, exist_ok=True)

    for file_name in os.listdir(features_folder):
        if not file_name.endswith("_features_filtered.csv"):
            continue

        ticker = file_name.replace("_features_filtered.csv", "")
        file_path = os.path.join(features_folder, file_name)
        df = pd.read_csv(file_path, index_col=0, parse_dates=True)

        # Generate signals
        df = generate_signals(df)

        # Backtest
        df = backtest_strategy(df)

        # Save results
        result_path = os.path.join(results_folder, f"{ticker}_backtest.csv")
        df.to_csv(result_path)
        print(f"Backtest complete for {ticker}, saved to {result_path}")

        print(df)

        # Plot equity + signals + positions
        plot_equity_with_signals(df, ticker, results_folder)
        print(f"Equity + Signals plot saved for {ticker}")
