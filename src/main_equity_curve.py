from portfolio.equity_curve import calculate_portfolio_equity_curve
from data.engine import build_db, get_session
from data.repositories.client_repo import get_all_clients
from data.repositories.portfolio_repo import get_portfolios_by_client
import pandas as pd
from data.repositories.portfolio_repo import save_equity_curve


# ❗ FIX: SessionFactory must come from build_db()
engine, SessionFactory = build_db()


with get_session(SessionFactory) as session:

    clients = get_all_clients(session)

    for client in clients:
        portfolios = get_portfolios_by_client(session, client.client_id)

        for portfolio in portfolios:

            df = calculate_portfolio_equity_curve(
                session, portfolio.portfolio_id, portfolio.start_date
            )

            print("\n---")
            print(client.name, portfolio.name)
            print(df)

            if df.empty:
                print("EMPTY DF")
                continue

            df = df.sort_values("Date")

            save_equity_curve(session, portfolio.portfolio_id, df)

            start_value = df["total_value"].iloc[0]
            end_value = df["total_value"].iloc[-1]

            days = (
                pd.to_datetime(df["Date"].iloc[-1]) - pd.to_datetime(df["Date"].iloc[0])
            ).days

            years = days / 365.25

            if years <= 0 or start_value == 0:
                print("Skipping CAGR (invalid data)")
                continue

            cagr = (end_value / start_value) ** (1 / years) - 1

            print(f"{client.name} - {portfolio.name} CAGR: {cagr:.2%}")
