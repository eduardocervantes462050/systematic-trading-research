import numpy as np
from scipy.optimize import minimize


# -----------------------------
# Portfolio Statistics
# -----------------------------
def portfolio_return(weights, expected_returns):
    """Compute expected return of the portfolio."""
    return np.dot(weights, expected_returns)


def portfolio_volatility(weights, cov_matrix):
    """Compute portfolio volatility (std deviation)."""
    return np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))


def sharpe_ratio(weights, expected_returns, cov_matrix, risk_free_rate=0.0):
    """Compute Sharpe ratio of portfolio."""
    port_ret = portfolio_return(weights, expected_returns)
    port_vol = portfolio_volatility(weights, cov_matrix)
    return (port_ret - risk_free_rate) / port_vol


# -----------------------------
# Optimization
# -----------------------------
def min_variance_portfolio(expected_returns, cov_matrix, bounds=None):
    """Find weights that minimize portfolio volatility."""
    n = len(expected_returns)
    if bounds is None:
        bounds = [(0, 1)] * n
    constraints = {"type": "eq", "fun": lambda w: np.sum(w) - 1}
    initial_guess = np.repeat(1 / n, n)

    result = minimize(
        portfolio_volatility,
        initial_guess,
        args=(cov_matrix,),
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
    )
    return result.x


def efficient_frontier(
    expected_returns, cov_matrix, returns_range=np.linspace(0.0, 0.3, 50)
):
    """Generate the Efficient Frontier."""
    n = len(expected_returns)
    frontier_weights = []
    frontier_returns = []
    frontier_vols = []

    bounds = [(0, 1)] * n

    for target_return in returns_range:
        constraints = [
            {"type": "eq", "fun": lambda w: np.sum(w) - 1},
            {
                "type": "eq",
                "fun": lambda w: portfolio_return(w, expected_returns) - target_return,
            },
        ]
        result = minimize(
            portfolio_volatility,
            np.repeat(1 / n, n),
            args=(cov_matrix,),
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
        )
        if result.success:
            frontier_weights.append(result.x)
            frontier_returns.append(target_return)
            frontier_vols.append(portfolio_volatility(result.x, cov_matrix))

    return np.array(frontier_returns), np.array(frontier_vols), frontier_weights
