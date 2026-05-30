from data.engine import build_db, get_session
from data.repositories.asset_repo import upsert_asset

engine, SessionFactory = build_db()

ASSETS = [
    # symbol        name                        type
    ("AAPL", "Apple Inc.", "stock"),
    ("MSFT", "Microsoft", "stock"),
    ("GOOGL", "Alphabet Inc.", "stock"),
    ("BAC", "Bank of America", "stock"),
    ("WFC", "Wells Fargo", "stock"),
    ("C", "Citigroup", "stock"),
    ("INTC", "Intel", "stock"),
    ("DIS", "Walt Disney", "stock"),
    ("ABT", "Abbott Laboratories", "stock"),
    ("WMT", "Walmart", "stock"),
    ("BTC-USD", "Bitcoin", "crypto"),
    ("ETH-USD", "Ethereum", "crypto"),
    ("XRP-USD", "XRP", "crypto"),
    ("GC=F", "Gold Futures", "ETF"),
    ("SI=F", "Silver Futures", "ETF"),
    ("CL=F", "Crude Oil Futures", "ETF"),
    ("EURUSD=X", "Euro / US Dollar", "bond"),
    ("GBPUSD=X", "British Pound / USD", "bond"),
    ("JPY=X", "USD / Japanese Yen", "bond"),
    ("^TNX", "10-Year Treasury Yield", "bond"),
    ("^TYX", "30-Year Treasury Yield", "bond"),
    ("^IRX", "13-Week Treasury Bill", "bond"),
    ("MCD", "McDonald's", "stock"),

]

with get_session(SessionFactory) as session:
    for symbol, name, asset_type in ASSETS:
        upsert_asset(session, symbol=symbol, name=name, asset_type=asset_type)
        print(f"✅ {symbol} — {name} ({asset_type})")

print("🎉 Asset catalog loaded!")
