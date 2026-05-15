"""
src/data/repositories/__init__.py
"""

from data.repositories.asset_repo import (
    upsert_asset,
    get_asset_by_symbol,
    get_assets_by_symbols,
    bulk_insert_prices,
    get_price_history,
)
from data.repositories.client_repo import (
    create_client,
    get_client_by_email,
    get_client_by_id,
    get_all_clients,
    update_client,
    delete_client,
)
from data.repositories.portfolio_repo import (
    create_portfolio,
    get_portfolio_by_id,
    get_portfolios_by_client,
    update_portfolio,
    delete_portfolio,
    upsert_holding,
    get_holdings,
    delete_holding,
    save_equity_curve,
    get_equity_curve,
    save_portfolio_metrics,
    get_portfolio_metrics,
)
from data.repositories.transaction_repo import (
    record_transaction,
    get_transactions,
    get_transaction_by_id,
    delete_transaction,
    get_transaction_summary,
)
from data.repositories.optimized_repo import (
    create_optimized_portfolio,
    get_optimized_portfolio_by_id,
    get_optimized_portfolios_by_portfolio,
    get_optimized_portfolio_by_method,
    upsert_optimized_portfolio,
    update_optimized_portfolio_stats,
    delete_optimized_portfolio,
    save_weights,
    get_weights,
    save_optimized_metrics,
    get_optimized_metrics,
)