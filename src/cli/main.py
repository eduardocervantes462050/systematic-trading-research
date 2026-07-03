"""
src/main.py

Unified CLI entry point.

OPTIMIZATION
------------
  python main.py optimize
    --portfolio_name  NAME
    --strategy        equal_weight | max_sharpe | min_vol | inverse_vol | risk_parity
    --method          METHOD

CLIENT MANAGEMENT
-----------------
  python main.py client list
  python main.py client show        --client_id UUID
  python main.py client add         --name NAME --email EMAIL [--phone PHONE]
  python main.py client correct     --client_id UUID --field FIELD --value VALUE
  python main.py client delete      --client_id UUID

PORTFOLIO MANAGEMENT
--------------------
  python main.py portfolio list     --client_id UUID
  python main.py portfolio add      --client_id UUID --name NAME --risk_level LEVEL --start_date YYYY-MM-DD
  python main.py portfolio update   --portfolio_id UUID --field FIELD --value VALUE

POSITION MANAGEMENT
-------------------
  python main.py position list      --portfolio_id UUID
  python main.py position set       --portfolio_id UUID --symbol TICKER --quantity N --avg_price N
  python main.py position delete    --portfolio_id UUID --symbol TICKER

TRANSACTION MANAGEMENT
----------------------
  python main.py transaction list   --portfolio_id UUID
  python main.py transaction add    --portfolio_id UUID --symbol TICKER --type buy|sell --quantity N --price N
"""

