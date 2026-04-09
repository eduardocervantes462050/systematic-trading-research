"""
filter_features.py
------------------
Loads processed feature CSV files, applies a date range filter and an optional
ticker whitelist defined in analysis_config.yaml, and saves the filtered results
back to the interim data folder.

Configuration files used
------------------------
- config/project_config.json   : folder paths (raw, interim, reports, backtests)
- config/analysis_config.yaml  : analysis window (start_date, end_date) and
                                  optional ticker list

Output
------
For every ticker that passes the filter, writes:
    <INTERIM_DATA_FOLDER>/<ticker>_features_filtered.csv

Author : Eduardo Cervantes Alarcón
"""

import yaml
import os
import pandas as pd
import json


# ---------------------------------------------------------------------------
# Global config — loaded once at module level so every function can access it
# ---------------------------------------------------------------------------

# Absolute path to the project config.  Using a raw string avoids issues with
# backslashes on Windows.
_CONFIG_PATH = (
    r"C:\Users\eduar\Projects\Python\quant_project\config\project_config.json"
)

with open(_CONFIG_PATH, "r") as f:
    _config = json.load(f)

# Folder where feature CSVs produced by FeatureEngineer are stored.
# Expected files: <ticker>_features.csv
INTERIM_DATA_FOLDER: str = _config["folders"]["interim_data"]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """
    Entry point for the feature-filtering pipeline step.

    Steps
    -----
    1. Read analysis_config.yaml to get the desired date window and optional
       ticker whitelist.
    2. Scan INTERIM_DATA_FOLDER for files ending in ``_features.csv``.
    3. For each file, extract the ticker name, optionally skip it if it is not
       in the whitelist, load the CSV, and slice it to the requested date range.
    4. Write the filtered DataFrame back to disk as
       ``<ticker>_features_filtered.csv`` in the same folder.
    """

    # ------------------------------------------------------------------
    # Step 1 — Load analysis config
    # ------------------------------------------------------------------
    with open("config/analysis_config.yaml") as f:
        analysis_cfg = yaml.safe_load(f)

    # pd.to_datetime converts the string "2000-01-01" to a Timestamp so it can
    # be compared directly with the DataFrame's DatetimeIndex.
    # .get(key, default) returns the default if the key is missing in the YAML.
    ANALYSIS_START = pd.to_datetime(analysis_cfg.get("start_date", "2000-01-01"))
    ANALYSIS_END = pd.to_datetime(analysis_cfg.get("end_date", "2025-12-31"))

    # Optional list of tickers to process.  When absent (None), every ticker
    # found on disk is included.
    ANALYSIS_TICKERS = analysis_cfg.get("tickers", None)

    # ------------------------------------------------------------------
    # Step 2 — Discover feature files
    # ------------------------------------------------------------------
    filtered_data: dict[str, pd.DataFrame] = {}

    # os.listdir returns plain filenames (no directory prefix).
    # The list comprehension keeps only files whose names end with the expected
    # suffix, ignoring any other CSVs or subdirectories in the folder.
    features_files = [
        f for f in os.listdir(INTERIM_DATA_FOLDER) if f.endswith("_features.csv")
    ]

    # ------------------------------------------------------------------
    # Step 3 — Load, filter by ticker whitelist, filter by date
    # ------------------------------------------------------------------
    for file in features_files:

        # Extract the ticker symbol from the filename.
        # os.path.basename is defensive — the list already contains bare names,
        # but using it makes the code safe if the list ever contains full paths.
        # .split("_")[0] takes everything before the first underscore, e.g.
        # "AAPL_features.csv" → "AAPL".
        ticker = os.path.basename(file).split("_")[0]

        # Skip this file if the user supplied a whitelist and this ticker is
        # not on it.  "if ANALYSIS_TICKERS" is False when the value is None or
        # an empty list, so the skip logic is inactive in both those cases.
        if ANALYSIS_TICKERS and ticker not in ANALYSIS_TICKERS:
            continue

        # Read the CSV.
        # - index_col=0   : the first column (dates written by to_csv) becomes
        #                   the row index.
        # - parse_dates=True : pandas attempts to parse the index as dates,
        #                      giving us a DatetimeIndex needed for .loc slicing.
        df = pd.read_csv(
            os.path.join(INTERIM_DATA_FOLDER, file),
            index_col=0,
            parse_dates=True,
        )

        # Boolean mask: keep only rows whose index falls within [START, END].
        # Using .loc with boolean arrays is the standard pandas pattern for
        # date-range slicing on a DatetimeIndex.
        df_filtered = df.loc[(df.index >= ANALYSIS_START) & (df.index <= ANALYSIS_END)]

        # Store the filtered DataFrame in the results dict, keyed by ticker.
        filtered_data[ticker] = df_filtered

        # ------------------------------------------------------------------
        # Step 4 — Persist filtered data
        # Note: this inner loop re-iterates filtered_data on every outer
        # iteration, which means earlier tickers are re-written multiple times.
        # This is harmless but inefficient; moving the save loop outside the
        # outer for-loop would be cleaner.
        # ------------------------------------------------------------------
        for ticker, df_filtered in filtered_data.items():
            df_filtered.to_csv(
                os.path.join(
                    INTERIM_DATA_FOLDER,
                    f"{ticker}_features_filtered.csv",
                )
            )


if __name__ == "__main__":
    main()
