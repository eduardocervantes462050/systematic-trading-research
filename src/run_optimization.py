from data.database import build_db, get_session
from services.optimization_service import run_equal_weight_optimization


def main():
    engine, SessionFactory = build_db()

    with get_session(SessionFactory) as session:

        portfolio_id = "16028f63-48a6-49ac-b335-b08fda217e03"

        weights = run_equal_weight_optimization(session, portfolio_id)

        print("Final Weights:", weights)


if __name__ == "__main__":
    main()
