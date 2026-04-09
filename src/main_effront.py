"""
efficient_frontier_step.py
--------------------------
Step 4b of the quant-project pipeline: compute the Efficient Frontier and
save the resulting optimal portfolio weights to a JSON file.

What this script does
---------------------
1. Loads the pre-filtered feature data from a pickle file produced by the
   feature-filtering step (filter_features.py).
2. Reads the efficient_frontier section of analysis_config.yaml to check
   whether the step is enabled and to obtain solver parameters.
3. If enabled, calls compute_and_save_efficient_frontier() which runs mean-
   variance optimisation and returns the optimal ticker weights.
4. Writes those weights to reports/ef_weights.json so downstream steps
   (portfolio rebalancing, report generation) can consume them without
   rerunning the optimisation.

Why pickle for filtered_data?
------------------------------
Pickle preserves the exact Python objects (DataFrames with DatetimeIndex,
dtypes, etc.) produced by the filtering step.  Saving to pickle avoids
re-running the expensive filtering logic every time this step is executed.

Expected analysis_config.yaml shape
-------------------------------------
    efficient_frontier:
        enabled: true
        method: "max_sharpe"          # or "min_volatility"
        risk_free_rate: 0.04
        n_portfolios: 10000

Output
------
    reports/ef_weights.json
        {
            "AAPL": 0.312,
            "MSFT": 0.241,
            ...
        }

Author : Eduardo Cervantes Alarcón
"""

import json
import os
from datetime import datetime  # imported but reserved for future logging

import yaml
import pickle

from utils.helpers import ensure_folder
from utils.efficient_frontier_utils import compute_and_save_efficient_frontier


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """
    Execute Step 4b: Efficient Frontier computation and weight export.
    """

    # ------------------------------------------------------------------
    # Load filtered data from pickle
    # ------------------------------------------------------------------
    # filtered_data is a dict {ticker: DataFrame} where each DataFrame
    # contains OHLCV columns plus engineered features, already sliced to the
    # analysis date window by filter_features.py.
    # "rb" = read binary, required for pickle files.
    pkl_path = (
        r"C:\Users\eduar\Projects\Python\quant_project\data\interim\filtered_data.pkl"
    )
    with open(pkl_path, "rb") as f:
        filtered_data: dict = pickle.load(f)

    # ------------------------------------------------------------------
    # Load analysis config
    # ------------------------------------------------------------------
    with open("config/analysis_config.yaml") as f:
        analysis_cfg = yaml.safe_load(f)

    # Extract only the efficient_frontier sub-section.
    # .get("efficient_frontier", {}) returns an empty dict if the key is
    # missing, so every subsequent .get() on ef_cfg has a safe fallback.
    ef_cfg: dict = analysis_cfg.get("efficient_frontier", {})

    # Initialise output variables to None so the JSON save block below can
    # detect whether the optimisation actually ran.
    ef_weights = None
    returns_df = None

    # ------------------------------------------------------------------
    # Step 4b — Compute Efficient Frontier (conditional)
    # ------------------------------------------------------------------
    # The step is guarded by the "enabled" flag so the pipeline can skip
    # the (potentially slow) optimisation by setting enabled: false in the
    # YAML without changing any code.
    if ef_cfg.get("enabled", False):
        print("\nStep 4b: Computing Efficient Frontier...")

        # compute_and_save_efficient_frontier() runs mean-variance
        # optimisation (e.g. max Sharpe or min volatility) over the returns
        # derived from filtered_data and returns:
        #   ef_weights : dict {ticker: weight}  — optimal allocation, sums to 1
        #   returns_df : DataFrame              — daily returns used internally
        ef_weights, returns_df = compute_and_save_efficient_frontier(
            filtered_data, ef_cfg
        )

    # ------------------------------------------------------------------
    # Build the output path
    # ------------------------------------------------------------------
    # os.path.dirname(__file__) gives the directory containing this script.
    # Joining with ".." navigates one level up to the project root, then
    # into the reports/ folder — so the path works regardless of the current
    # working directory when the script is executed.
    reports_dir = os.path.join(os.path.dirname(__file__), "..", "reports")

    # exist_ok=True means no error is raised if the folder already exists.
    os.makedirs(reports_dir, exist_ok=True)

    json_path = os.path.join(reports_dir, "ef_weights.json")

    # ------------------------------------------------------------------
    # Save weights to JSON
    # ------------------------------------------------------------------
    # ef_weights values may be numpy float64 scalars, which the standard
    # json module cannot serialise.  Wrapping each value in float() converts
    # them to plain Python floats before writing.
    # indent=4 produces a human-readable file that is easy to inspect and
    # version-control.
    with open(json_path, "w") as f:
        json.dump({k: float(v) for k, v in ef_weights.items()}, f, indent=4)

    print(f"Efficient frontier weights saved to {json_path}")


if __name__ == "__main__":
    main()
