from typing import Dict, List
import pandas as pd
from pypfopt import EfficientFrontier
from .base import BaseWeightGenerator
 
 
class EfficientFrontierWeight(BaseWeightGenerator):
    """
    Efficient Frontier portfolio generator via pypfopt.
 
    Supports:
        - max_sharpe  : maximise Sharpe ratio
        - min_vol     : minimise volatility
    """
 
    def __init__(self, objective: str = "max_sharpe"):
        """
        Parameters
        ----------
        objective : str
            "max_sharpe" or "min_vol"
        """
        if objective not in ("max_sharpe", "min_vol"):
            raise ValueError("objective must be 'max_sharpe' or 'min_vol'")
        self.objective = objective
 
    def generate(
        self,
        returns: pd.DataFrame,
        cov_matrix: pd.DataFrame,
        assets: List[str],
        **kwargs,
    ) -> Dict[str, float]:
        if not assets:
            raise ValueError("Asset list is empty")
 
        mu = returns.astype(float)
        cov = cov_matrix.astype(float)
 
        ef = EfficientFrontier(mu, cov)
 
        if self.objective == "max_sharpe":
            ef.max_sharpe()
        else:
            ef.min_volatility()
 
        weights = ef.clean_weights()
        return self.validate_weights(dict(weights))
