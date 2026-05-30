"""
src/cli/commands.py

All client-management subcommands for the CLI.
Each function receives the parsed args and a SessionFactory,
does its work via the service layer, and prints results.
"""

from __future__ import annotations

from services import client_service as svc


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def _row(label: str, value) -> None:
    print(f"  {label:<20} {value}")


def _divider(title: str = "") -> None:
    width = 60
    if title:
        print(f"\n{'─' * 4} {title} {'─' * (width - len(title) - 6)}")
    else:
        print("─" * width)


# ─────────────────────────────────────────────
# CLIENT COMMANDS
# ─────────────────────────────────────────────

def cmd_client_list(args, SessionFactory) -> None:
    clients = svc.list_clients(SessionFactory)
    if not clients:
        print("No clients found.")
        return
    _divider("CLIENTS")
    for c in clients:
        print(f"\n  {c['name']}  ({c['email']})")
        _row("client_id:", c["client_id"])
        _row("phone:", c["phone"])
        _row("created:", c["created_at"])
    print()


def cmd_client_show(args, SessionFactory) -> None:
    data = svc.show_client(SessionFactory, args.client_id)
    _divider(f"CLIENT: {data['name']}")
    _row("client_id:", data["client_id"])
    _row("email:", data["email"])
    _row("phone:", data["phone"])
    _row("created:", data["created_at"])
    if data["portfolios"]:
        _divider("PORTFOLIOS")
        for p in data["portfolios"]:
            print(
                f"  {p['name']:<30} risk={p['risk_level']:<8} "
                f"start={p['start_date']}  id={p['portfolio_id']}"
            )
    else:
        print("\n  No portfolios yet.")
    print()


def cmd_client_add(args, SessionFactory) -> None:
    result = svc.add_client(
        SessionFactory,
        name=args.name,
        email=args.email,
        phone=getattr(args, "phone", None),
    )
    print(f"\n✓ Client created: {result['name']} ({result['email']})")
    print(f"  client_id: {result['client_id']}\n")


def cmd_client_correct(args, SessionFactory) -> None:
    result = svc.correct_client(
        SessionFactory,
        client_id=args.client_id,
        field=args.field,
        value=args.value,
    )
    print(
        f"\n✓ Client {result['client_id']}: "
        f"'{result['updated']}' updated to '{result['new_value']}'\n"
    )


def cmd_client_delete(args, SessionFactory) -> None:
    confirm = input(
        f"  ⚠  This will delete client {args.client_id} and ALL their portfolios/transactions.\n"
        f"  Type 'yes' to confirm: "
    )
    if confirm.strip().lower() != "yes":
        print("  Aborted.\n")
        return
    svc.remove_client(SessionFactory, args.client_id)
    print(f"\n✓ Client {args.client_id} deleted.\n")


# ─────────────────────────────────────────────
# PORTFOLIO COMMANDS
# ─────────────────────────────────────────────

def cmd_portfolio_list(args, SessionFactory) -> None:
    portfolios = svc.list_portfolios(SessionFactory, args.client_id)
    if not portfolios:
        print(f"No portfolios found for client {args.client_id}.")
        return
    _divider(f"PORTFOLIOS — client {args.client_id}")
    for p in portfolios:
        print(f"\n  {p['name']}")
        _row("portfolio_id:", p["portfolio_id"])
        _row("risk_level:", p["risk_level"])
        _row("start_date:", p["start_date"])
    print()


def cmd_portfolio_add(args, SessionFactory) -> None:
    result = svc.add_portfolio(
        SessionFactory,
        client_id=args.client_id,
        name=args.name,
        risk_level=args.risk_level,
        start_date=args.start_date,
    )
    print(f"\n✓ Portfolio created: '{result['name']}' (risk={result['risk_level']})")
    print(f"  portfolio_id: {result['portfolio_id']}\n")


def cmd_portfolio_update(args, SessionFactory) -> None:
    result = svc.update_portfolio(
        SessionFactory,
        portfolio_id=args.portfolio_id,
        field=args.field,
        value=args.value,
    )
    print(
        f"\n✓ Portfolio {result['portfolio_id']}: "
        f"'{result['updated']}' updated to '{result['new_value']}'\n"
    )


# ─────────────────────────────────────────────
# POSITION COMMANDS
# ─────────────────────────────────────────────

def cmd_position_list(args, SessionFactory) -> None:
    positions = svc.list_positions(SessionFactory, args.portfolio_id)
    if not positions:
        print(f"No positions found in portfolio {args.portfolio_id}.")
        return
    _divider(f"POSITIONS — portfolio {args.portfolio_id}")
    print(f"\n  {'SYMBOL':<10} {'QTY':>12} {'AVG PRICE':>12} {'MKT VALUE':>12}")
    print(f"  {'─'*10} {'─'*12} {'─'*12} {'─'*12}")
    for p in positions:
        print(
            f"  {p['symbol']:<10} "
            f"{p['quantity']:>12.4f} "
            f"{p['avg_price']:>12.2f} "
            f"{p['market_value']:>12.2f}"
        )
    print()


