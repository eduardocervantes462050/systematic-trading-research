from typing import Dict, List
import pandas as pd
import numpy as np
from .base import BaseWeightGenerator
 
 
class RiskParityWeight(BaseWeightGenerator):
    """
    Risk Parity (Equal Risk Contribution) portfolio generator.
    Each asset contributes equally to total portfolio risk.
    Uses scipy — no cvxpy required.
    """
 
    def generate(
        self,
        returns: pd.DataFrame,
        cov_matrix: pd.DataFrame,
        assets: List[str],
        **kwargs,
    ) -> Dict[str, float]:
        if not assets:
            raise ValueError("Asset list is empty")
 
        from scipy.optimize import minimize
 
        Sigma = cov_matrix.astype(float).loc[assets, assets].values
        n = len(assets)
 
        def objective(w):
            portfolio_vol = np.sqrt(w @ Sigma @ w)
            marginal = Sigma @ w
            rc = w * marginal / portfolio_vol      # risk contribution per asset
            target = rc.sum() / n                  # equal target
            return float(np.sum((rc - target) ** 2))
 
        w0 = np.ones(n) / n
        constraints = {"type": "eq", "fun": lambda w: np.sum(w) - 1}
        bounds = [(0.0, 1.0)] * n
 
        result = minimize(
            objective,
            w0,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={"ftol": 1e-12, "maxiter": 1000},
        )
 
        if not result.success:
            raise ValueError(f"Risk parity optimization failed: {result.message}")
 
        weights = {asset: float(result.x[i]) for i, asset in enumerate(assets)}
        return self.validate_weights(weights)
