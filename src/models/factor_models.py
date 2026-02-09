class FactorModel:
    def generate_signals(self, df):
        df = df.copy()
        signals = (df["sma_20"] > df["sma_50"]).astype(int)
        signals[signals == 0] = -1
        return signals
