import pandas as pd
import matplotlib.pyplot as plt
from sqlalchemy import select

from data.database import PortfolioEquityCurve


def get_equity_curve(session, portfolio_id):
    """
    Load equity curve from DB into a DataFrame.
    """

    rows = (
        session.query(PortfolioEquityCurve)
        .filter(PortfolioEquityCurve.portfolio_id == portfolio_id)
        .order_by(PortfolioEquityCurve.date)
        .all()
    )

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(
        [
            {
                "date": r.date,
                "total_value": float(r.total_value),
            }
            for r in rows
        ]
    )

    return df


def plot_equity_curve(session, portfolio_id, portfolio_name="Portfolio"):
    """
    Plot equity curve for one portfolio.
    """

    df = get_equity_curve(session, portfolio_id)

    if df.empty:
        print(f"No equity curve found for {portfolio_name}")
        return

    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")

    plt.figure()
    plt.plot(df["date"], df["total_value"])
    plt.title(f"Equity Curve - {portfolio_name}")
    plt.xlabel("Date")
    plt.ylabel("Portfolio Value")
    plt.grid(True)
    plt.tight_layout()
    plt.show()

    def plot_multiple_equity_curves(session, portfolios):
        """
        portfolios = list of (portfolio_id, portfolio_name)
        """

        plt.figure()

        for portfolio_id, name in portfolios:
            df = get_equity_curve(session, portfolio_id)

            if df.empty:
                continue

            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date")

            plt.plot(df["date"], df["total_value"], label=name)

        plt.title("Equity Curve Comparison")
        plt.xlabel("Date")
        plt.ylabel("Portfolio Value")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.show()
