from abc import ABC, abstractmethod
from typing import Dict, List
import pandas as pd


class BaseWeightGenerator(ABC):
    """
    Abstract base class for all portfolio weight generators.

    Every strategy (equal weight, max Sharpe, risk parity, etc.)
    must implement this interface.
    """

    @abstractmethod
    def generate(
        self,
        returns: pd.DataFrame,
        cov_matrix: pd.DataFrame,
        assets: List[str],
        **kwargs
    ) -> Dict[str, float]:
        """
        Generate portfolio weights.

        Parameters
        ----------
        returns : pd.DataFrame
            Historical returns of assets.
        cov_matrix : pd.DataFrame
            Covariance matrix of returns.
        assets : List[str]
            List of asset tickers.
        kwargs : dict
            Extra parameters (risk aversion, constraints, etc.)

        Returns
        -------
        Dict[str, float]
            Asset weights summing to 1.0
        """
        pass

    def validate_weights(self, weights: Dict[str, float]) -> Dict[str, float]:
        """
        Ensures weights are valid:
        - non-negative (optional rule, can be relaxed later)
        - sum to 1.0
        """

        if not weights:
            raise ValueError("Weights dictionary is empty")

        total = sum(weights.values())

        if total == 0:
            raise ValueError("Sum of weights is zero")

        # normalize automatically (important for robustness)
        normalized = {k: v / total for k, v in weights.items()}

        return normalized

    def name(self) -> str:
        """
        Optional: override in child classes for logging/debugging.
        """
        return self.__class__.__name__
