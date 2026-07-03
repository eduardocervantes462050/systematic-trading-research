from portfolio.metrics.bigs import calculate_and_store_big_single_position
from portfolio.metrics.cagr import calculate_and_store_cagr
from portfolio.metrics.enh import calculate_and_store_enh
from portfolio.metrics.hhi import calculate_and_store_hhi
from portfolio.metrics.top5 import calculate_and_store_top5_concentration
from portfolio.metrics.volatility import calculate_and_store_volatility
from portfolio.metrics.max_drawdown import calculate_and_store_max_drawdown
from portfolio.metrics.sharpe import calculate_and_store_sharpe


def refresh_all_metrics(session):
    return {
        "cagr": calculate_and_store_cagr(session),
        "volatility": calculate_and_store_volatility(session),
        "max_drawdown": calculate_and_store_max_drawdown(session),
        "sharpe": calculate_and_store_sharpe(session),
        "hhi": calculate_and_store_hhi(session),
        "top5_concentration": calculate_and_store_top5_concentration(session),
        "enh": calculate_and_store_enh(session),
        "big_single_position": calculate_and_store_big_single_position(session),

    }