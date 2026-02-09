import pandas as pd


def load_and_clean_price_csv(path: str) -> pd.DataFrame:
    """
    Cleans malformed price CSVs by:
    - Finding the row where 'Date' starts
    - Dropping all rows above it
    - Enforcing a standard OHLCV schema
    """

    raw = pd.read_csv(path, header=None)

    # Find row where first column is 'Date'
    date_row_idx = raw.index[raw.iloc[:, 0] == "Date"]

    if len(date_row_idx) == 0:
        raise ValueError(f"Cannot find Date row in {path}")

    start_idx = date_row_idx[0] + 1

    # Slice actual data
    df = raw.iloc[start_idx:].copy()

    # Enforce standard column names
    expected_cols = ["Date", "Close", "High", "Low", "Open", "Volume"]

    if df.shape[1] < len(expected_cols):
        raise ValueError(
            f"{path}: Expected at least {len(expected_cols)} columns, "
            f"found {df.shape[1]}"
        )

    df = df.iloc[:, : len(expected_cols)]
    df.columns = expected_cols

    # Parse Date
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.set_index("Date").sort_index()

    # Convert numeric columns
    for col in ["Close", "High", "Low", "Open", "Volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Drop invalid rows
    df = df.dropna(subset=["Close"])

    return df
