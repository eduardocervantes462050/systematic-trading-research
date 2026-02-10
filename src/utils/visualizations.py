from pathlib import Path
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from tqdm import tqdm

FEATURE_GROUPS = {
    "price": ["Close"],
    "volume": ["Volume"],
    "returns": ["return", "log_return", "cum_return"],
    "volatility": ["vol_20", "vol_60", "drawdown"],
    "momentum": ["rsi_14"],
    "trend": ["macd", "macd_signal", "macd_hist"],
}


def plot_all_tickers(
    features_dir: str | Path,
    reports_dir: str | Path,
    enabled_groups: list[str],
):
    features_dir = Path(features_dir)
    reports_dir = Path(reports_dir)

    figures_dir = reports_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    feature_files = list(features_dir.glob("*_features_filtered.csv"))

    if not feature_files:
        raise FileNotFoundError("No *_features_filtered.csv files found")

    for file_path in tqdm(feature_files, desc="Plotting tickers"):
        symbol = file_path.stem.replace("_features", "")

        df = pd.read_csv(file_path)

        if "Date" not in df.columns:
            tqdm.write(f"Skipping {symbol}: no Date column")
            continue

        # --- 1️⃣ Time index ---
        df["Date"] = pd.to_datetime(df["Date"])
        df.set_index("Date", inplace=True)
        roll_window = 60

        rolling_mean = df["return"].rolling(roll_window).mean()
        rolling_std = df["return"].rolling(roll_window).std()

        df["macd_buy"] = (df["macd"] > df["macd_signal"]) & (
            df["macd"].shift(1) <= df["macd_signal"].shift(1)
        )

        df["macd_sell"] = (df["macd"] < df["macd_signal"]) & (
            df["macd"].shift(1) >= df["macd_signal"].shift(1)
        )

        df["rsi_buy"] = df["rsi_14"] < 30
        df["rsi_sell"] = df["rsi_14"] > 70

        cols = []
        for group in enabled_groups:
            cols.extend(FEATURE_GROUPS.get(group, []))

        # Keep only columns that actually exist
        cols = [c for c in cols if c in df.columns]

        if not cols:
            tqdm.write(f"Skipping {symbol}: no plottable columns")
            continue

        # --- 3️⃣ Plotting ---
        fig, axes = plt.subplots(len(cols), 1, figsize=(18, 5 * len(cols)), sharex=True)

        if len(cols) == 1:
            axes = [axes]

        for ax, col in zip(axes, cols):
            df[col].plot(ax=ax)
            ax.set_title(f"{symbol} — {col}")

        axes[-1].set_xlabel("Date")
        plt.tight_layout()

        out_path = figures_dir / f"{symbol}.png"
        plt.savefig(out_path, dpi=150)
        plt.close()

        tqdm.write(f"Saved {out_path}")
        # ===============================
        # D️⃣ Return distribution (histogram)
        # ===============================

        returns = df["return"].dropna()

        if len(returns) > 0:
            plt.figure(figsize=(10, 6))
            plt.hist(returns, bins=100, density=True, alpha=0.7)
            plt.axvline(returns.mean(), linestyle="--", linewidth=2)
            plt.title(f"{symbol} — Return Distribution")
            plt.xlabel("Return")
            plt.ylabel("Density")

            hist_path = figures_dir / f"{symbol}_returns_hist.png"
            plt.tight_layout()
            plt.savefig(hist_path, dpi=150)
            plt.close()

            tqdm.write(f"Saved {hist_path}")

        if rolling_mean.notna().sum() > 0:
            fig, axes = plt.subplots(2, 1, figsize=(18, 8), sharex=True)

            rolling_mean.plot(ax=axes[0])
            axes[0].set_title(f"{symbol} — {roll_window}D Rolling Mean Return")
            axes[0].axhline(0, linestyle="--", linewidth=1)

            rolling_std.plot(ax=axes[1])
            axes[1].set_title(f"{symbol} — {roll_window}D Rolling Std (Volatility)")

            axes[1].set_xlabel("Date")
            plt.tight_layout()

            roll_path = figures_dir / f"{symbol}_rolling_stats.png"
            plt.savefig(roll_path, dpi=150)
            plt.close()

            tqdm.write(f"Saved {roll_path}")

            fig, axes = plt.subplots(
                3,
                1,
                figsize=(18, 12),
                sharex=True,
                gridspec_kw={"height_ratios": [3, 1.5, 1.5]},
            )

            # -------------------------------
            # Price + signals
            # -------------------------------
            axes[0].plot(df.index, df["Close"], label="Close", color="black")

            axes[0].scatter(
                df.index[df["macd_buy"]],
                df.loc[df["macd_buy"], "Close"],
                marker="^",
                color="green",
                label="MACD Buy",
            )

            axes[0].scatter(
                df.index[df["macd_sell"]],
                df.loc[df["macd_sell"], "Close"],
                marker="v",
                color="red",
                label="MACD Sell",
            )

            axes[0].set_title(f"{symbol} — Price + Signals")
            axes[0].legend()

            # -------------------------------
            # MACD
            # -------------------------------
            axes[1].plot(df.index, df["macd"], label="MACD")
            axes[1].plot(df.index, df["macd_signal"], label="Signal")
            axes[1].axhline(0, linestyle="--", linewidth=1)
            axes[1].legend()

            # -------------------------------
            # RSI
            # -------------------------------
            axes[2].plot(df.index, df["rsi_14"], label="RSI", color="purple")
            axes[2].axhline(30, linestyle="--", color="green")
            axes[2].axhline(70, linestyle="--", color="red")
            axes[2].set_ylim(0, 100)
            axes[2].legend()

            axes[2].set_xlabel("Date")
            plt.tight_layout()

            signal_path = figures_dir / f"{symbol}_signals.png"
            plt.savefig(signal_path, dpi=150)
            plt.close()

            tqdm.write(f"Saved {signal_path}")
