import os
import logging
import pandas as pd
import numpy as np
from typing import Dict
from utils.cleandata import load_and_clean_price_csv


logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)


class FeatureEngineer:
    """
    Production-grade feature engineering pipeline for financial time series.
    """

    REQUIRED_COLUMNS = {"Close"}

    def add_features(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        # Validate columns
        missing = self.REQUIRED_COLUMNS - set(df.columns)
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        # Ensure correct time order
        df = df.sort_index()

        # ======================
        # 1️⃣ Returns
        # ======================
        df["return"] = df["Close"].pct_change(fill_method=None)
        df["log_return"] = np.log(df["Close"]).diff()

        # ======================
        # 2️⃣ Rolling Volatility
        # ======================
        df["vol_20"] = df["return"].rolling(window=20).std()
        df["vol_60"] = df["return"].rolling(window=60).std()

        # ======================
        # 3️⃣ RSI (14-day)
        # ======================
        delta = df["Close"].diff()

        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)

        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()

        rs = avg_gain / avg_loss
        df["rsi_14"] = 100 - (100 / (1 + rs))

        # ======================
        # 4️⃣ MACD
        # ======================
        ema_12 = df["Close"].ewm(span=12, adjust=False).mean()
        ema_26 = df["Close"].ewm(span=26, adjust=False).mean()

        df["macd"] = ema_12 - ema_26
        df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()
        df["macd_hist"] = df["macd"] - df["macd_signal"]

        df["cum_return"] = (1 + df["return"]).cumprod()
        df["rolling_max"] = df["cum_return"].cummax()
        df["drawdown"] = df["cum_return"] / df["rolling_max"] - 1

        # ======================
        # Final cleanup
        # ======================
        df = df.dropna()

        return df

    def process_csv_folder(self, folder: str) -> Dict[str, pd.DataFrame]:
        if not os.path.isdir(folder):
            raise FileNotFoundError(f"Folder not found: {folder}")

        results: Dict[str, pd.DataFrame] = {}

        for file in os.listdir(folder):
            if not file.lower().endswith(".csv"):
                continue

            ticker = file.replace(".csv", "")
            path = os.path.join(folder, file)

            try:
                df = load_and_clean_price_csv(path)
                print(df)

                if df.empty:
                    logger.warning(f"{ticker}: empty CSV, skipping.")
                    continue

                df_features = self.add_features(df)
                results[ticker] = df_features

                logger.info(
                    f"{ticker}: processed {len(df_features)} rows, "
                    f"{len(df_features.columns)} features"
                )

            except Exception as e:
                logger.error(f"{ticker}: failed — {e}")

        return results
