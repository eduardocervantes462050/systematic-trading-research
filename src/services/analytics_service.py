from sqlalchemy.orm import Session

from services.market_data_service import load_portfolio_price_matrix
from analytics.expected_returns import compute_expected_returns
from analytics.covariance import compute_covariance_matrix


def generate_portfolio_analytics(
    session: Session,
    assets: list[str],
):
    """
    PURE analytics layer:

    prices → mu + covariance
    """

    # 1. Load price matrix
    price_df = load_portfolio_price_matrix(
        session=session,
        assets=assets,
    )
    print(price_df)

    # 2. Expected returns
    mu = compute_expected_returns(price_df)


    # 3. Covariance matrix
    cov = compute_covariance_matrix(price_df)

    return mu, cov