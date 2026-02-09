import pandas as pd
import yfinance as yf
from yahoofinancials import YahooFinancials
import time
import pandas as pd
import quandl
import requests


class DataFetcher:
    def get_price_data(self, tickers, start, end, batch_size=5, retries=3, delay=5):
        """
        Fetch price data for multiple tickers with batching to avoid rate limits.

        tickers: list of ticker symbols
        start, end: strings "YYYY-MM-DD"
        batch_size: number of tickers per download
        retries: number of retries for failed batches
        delay: seconds to wait between retries
        """
        if isinstance(tickers, str):
            tickers = [tickers]

        all_data = {}

        # Split tickers into batches
        for i in range(0, len(tickers), batch_size):
            batch = tickers[i : i + batch_size]
            attempt = 0
            while attempt < retries:
                try:
                    print(f"Fetching batch: {batch}")
                    df = yf.download(
                        batch, start=start, end=end, auto_adjust=True, progress=False
                    )
                    # Separate batch data into individual tickers
                    if len(batch) == 1:
                        all_data[batch[0]] = df
                    else:
                        # yfinance returns multi-level columns when batch>1
                        for ticker in batch:
                            all_data[ticker] = df.xs(ticker, axis=1, level=1)
                    break  # success, exit retry loop
                except Exception as e:
                    attempt += 1
                    print(f"Attempt {attempt} failed for {batch}: {e}")
                    time.sleep(delay)
            else:
                # If all retries fail
                print(
                    f"Failed to fetch data for batch {batch} after {retries} attempts"
                )
                for ticker in batch:
                    all_data[ticker] = pd.DataFrame()  # empty DF as fallback

        return all_data

    def get_multiple_tickers(self, tickers, start, end):
        all_data = {}

        for ticker in tickers:
            yahoo_financials = YahooFinancials(ticker)

            all_data[ticker] = {
                "cash_flow_annual": yahoo_financials.get_financial_stmts(
                    "annual", "cash"
                ),
                "ebit": yahoo_financials.get_ebit(),
                "price_data": yahoo_financials.get_stock_price_data(),
                "historical_prices": yahoo_financials.get_historical_price_data(
                    start, end, "daily"
                ),
            }

        return all_data

    def get_fred_data(
        self,
        api_key,
        series_id,
        url,
    ):
        params = {"series_id": series_id, "api_key": api_key, "file_type": "json"}
        response = requests.get(url, params=params)
        data = response.json()
        df_cpi = pd.DataFrame(data["observations"])
        df_cpi["date"] = pd.to_datetime(df_cpi["date"])
        df_cpi["value"] = pd.to_numeric(df_cpi["value"], errors="coerce")
        df_cpi.set_index("date", inplace=True)
        df_cpi.rename(columns={"value": "Close"}, inplace=True)
        return df_cpi
