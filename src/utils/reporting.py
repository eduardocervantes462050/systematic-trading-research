import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


def generate_overall_equity_curve(
    tickers, backtests_folder, figures_dir, initial_capital=100_000
):
    os.makedirs(figures_dir, exist_ok=True)

    all_returns = pd.DataFrame()

    for ticker in tickers:
        path = os.path.join(backtests_folder, f"{ticker}_backtest.csv")
        if os.path.exists(path):
            df = pd.read_csv(path, index_col=0, parse_dates=True)
            if "strategy_return" in df.columns:
                all_returns[ticker] = df["strategy_return"]
            else:
                print(f"Warning: 'strategy_return' not found in {ticker}_backtest.csv")
        else:
            print(f"Warning: {ticker}_backtest.csv not found")

    all_returns = all_returns.fillna(0)
    portfolio_returns = all_returns.mean(axis=1)
    equity_curve = initial_capital * (1 + portfolio_returns).cumprod()

    # Plot equity curve
    plt.figure(figsize=(12, 6))
    plt.plot(equity_curve.index, equity_curve.values, label="Portfolio Equity")
    plt.title("Overall Equity Curve")
    plt.xlabel("Date")
    plt.ylabel("Portfolio Value ($)")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    output_path = os.path.join(figures_dir, "overall_equity_curve.png")
    plt.savefig(output_path)
    plt.close()
    print(f"Saved overall equity curve to {output_path}")

    # Plot drawdown
    running_max = equity_curve.cummax()
    drawdown = (equity_curve - running_max) / running_max
    plt.figure(figsize=(12, 4))
    plt.fill_between(drawdown.index, drawdown.values, 0, color="red")
    plt.title("Portfolio Drawdown")
    plt.ylabel("Drawdown")
    plt.grid(True)
    plt.tight_layout()
    drawdown_path = os.path.join(figures_dir, "overall_drawdown.png")
    plt.savefig(drawdown_path)
    plt.close()
    print(f"Saved overall drawdown to {drawdown_path}")

    return equity_curve
