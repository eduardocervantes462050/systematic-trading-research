from sklearn.ensemble import RandomForestClassifier
import numpy as np

class MLModel:
    def __init__(self):
        self.model = RandomForestClassifier()

    def train(self, df):
        df = df.copy()
        X = df[["returns", "sma_20", "sma_50", "volatility"]].values[1:]
        y = (df["returns"].shift(-1) > 0).astype(int).values[1:]
        self.model.fit(X, y)

    def predict(self, df):
        X = df[["returns", "sma_20", "sma_50", "volatility"]].values
        return self.model.predict(X)
