import pandas as pd
from datetime import datetime


class Portfolio:
    def __init__(self, name, initial_capital, initial_positions=None):
        """
        A single portfolio for a client
        initial_positions: dict {ticker: shares}
        """
        self.name = name
        self.total_capital = initial_capital
        self.positions = (
            {}
        )  # {ticker: {"shares": int, "price": float, "capital": float}}
        self.history = pd.DataFrame(
            columns=["date", "ticker", "action", "shares", "price", "capital"]
        )
        if initial_positions:
            for ticker, shares in initial_positions.items():
                self.positions[ticker] = {"shares": shares, "price": 0, "capital": 0}

    def update_market_prices(self, market_prices):
        """Update prices and total capital"""
        for ticker, pos in self.positions.items():
            if ticker in market_prices:
                pos["price"] = market_prices[ticker]
                pos["capital"] = pos["shares"] * pos["price"]
        self.total_capital = sum(pos["capital"] for pos in self.positions.values())

    def input_trade(self, ticker, shares, price, action):
        """Record a trade and update positions"""
        if ticker not in self.positions:
            self.positions[ticker] = {"shares": 0, "price": price, "capital": 0}
        if action == "buy":
            self.positions[ticker]["shares"] += shares
        elif action == "sell":
            self.positions[ticker]["shares"] -= shares
            if self.positions[ticker]["shares"] < 0:
                raise ValueError(f"Cannot sell more shares than owned for {ticker}")
        self.positions[ticker]["price"] = price
        self.positions[ticker]["capital"] = self.positions[ticker]["shares"] * price
        self.total_capital = sum(pos["capital"] for pos in self.positions.values())
        self.history = pd.concat(
            [
                self.history,
                pd.DataFrame(
                    [
                        {
                            "date": datetime.now(),
                            "ticker": ticker,
                            "action": action,
                            "shares": shares,
                            "price": price,
                            "capital": shares * price,
                        }
                    ]
                ),
            ],
            ignore_index=True,
        )

    def get_current_weights(self):
        """Return current weights per asset"""
        self.update_market_prices(
            {t: pos["price"] for t, pos in self.positions.items()}
        )
        return {
            ticker: pos["capital"] / self.total_capital
            for ticker, pos in self.positions.items()
        }

    def rebalance_to_target(self, target_weights, market_prices):
        """
        target_weights: {ticker: weight} sum to 1
        Returns dict of shares to buy (+) or sell (-)
        """
        self.update_market_prices(market_prices)
        trades = {}
        for ticker, target_w in target_weights.items():
            target_capital = self.total_capital * target_w
            current_capital = self.positions.get(ticker, {}).get("capital", 0)
            delta_capital = target_capital - current_capital
            share_price = market_prices[ticker]
            delta_shares = int(delta_capital / share_price)
            trades[ticker] = delta_shares
        return trades

    def get_positions_df(self):
        return pd.DataFrame(self.positions).T

    def save_history(self, filepath):
        self.history.to_csv(filepath, index=False)


class MultiClientPortfolioTracker:
    def __init__(self):
        self.clients = {}  # {client_name: Portfolio instance}

    def get_all_clients(self):
        """Return a list of all client names."""
        return list(self.clients.keys())

    def add_client(self, name, initial_capital, initial_positions=None):
        self.clients[name] = Portfolio(name, initial_capital, initial_positions)

    def get_client(self, name):
        return self.clients.get(name)

    def update_all_market_prices(self, market_prices):
        for client in self.clients.values():
            client.update_market_prices(market_prices)

    def rebalance_client(self, name, target_weights, market_prices):
        client = self.get_client(name)
        if client:
            return client.rebalance_to_target(target_weights, market_prices)
        else:
            raise ValueError(f"No client named {name}")

    def save_all_histories(self, folder="reports/portfolios"):
        import os

        os.makedirs(folder, exist_ok=True)
        for client_name, client in self.clients.items():
            client.save_history(f"{folder}/{client_name}_history.csv")
