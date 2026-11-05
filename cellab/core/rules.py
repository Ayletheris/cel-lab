"""Aplicarea simultană a regulilor bazate pe numărul vecinilor."""

from collections.abc import Sequence
from typing import Any

import numpy as np

from cellab.core.neighbors import count_neighbors


def _state_value(value: Any, grid: np.ndarray) -> Any:
    if isinstance(value, dict) and "next_mod" in value:
        return (grid + 1) % value["next_mod"]
    return value


def apply_rules(
    grid: np.ndarray,
    rules: Sequence[dict[str, Any]],
    kernel: np.ndarray,
    boundary: str = "fixed",
    rng: np.random.Generator | None = None,
) -> np.ndarray:
    """Aplică prima regulă potrivită; fără potrivire, celula rămâne la fel.

    O regulă folosește state, condition și next_state; formatul vechi cu
    neighbor_state și counts rămâne valid. Fără condiție, este ramura «altfel».
    """

    for rule in rules:
        unknown = set(rule) - {"state", "condition", "neighbor_state", "counts", "next_state", "prob"}
        if unknown or ("neighbor_state" in rule and "counts" not in rule):
            raise ValueError(f"invalid rule {rule}: put the neighbor test inside 'condition'")
        # prob = sansa (0..1) ca regula sa se aplice; are nevoie de rng (generator cu seed)
        if "prob" in rule:
            if not 0 <= rule["prob"] <= 1:
                raise ValueError(f"prob must be between 0 and 1: {rule}")
            if rng is None:
                raise ValueError("rule with prob needs an rng (np.random.default_rng(seed))")

    result = grid.copy()
    matched = np.zeros(grid.shape, dtype=bool)
    neighbor_counts: dict[Any, np.ndarray] = {}

    def counts_for(state: Any) -> np.ndarray:
        if isinstance(state, dict) and "next_mod" in state:
            modulus = state["next_mod"]
            counts = [counts_for(value) for value in range(modulus)]
            return np.take_along_axis(
                np.stack(counts), ((grid + 1) % modulus)[np.newaxis, ...], axis=0
            )[0]
        if state not in neighbor_counts:
            neighbor_counts[state] = count_neighbors(grid, state, kernel, boundary)
        return neighbor_counts[state]

    def matches(condition: dict[str, Any]) -> np.ndarray:
        if "all" in condition:
            return np.logical_and.reduce([matches(item) for item in condition["all"]])
        if "any" in condition:
            return np.logical_or.reduce([matches(item) for item in condition["any"]])
        if "more_than" in condition:
            left, right = condition["more_than"]
            return counts_for(left) > counts_for(right)

        counts = counts_for(condition["neighbor_state"])
        if "at_least" in condition:
            return counts >= condition["at_least"]
        if "at_most" in condition:
            return counts <= condition["at_most"]
        if "exact" in condition:
            return counts == condition["exact"]
        if "between" in condition:
            low, high = condition["between"]
            return (counts >= low) & (counts <= high)
        return np.isin(counts, condition["counts"])

    ordered_rules = [rule for rule in rules if "condition" in rule or "counts" in rule]
    ordered_rules.extend(rule for rule in rules if "condition" not in rule and "counts" not in rule)
    for rule in ordered_rules:
        mask = ~matched
        if "state" in rule:
            mask = mask & (grid == rule["state"])
        if "condition" in rule:
            mask = mask & matches(rule["condition"])
        elif "counts" in rule:
            mask = mask & matches(rule)
        # tragem un nr random per celula (mereu pe toata grila, ca sa fie reproductibil)
        # daca nu iese sansa, celula merge mai departe la urm. regula
        if "prob" in rule:
            mask = mask & (rng.random(grid.shape) < rule["prob"])
        next_state = _state_value(rule["next_state"], grid)
        result[mask] = next_state[mask] if isinstance(next_state, np.ndarray) else next_state
        matched |= mask

    return result
