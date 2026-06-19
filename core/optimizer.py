"""Optimiser module for CORTEX.

This module will support optimisation tasks and scoring.
"""


class Optimizer:
    """Optimisation helper stub."""

    def score(self, metrics: dict) -> dict:
        """Score a simple metric dictionary."""
        return {key: float(value) for key, value in metrics.items() if isinstance(value, (int, float))}
