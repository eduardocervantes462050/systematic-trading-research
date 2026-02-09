import pandas as pd

class Backtester:
    def __init__(self, portfolio):
        self.portfolio = portfolio

    def run(self, df, signals):
        df = df.copy()
        df["signal"] = signals

        for i in range(1, len(df)):
            today = df.index[i]
            price = df["close"].iloc[i]
            signal = df["signal"].iloc[i]

            if signal == 1:
                self.portfolio.buy(price)
            elif signal == -1:
                self.portfolio.sell(price)

            df.loc[today, "portfolio_value"] = self.portfolio.value(price)

        return df