def cmd_position_set(args, SessionFactory) -> None:
    result = svc.set_position(
        SessionFactory,
        portfolio_id=args.portfolio_id,
        symbol=args.symbol,
        quantity=float(args.quantity),
        avg_price=float(args.avg_price),
    )
    print(
        f"\n✓ Position set: {result['symbol']}  "
        f"qty={result['quantity']}  avg_price={result['avg_price']}\n"
    )


def cmd_position_delete(args, SessionFactory) -> None:
    confirm = input(
        f"  ⚠  Remove position '{args.symbol}' from portfolio {args.portfolio_id}?\n"
        f"  Type 'yes' to confirm: "
    )
    if confirm.strip().lower() != "yes":
        print("  Aborted.\n")
        return
    svc.remove_position(SessionFactory, args.portfolio_id, args.symbol)
    print(f"\n✓ Position '{args.symbol.upper()}' removed.\n")


# ─────────────────────────────────────────────
# TRANSACTION COMMANDS
# ─────────────────────────────────────────────

def cmd_transaction_list(args, SessionFactory) -> None:
    txs = svc.list_transactions(SessionFactory, args.portfolio_id)
    if not txs:
        print(f"No transactions found in portfolio {args.portfolio_id}.")
        return
    _divider(f"TRANSACTIONS — portfolio {args.portfolio_id}")
    print(f"\n  {'DATE':<12} {'TYPE':<6} {'SYMBOL':<10} {'QTY':>10} {'PRICE':>10} {'TOTAL':>12}")
    print(f"  {'─'*12} {'─'*6} {'─'*10} {'─'*10} {'─'*10} {'─'*12}")
    for t in txs:
        print(
            f"  {t['date']:<12} {t['type'].upper():<6} {t['symbol']:<10} "
            f"{t['quantity']:>10.4f} {t['price']:>10.2f} {t['total']:>12.2f}"
        )
    print()


def cmd_transaction_add(args, SessionFactory) -> None:
    result = svc.record_transaction(
        SessionFactory,
        portfolio_id=args.portfolio_id,
        symbol=args.symbol,
        tx_type=args.type,
        quantity=float(args.quantity),
        price=float(args.price),
    )
    print(
        f"\n✓ Transaction recorded: {result['type'].upper()} {result['symbol']}  "
        f"qty={result['quantity']}  price={result['price']}  total={result['total']}"
    )
    print(f"  transaction_id: {result['transaction_id']}\n")


# ─────────────────────────────────────────────
# REBALANCE COMMAND
# ─────────────────────────────────────────────

