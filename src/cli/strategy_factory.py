from portfolio.weights.equal_weight import EqualWeight
from portfolio.weights.efficient_frontier import EfficientFrontierWeight
from portfolio.weights.inverse import InverseVolatilityWeight
from portfolio.weights.risk_parity import RiskParityWeight
from portfolio.weights.base import BaseWeightGenerator
 
# Maps CLI --strategy argument to a strategy instance
STRATEGY_REGISTRY: dict[str, BaseWeightGenerator] = {
    "equal_weight":   EqualWeight(),
    "max_sharpe":     EfficientFrontierWeight(objective="max_sharpe"),
    "min_vol":        EfficientFrontierWeight(objective="min_vol"),
    "inverse_vol":    InverseVolatilityWeight(),
    "risk_parity":    RiskParityWeight(),
}
 
 
def get_strategy(name: str) -> BaseWeightGenerator:
    """
    Resolve a CLI strategy name to a strategy instance.
 
    Parameters
    ----------
    name : str
        One of: equal_weight, max_sharpe, min_vol, inverse_vol, risk_parity
 
    Returns
    -------
    BaseWeightGenerator
    """
    strategy = STRATEGY_REGISTRY.get(name)
    if strategy is None:
        valid = ", ".join(STRATEGY_REGISTRY.keys())
        raise ValueError(
            f"Unknown strategy '{name}'. Valid options: {valid}"
        )
    return strategy
