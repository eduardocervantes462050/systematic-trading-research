from typing import Dict, List
import pandas as pd
import numpy as np

from .base import BaseWeightGenerator


class InverseVolatilityWeight(BaseWeightGenerator):
    """
    Inverse Volatility (Inverse Risk) portfolio generator.

    Idea:
        w_i ∝ 1 / σ_i

    Higher volatility assets get lower weight.
    """

    def generate(
        self,
        returns: pd.DataFrame,
        cov_matrix: pd.DataFrame,
        assets: List[str],
        **kwargs
    ) -> Dict[str, float]:

        if not assets:
            raise ValueError("Asset list is empty")

        # compute annualized / sample volatility
        vol = returns[assets].std()

        # avoid division by zero
        vol = vol.replace(0, np.nan)
        inv_vol = 1.0 / vol

        # fill any NaNs safely
        inv_vol = inv_vol.fillna(0)

        total = inv_vol.sum()

        if total == 0:
            raise ValueError("All volatilities are zero or invalid")

        weights = {
            asset: float(inv_vol[asset] / total)
            for asset in assets
        }

        return self.validate_weights(weights)