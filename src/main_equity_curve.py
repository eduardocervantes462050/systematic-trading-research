from portfolio.equity_curve import calculate_portfolio_equity_curve
from data.database import (
    build_db,
    get_all_clients,
    get_portfolios_by_client,
    save_equity_curve,
    get_session,
)
import pandas as pd


# ❗ FIX: SessionFactory must come from build_db()
engine, SessionFactory = build_db()


with get_session(SessionFactory) as session:

    clients = get_all_clients(session)

    for client in clients:
        portfolios = get_portfolios_by_client(session, client.client_id)

        for portfolio in portfolios:

            # 1. Calculate equity curve from DB
            df = calculate_portfolio_equity_curve(session, portfolio.portfolio_id)
            print(df)

            if df.empty:
                continue

            # 2. Save to DB (persist results)
            save_equity_curve(session, portfolio.portfolio_id, df)

            # 3. Compute CAGR
            start_value = df["total_value"].iloc[0]
            end_value = df["total_value"].iloc[-1]

            days = (
                pd.to_datetime(df["Date"].iloc[-1]) - pd.to_datetime(df["Date"].iloc[0])
            ).days

            years = days / 365.25

            cagr = (end_value / start_value) ** (1 / years) - 1

            print(f"{client.name} - {portfolio.name} CAGR: {cagr:.2%}")

print("All portfolio equity curves saved.")
