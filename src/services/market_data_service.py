from sqlalchemy.orm import Session

from data.repositories.price_repo import (
    get_price_history,
)


def load_portfolio_price_matrix(
    session: Session,
    assets: list[str],
):
    """
    Service wrapper around repository.
    """

    return get_price_history(
        session=session,
        assets=assets,
    )