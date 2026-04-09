import yaml
import os
import pandas as pd
import json


path = r"C:\Users\eduar\Projects\Python\quant_project\config\project_config.json"

with open(path, "r") as f:
    config = json.load(f)

# Access folders
INTERIM_DATA_FOLDER = config["folders"]["interim_data"]


def main():
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


if __name__ == "__main__":
    main()
