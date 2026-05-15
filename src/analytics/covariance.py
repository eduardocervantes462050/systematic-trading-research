from pypfopt import risk_models


def compute_covariance_matrix(price_df):

    return risk_models.sample_cov(
        price_df
    )