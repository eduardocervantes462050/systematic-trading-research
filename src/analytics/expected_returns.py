from pypfopt import expected_returns


def compute_expected_returns(price_df):
    price_df = price_df.astype(float)
    return expected_returns.mean_historical_return(
        price_df
    )