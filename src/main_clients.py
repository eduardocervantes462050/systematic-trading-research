from datetime import datetime

from data.database import (
    build_db,
    get_session,
    create_client,
    create_portfolio,
    upsert_holding,
    get_asset_by_symbol,
    get_portfolios_by_client,
    get_client_by_email,
)

engine, SessionFactory = build_db()

with get_session(SessionFactory) as session:
    # ── CLIENT ──────────────────────────────────────
    name = input("Client name: ")
    email = input("Client email: ")
    phone = input("Client phone (optional, press Enter to skip): ")
    client = create_client(session, name=name, email=email, phone=phone or None)
    print(f"✅ Client '{name}' added successfully!")

    # ── PORTFOLIO ────────────────────────────────────
    portfolio_name = input("Portfolio name: ")
    risk = input("Risk level (low / medium / high): ")
    start_date = input("Start date (YYYY-MM-DD, optional): ")
    if start_date:
        start_date = datetime.strptime(start_date, "%Y-%m-%d")

    portfolio = create_portfolio(
        session,
        client_id=client.client_id,
        name=portfolio_name,
        risk_level=risk,
        start_date=start_date,
    )
    print(f"✅ Portfolio '{portfolio_name}' added successfully!")

    # ── HOLDINGS ─────────────────────────────────────
    print("\nAdd holdings (type 'done' when finished)")
    while True:
        symbol = input("Ticker symbol (e.g. AAPL): ").strip().upper()
        if symbol == "DONE":
            break

        # fetch asset id from DB
        asset = get_asset_by_symbol(session, symbol)
        if asset is None:
            print(
                f"❌ '{symbol}' not found in asset catalog. Run setup_assets.py first."
            )
            continue

        quantity = float(input(f"Quantity of {symbol}: "))
        avg_price = float(input(f"Average buy price of {symbol}: "))

        upsert_holding(
            session,
            portfolio_id=portfolio.portfolio_id,
            asset_id=asset.asset_id,
            quantity=quantity,
            avg_price=avg_price,
        )
        print(f"✅ {symbol} — {quantity} units @ ${avg_price} added!")

print("🎉 Client, portfolio and holdings saved!")
