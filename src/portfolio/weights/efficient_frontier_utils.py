# utils/efficient_frontier_utils.py
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from portfolio.mean_variance import efficient_frontier


def compute_and_save_efficient_frontier(filtered_data, ef_cfg):
    """
    Compute EF from filtered price data and save graph.
    Returns the Max Sharpe Portfolio weights for use in rebalancing.
    """
    tickers = list(filtered_data.keys())
    returns_df = pd.DataFrame(
        {t: df["Close"].pct_change().dropna() for t, df in filtered_data.items()}
    )
    expected_returns = returns_df.mean().values
    cov_matrix = returns_df.cov().values

    # Generate EF
    returns_range = np.linspace(
        returns_df.mean().min(), returns_df.mean().max(), ef_cfg.get("n_points", 50)
    )
    ef_returns, ef_vols, ef_weights_array = efficient_frontier(
        expected_returns, cov_matrix, returns_range
    )

    # Find Max Sharpe Portfolio (assume risk-free = 0)
    sharpe_ratios = ef_returns / ef_vols
    max_idx = np.argmax(sharpe_ratios)
    max_sharpe_weights = ef_weights_array[max_idx]

    # Convert to dict
    ef_weights = {tickers[i]: max_sharpe_weights[i] for i in range(len(tickers))}

    # Plot EF
    plt.figure(figsize=(10, 6))
    plt.plot(ef_vols, ef_returns, "b--", linewidth=2, label="Efficient Frontier")
    plt.scatter(
        ef_vols[max_idx],
        ef_returns[max_idx],
        color="r",
        marker="*",
        s=200,
        label="Max Sharpe",
    )
    plt.xlabel("Volatility")
    plt.ylabel("Expected Return")
    plt.title("Efficient Frontier")
    plt.legend()
    plt.grid(True)
    ef_path = ef_cfg.get(
        "save_path",
        r"C:\Users\eduar\Projects\Python\quant_project\reports\figures\efficient_frontier.png",
    )
    plt.savefig(ef_path)
    plt.close()
    print(f"Efficient Frontier saved to {ef_path}")

    return ef_weights, returns_df
