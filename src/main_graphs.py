from data.database import (
    build_db,
    get_session,
    get_all_clients,
    get_portfolios_by_client,
)
from Graphs.plot_equity_curve import plot_equity_curve


engine, SessionFactory = build_db()

with get_session(SessionFactory) as session:

    clients = get_all_clients(session)

    for client in clients:
        portfolios = get_portfolios_by_client(session, client.client_id)

        for portfolio in portfolios:
            plot_equity_curve(session, portfolio.portfolio_id, portfolio.name)
