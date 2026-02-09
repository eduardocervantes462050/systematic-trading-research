def generate_signals(df):
    df = df.copy()
    df["macd_up"] = (df["macd_hist"] > 0) & (df["macd_hist"].shift(1) <= 0)
    df["macd_down"] = (df["macd_hist"] < 0) & (df["macd_hist"].shift(1) >= 0)

    df["signal"] = 0
    df.loc[(df["rsi_14"] < 30) & df["macd_up"], "signal"] = 1
    df.loc[(df["rsi_14"] > 70) | df["macd_down"], "signal"] = -1

    return df
