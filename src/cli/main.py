import argparse

from data.engine import build_db, get_session
from services.optimization_service import run_optimization
from cli.strategy_factory import get_strategy
from data.repositories.portfolio_repo import get_portfolio_id_by_name


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--portfolio_name", required=True)
    parser.add_argument("--strategy", required=True)
    parser.add_argument("--method", required=True)

    args = parser.parse_args()

    engine, SessionFactory = build_db()

    with get_session(SessionFactory) as session:

        portfolio_id = get_portfolio_id_by_name(session, args.portfolio_name)

        strategy = get_strategy(args.strategy)

        weights = run_optimization(
    session=session,
    portfolio_id=portfolio_id,
    strategy=strategy,
    method_name=args.method,
)

        print("\nFinal Weights:")
        for k, v in weights.items():
            print(f"{k}: {v:.4f}")


if __name__ == "__main__":
    main()