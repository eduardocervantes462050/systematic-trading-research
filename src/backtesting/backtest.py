import pandas as pd


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


def backtest_all_tickers(features_folder, results_folder):
    import os
    import pandas as pd
    import matplotlib.pyplot as plt
    from backtesting.signals import generate_signals
    from backtesting.backtest import backtest_strategy

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

        # Plot equity curve
        plt.figure(figsize=(10, 5))
        df["equity"].plot(title=f"{ticker} Equity Curve")
        plt.savefig(os.path.join(results_folder, f"{ticker}_equity.png"))
        plt.close()
