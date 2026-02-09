import pandas as pd

class DataPreprocessor:
    def clean(self, df):
        df = df.copy()
        df.columns = [c.lower().replace(' ', '_') for c in df.columns]
        df = df.dropna()
        return df