def cmd_rebalance(args, SessionFactory) -> None:
    """
    Compute buy/sell orders to move from current positions to the latest
    optimized weights stored in optimized_portfolio_assets.

    Automatically reads weights and prices from the DB — no manual input needed.
    """

    # ── Load latest optimized weights from DB ─────────────────────────────────
    target_weights, opt_name = svc.get_latest_optimized_weights(
        SessionFactory, args.portfolio_id
    )
    if not target_weights:
        print(
            f"\n  ⚠  No optimized weights found for portfolio {args.portfolio_id}.\n"
            f"  Run optimize first:\n"
            f"  python -m src.cli.main optimize --portfolio_name ... --strategy ... --method ...\n"
        )
        return

    # ── Load latest prices from DB ────────────────────────────────────────────
    current_prices = svc.get_latest_prices(SessionFactory, list(target_weights.keys()))
    missing = [s for s in target_weights if s not in current_prices]
    if missing:
        print(f"\n  ⚠  No price data found for: {', '.join(missing)}\n")
        return

    # ── Load current positions ────────────────────────────────────────────────
    positions = svc.list_positions(SessionFactory, args.portfolio_id)
    if not positions:
        print(f"  No positions found in portfolio {args.portfolio_id}.\n")
        return

    current_holdings: dict[str, float] = {
        p["symbol"]: p["quantity"] for p in positions
    }

    # ── Compute portfolio market value ────────────────────────────────────────
    all_symbols = set(list(current_holdings.keys()) + list(target_weights.keys()))
    portfolio_value = sum(
        current_holdings.get(sym, 0.0) * current_prices.get(sym, 0.0)
        for sym in all_symbols
    )
    if portfolio_value <= 0:
        print("  ⚠  Could not compute portfolio value.\n")
        return

    # ── Compute deltas ────────────────────────────────────────────────────────
    orders: list[dict] = []
    for symbol in sorted(all_symbols):
        price = current_prices.get(symbol)
        if price is None:
            continue
        target_qty  = (portfolio_value * target_weights.get(symbol, 0.0)) / price
        current_qty = current_holdings.get(symbol, 0.0)
        delta_qty   = target_qty - current_qty
        if abs(delta_qty) < 0.0001:
            continue
        orders.append({
            "symbol":      symbol,
            "type":        "buy" if delta_qty > 0 else "sell",
            "delta_qty":   abs(delta_qty),
            "price":       price,
            "delta_value": abs(delta_qty * price),
            "current_qty": current_qty,
            "target_qty":  target_qty,
        })

    if not orders:
        print("\n  Portfolio is already at target weights. No orders needed.\n")
        return

    # ── Print order table ─────────────────────────────────────────────────────
    _divider(f"REBALANCE — {opt_name}")
    print(f"\n  Portfolio value : ${portfolio_value:,.2f}")
    print(f"  Weights source  : latest optimized run ({opt_name})\n")
    print(f"  {'SYMBOL':<10} {'ACTION':<6} {'CURRENT QTY':>12} {'TARGET QTY':>12} {'ORDER QTY':>12} {'@ PRICE':>10} {'VALUE':>12}")
    print(f"  {'─'*10} {'─'*6} {'─'*12} {'─'*12} {'─'*12} {'─'*10} {'─'*12}")

    sells = [o for o in orders if o["type"] == "sell"]
    buys  = [o for o in orders if o["type"] == "buy"]

    for o in sells + buys:
        action = "SELL" if o["type"] == "sell" else "BUY"
        print(
            f"  {o['symbol']:<10} {action:<6} "
            f"{o['current_qty']:>12.4f} {o['target_qty']:>12.4f} "
            f"{o['delta_qty']:>12.4f} {o['price']:>10.2f} "
            f"${o['delta_value']:>11,.2f}"
        )

    print(f"\n  {len(sells)} sell order(s)   {len(buys)} buy order(s)")

    # ── Confirm and save ──────────────────────────────────────────────────────
    confirm = input("\n  Save transactions and update positions? Type 'yes' to confirm: ")
    if confirm.strip().lower() != "yes":
        print("  Aborted — nothing saved.\n")
        return

    saved = 0
    for o in orders:
        result = svc.record_transaction(
            SessionFactory,
            portfolio_id=args.portfolio_id,
            symbol=o["symbol"],
            tx_type=o["type"],
            quantity=round(o["delta_qty"], 6),
            price=o["price"],
        )
        new_qty = round(o["target_qty"], 6)
        if new_qty > 0:
            svc.set_position(
                SessionFactory,
                portfolio_id=args.portfolio_id,
                symbol=o["symbol"],
                quantity=new_qty,
                avg_price=o["price"],
            )
        else:
            svc.remove_position(SessionFactory, args.portfolio_id, o["symbol"])

        print(
            f"  ✓ {o['type'].upper()} {result['symbol']:<6}  "
            f"qty={result['quantity']:.4f}  "
            f"new_position={new_qty:.4f}  "
            f"total=${result['total']:,.2f}"
        )
        saved += 1

    print(f"\n✓ {saved} transaction(s) saved and positions updated.\n")


# ─────────────────────────────────────────────
# POSITION HISTORY COMMAND
# ─────────────────────────────────────────────

def cmd_position_history(args, SessionFactory) -> None:
    """
    Reconstruct portfolio positions as of a given date
    by replaying all recorded transactions up to that date.
    """
    positions = svc.get_position_history(
        SessionFactory,
        portfolio_id=args.portfolio_id,
        as_of_date=args.date,
    )

    if not positions:
        print(f"\n  No positions found as of {args.date} — no transactions recorded before this date.\n")
        return

    total_value = sum(p["total_cost"] for p in positions)

    _divider(f"POSITIONS AS OF {args.date}")
    print(f"  (replayed all transactions up to {args.date})")
    print(f"\n  {'SYMBOL':<10} {'QUANTITY':>12} {'AVG PRICE':>12} {'TOTAL COST':>12}")
    print(f"  {'─'*10} {'─'*12} {'─'*12} {'─'*12}")
    for p in positions:
        print(
            f"  {p['symbol']:<10} "
            f"{p['quantity']:>12.4f} "
            f"{p['avg_price']:>12.2f} "
            f"{p['total_cost']:>12.2f}"
        )
    print(f"  {'─'*10} {'─'*12} {'─'*12} {'─'*12}")
    print(f"  {'TOTAL':<10} {'':>12} {'':>12} {total_value:>12.2f}")
    print()