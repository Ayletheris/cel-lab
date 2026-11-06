"""Aplicarea simultană a regulilor bazate pe numărul vecinilor.

Peste tot lucram cu "masti": matrici de True/False de aceeasi marime cu grila.
True = regula se aplica pe celula aceea. In loc de operatorii ~ & | folosim
functiile cu nume din NumPy (logical_not, logical_and, logical_or),
care fac acelasi lucru, celula cu celula.
"""

from collections.abc import Sequence
from typing import Any

import numpy as np

from cellab.core.neighbors import count_neighbors


def _state_value(value: Any, grid: np.ndarray) -> Any:
    """Starea in care trece celula. {"next_mod": m} = urmatoarea stare, in cerc: 0 -> 1 -> ... -> m-1 -> 0."""
    if isinstance(value, dict) and "next_mod" in value:
        return (grid + 1) % value["next_mod"]
    return value


def _check_rules(rules: Sequence[dict[str, Any]], rng) -> None:
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

    _check_rules(rules, rng)

    # numarul de vecini pt fiecare stare, calculat o singura data
    saved_counts: dict[Any, np.ndarray] = {}

    def counts_for(state: Any) -> np.ndarray:
        """Pt fiecare celula: cati vecini are in starea `state`."""
        if isinstance(state, dict) and "next_mod" in state:
            # fiecare celula se uita la vecinii aflati in starea ei urmatoare
            modulus = state["next_mod"]
            next_state = (grid + 1) % modulus
            counts = np.zeros(grid.shape, dtype=int)
            for value in range(modulus):
                counts = np.where(next_state == value, counts_for(value), counts)
            return counts
        if state not in saved_counts:
            saved_counts[state] = count_neighbors(grid, state, kernel, boundary)
        return saved_counts[state]

    def matches(condition: dict[str, Any]) -> np.ndarray:
        """Masca celulelor care indeplinesc conditia."""
        if "all" in condition:  # toate conditiile (SI)
            masks = [matches(item) for item in condition["all"]]
            return np.logical_and.reduce(masks)
        if "any" in condition:  # macar una (SAU)
            masks = [matches(item) for item in condition["any"]]
            return np.logical_or.reduce(masks)
        if "more_than" in condition:  # mai multi vecini in starea A decat in starea B
            a, b = condition["more_than"]
            return counts_for(a) > counts_for(b)

        counts = counts_for(condition["neighbor_state"])
        if "at_least" in condition:
            return counts >= condition["at_least"]
        if "at_most" in condition:
            return counts <= condition["at_most"]
        if "exact" in condition:
            return counts == condition["exact"]
        if "between" in condition:
            low, high = condition["between"]
            return np.logical_and(counts >= low, counts <= high)
        return np.isin(counts, condition["counts"])

    # intai regulile cu conditie, apoi cele fara (ramura "altfel")
    with_condition = [rule for rule in rules if "condition" in rule or "counts" in rule]
    without_condition = [rule for rule in rules if "condition" not in rule and "counts" not in rule]

    result = grid.copy()  # grila noua; testele se fac mereu pe grila veche
    already_set = np.zeros(grid.shape, dtype=bool)  # celulele prinse deja de o regula

    for rule in with_condition + without_condition:
        # 1. doar celulele neprinse inca de o regula anterioara
        mask = np.logical_not(already_set)
        # 2. doar celulele in starea ceruta de regula
        if "state" in rule:
            mask = np.logical_and(mask, grid == rule["state"])
        # 3. doar celulele care indeplinesc conditia pe vecini
        if "condition" in rule:
            mask = np.logical_and(mask, matches(rule["condition"]))
        elif "counts" in rule:
            mask = np.logical_and(mask, matches(rule))
        # 4. prob: un numar aleator per celula (mereu pe toata grila, ca sa fie reproductibil);
        #    daca nu iese sansa, celula merge mai departe la urmatoarea regula
        if "prob" in rule:
            lucky = rng.random(grid.shape) < rule["prob"]
            mask = np.logical_and(mask, lucky)

        # scriem starea noua pe celulele din masca si le marcam ca prinse
        next_state = _state_value(rule["next_state"], grid)
        if isinstance(next_state, np.ndarray):
            result[mask] = next_state[mask]
        else:
            result[mask] = next_state
        already_set = np.logical_or(already_set, mask)

    return result
