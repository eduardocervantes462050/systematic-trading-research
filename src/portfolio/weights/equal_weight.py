from typing import Dict, List
import pandas as pd

from .base import BaseWeightGenerator


class EqualWeight(BaseWeightGenerator):
    """
    Equal weight portfolio generator.

    Assigns the same weight to every asset:
    w_i = 1 / N
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

        n = len(assets)
        weight = 1.0 / n

        weights = {asset: weight for asset in assets}

        # ensure robustness via base validation
        return self.validate_weights(weights)
