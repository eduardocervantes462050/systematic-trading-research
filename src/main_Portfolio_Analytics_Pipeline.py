from data.engine import build_db, get_session

from services.analytics_service import (
    generate_portfolio_analytics,
)

from data.repositories.portfolio_repo import (
    get_portfolio_id_by_name,
)

from services.optimization_service import (
    load_portfolio_assets,
)


def main():

    engine, SessionFactory = build_db()

    portfolio_name = "Global Multi-Asset Growth Portfolio"

    with get_session(SessionFactory) as session:

        portfolio_id = get_portfolio_id_by_name(
            session,
            portfolio_name,
        )

        assets = load_portfolio_assets(
            session,
            portfolio_id,
        )

        mu, cov = generate_portfolio_analytics(
            session=session,
            assets=assets,
        )

        print("\nExpected Returns:")
        print(mu)

        print("\nCovariance Matrix:")
        print(cov)


if __name__ == "__main__":
    main()