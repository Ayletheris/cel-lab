"""Aplicarea simultană a regulilor bazate pe numărul vecinilor."""

from collections.abc import Sequence
from typing import Any

import numpy as np

from cellab.core.neighbors import count_neighbors


def apply_rules(
    grid: np.ndarray,
    rules: Sequence[dict[str, Any]],
    kernel: np.ndarray,
    boundary: str = "fixed",
) -> np.ndarray:
    """Aplică prima regulă potrivită; fără potrivire, celula rămâne la fel.

    O regulă folosește state, neighbor_state, counts și next_state.
    Fără neighbor_state și counts, regula este ramura «altfel» pentru state.
    """

    result = grid.copy()
    matched = np.zeros(grid.shape, dtype=bool)
    neighbor_counts: dict[Any, np.ndarray] = {}

    ordered_rules = [rule for rule in rules if "counts" in rule]
    ordered_rules.extend(rule for rule in rules if "counts" not in rule)
    for rule in ordered_rules:
        mask = (grid == rule["state"]) & ~matched
        if "counts" in rule:
            neighbor_state = rule["neighbor_state"]
            if neighbor_state not in neighbor_counts:
                neighbor_counts[neighbor_state] = count_neighbors(
                    grid, neighbor_state, kernel, boundary
                )
            mask &= np.isin(neighbor_counts[neighbor_state], rule["counts"])
        result[mask] = rule["next_state"]
        matched |= mask

    return result
