import yfinance as yf

print(yf.__version__)
df = yf.download("AAPL", start="2024-01-01")
print(df)
