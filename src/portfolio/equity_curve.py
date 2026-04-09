import pandas as pd


def calculate_portfolio_equity_curve(client, price_data):
    dates = price_data[next(iter(price_data))].index  # assume all have same dates
    equity_curve = []

    for date in dates:
        total_value = client.cash
        for ticker, shares in client.positions.items():
            if ticker in price_data:
                total_value += shares * price_data[ticker].loc[date, "Close"]
        equity_curve.append({"Date": date, "total_value": total_value})

    return pd.DataFrame(equity_curve)