import argparse
from data.engine import build_db, get_session
from services.optimization_service import run_optimization
from cli.strategy_factory import get_strategy
from cli import commands as cmd
from data.repositories.portfolio_repo import get_portfolio_id_by_name


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="quant-cli",
        description="Quant portfolio CLI — optimization & client management",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # ── OPTIMIZE ──────────────────────────────────────────────────────────────
    opt = sub.add_parser("optimize", help="Run portfolio optimization")
    opt.add_argument("--portfolio_name", required=True)
    opt.add_argument("--strategy", required=True)
    opt.add_argument("--method", required=True)

    # ── CLIENT ────────────────────────────────────────────────────────────────
    client_p = sub.add_parser("client", help="Manage clients")
    client_sub = client_p.add_subparsers(dest="subcommand", required=True)

    client_sub.add_parser("list", help="List all clients")

    cs = client_sub.add_parser("show", help="Show client details")
    cs.add_argument("--client_id", required=True)

    ca = client_sub.add_parser("add", help="Add a new client")
    ca.add_argument("--name", required=True)
    ca.add_argument("--email", required=True)
    ca.add_argument("--phone")

    cc = client_sub.add_parser("correct", help="Correct a client field")
    cc.add_argument("--client_id", required=True)
    cc.add_argument(
        "--field",
        required=True,
        choices=["name", "email", "phone"],
        help="Field to update",
    )
    cc.add_argument("--value", required=True)

    cd = client_sub.add_parser("delete", help="Delete a client (cascades)")
    cd.add_argument("--client_id", required=True)

    # ── PORTFOLIO ─────────────────────────────────────────────────────────────
    port_p = sub.add_parser("portfolio", help="Manage portfolios")
    port_sub = port_p.add_subparsers(dest="subcommand", required=True)

    pl = port_sub.add_parser("list", help="List portfolios for a client")
    pl.add_argument("--client_id", required=True)

    pa = port_sub.add_parser("add", help="Add a portfolio to a client")
    pa.add_argument("--client_id", required=True)
    pa.add_argument("--name", required=True)
    pa.add_argument("--risk_level", required=True, choices=["low", "medium", "high"])
    pa.add_argument("--start_date", required=True, help="YYYY-MM-DD")

    pu = port_sub.add_parser("update", help="Update a portfolio field")
    pu.add_argument("--portfolio_id", required=True)
    pu.add_argument("--field", required=True, choices=["name", "risk_level"])
    pu.add_argument("--value", required=True)

    # ── POSITION ──────────────────────────────────────────────────────────────
    pos_p = sub.add_parser("position", help="Manage positions")
    pos_sub = pos_p.add_subparsers(dest="subcommand", required=True)

    posl = pos_sub.add_parser("list", help="List positions in a portfolio")
    posl.add_argument("--portfolio_id", required=True)

    poss = pos_sub.add_parser("set", help="Create or overwrite a position")
    poss.add_argument("--portfolio_id", required=True)
    poss.add_argument("--symbol", required=True)
    poss.add_argument("--quantity", required=True, type=float)
    poss.add_argument("--avg_price", required=True, type=float)

    posd = pos_sub.add_parser("delete", help="Remove a position")
    posd.add_argument("--portfolio_id", required=True)
    posd.add_argument("--symbol", required=True)

    posh = pos_sub.add_parser("history", help="Reconstruct positions as of a date/time")
    posh.add_argument("--portfolio_id", required=True)
    posh.add_argument(
        "--datetime",
        required=True,
        dest="date",
        help="YYYY-MM-DD  or  'YYYY-MM-DD HH:MM:SS'",
    )

    # ── TRANSACTION ───────────────────────────────────────────────────────────
    tx_p = sub.add_parser("transaction", help="Manage transactions")
    tx_sub = tx_p.add_subparsers(dest="subcommand", required=True)

    txl = tx_sub.add_parser("list", help="List transactions in a portfolio")
    txl.add_argument("--portfolio_id", required=True)

    txa = tx_sub.add_parser("add", help="Record a buy or sell transaction")
    txa.add_argument("--portfolio_id", required=True)
    txa.add_argument("--symbol", required=True)
    txa.add_argument("--type", required=True, choices=["buy", "sell"])
    txa.add_argument("--quantity", required=True, type=float)
    txa.add_argument("--price", required=True, type=float)

    # ── REBALANCE ─────────────────────────────────────────────────────────────
    rb = sub.add_parser(
        "rebalance",
        help="Generate buy/sell orders from latest optimized weights in DB",
    )
    rb.add_argument("--portfolio_id", required=True)
    # ── REPORT ─────────────────────────────────────────────────────────────
    report_st = sub.add_parser("report", help="Create reports")
    report_sub = report_st.add_subparsers(dest="subcommand", required=True)

    rr = report_sub.add_parser(
        "recommendation", help="Create portfolio recommendation report"
    )

    rr.add_argument("--client_id", required=True)

    # ── ANALYSIS ─────────────────────────────────────────────────────────────
    analytics = sub.add_parser("analytics", help="Generate portfolio analytics")

    analytics.add_argument(
        "--client_id",
        required=True,
    )

    analytics.add_argument(
        "--portfolio_id",
        required=False,
    )

    # ── METRICS ─────────────────────────────────────────────────────────────
    metrics = sub.add_parser("metrics", help="Generate portfolio metrics")

    metrics.add_argument(
        "--client_id",
        required=True,
    )

    metrics.add_argument(
        "--portfolio_id",
        required=False,
    )
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    engine, SessionFactory = build_db()

    # ── OPTIMIZE ──────────────────────────────────────────────────────────────
    if args.command == "optimize":
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
            print(f"  {k}: {v:.4f}")

    # ── CLIENT ────────────────────────────────────────────────────────────────
    elif args.command == "client":
        dispatch = {
            "list": cmd.cmd_client_list,
            "show": cmd.cmd_client_show,
            "add": cmd.cmd_client_add,
            "correct": cmd.cmd_client_correct,
            "delete": cmd.cmd_client_delete,
        }
        dispatch[args.subcommand](args, SessionFactory)

    # ── PORTFOLIO ─────────────────────────────────────────────────────────────
    elif args.command == "portfolio":
        dispatch = {
            "list": cmd.cmd_portfolio_list,
            "add": cmd.cmd_portfolio_add,
            "update": cmd.cmd_portfolio_update,
        }
        dispatch[args.subcommand](args, SessionFactory)

    # ── POSITION ──────────────────────────────────────────────────────────────
    elif args.command == "position":
        dispatch = {
            "list": cmd.cmd_position_list,
            "set": cmd.cmd_position_set,
            "delete": cmd.cmd_position_delete,
            "history": cmd.cmd_position_history,
        }
        dispatch[args.subcommand](args, SessionFactory)

    # ── TRANSACTION ───────────────────────────────────────────────────────────
    elif args.command == "transaction":
        dispatch = {
            "list": cmd.cmd_transaction_list,
            "add": cmd.cmd_transaction_add,
        }
        dispatch[args.subcommand](args, SessionFactory)

    # ── REBALANCE ─────────────────────────────────────────────────────────────
    elif args.command == "rebalance":
        cmd.cmd_rebalance(args, SessionFactory)

    # ── REPORT ─────────────────────────────────────────────────────────────
    elif args.command == "report":
        dispatch = {
            "recommendation": cmd.cmd_report_recommendation,
        }
        dispatch[args.subcommand](args, SessionFactory)

    # ── ANALYTICS ─────────────────────────────────────────────────────────────
    elif args.command == "analytics":
        cmd.cmd_analytics(args, SessionFactory)

    # ── METRICS ─────────────────────────────────────────────────────────────
    elif args.command == "metrics":
        cmd.cmd_metrics(args, SessionFactory)



if __name__ == "__main__":
    main()
