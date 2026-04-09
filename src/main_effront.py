import json
import os
from datetime import datetime
from utils.helpers import ensure_folder
from utils.efficient_frontier_utils import compute_and_save_efficient_frontier
import yaml
import pickle


def main():
    # -------------------------------

    # Step 4b: Efficient Frontier
    # -------------------------------
    # Load config
    pkl_path = (
        r"C:\Users\eduar\Projects\Python\quant_project\data\interim\filtered_data.pkl"
    )
    with open(pkl_path, "rb") as f:
        filtered_data = pickle.load(f)
    with open("config/analysis_config.yaml") as f:
        analysis_cfg = yaml.safe_load(f)
    ef_cfg = analysis_cfg.get("efficient_frontier", {})
    ef_weights = None
    returns_df = None
    if ef_cfg.get("enabled", False):
        print("\nStep 4b: Computing Efficient Frontier...")
        ef_weights, returns_df = compute_and_save_efficient_frontier(
            filtered_data, ef_cfg
        )

    # Build path relative to main.py
    reports_dir = os.path.join(os.path.dirname(__file__), "..", "reports")
    os.makedirs(reports_dir, exist_ok=True)

    # File path
    json_path = os.path.join(reports_dir, "ef_weights.json")

    # Save ef_weights dict
    with open(json_path, "w") as f:
        json.dump({k: float(v) for k, v in ef_weights.items()}, f, indent=4)

    print(f"Efficient frontier weights saved to {json_path}")


if __name__ == "__main__":
    main()
