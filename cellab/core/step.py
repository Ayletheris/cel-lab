"""Functia step: un pas de simulare pentru orice automat."""

import numpy as np

from cellab.core.model import Automaton, State
from cellab.core.neighborhood import make_kernel
from cellab.core.numeric import apply_numeric
from cellab.core.rules import apply_rules
from cellab.core.table import apply_table


def rule_kind(rules) -> str:
    """Spune ce fel de reguli are automatul: counts, table sau numeric.

    - lista de reguli                          -> counts (ex. Life, Brian's Brain)
    - {"type": "table", "table": 30}           -> table (ex. Rule 30)
    - {"type": "numeric", "expression": "..."} -> numeric (ex. difuzie, sandpile)
    """

    if isinstance(rules, list):
        return "counts"
    if isinstance(rules, dict) and rules.get("type") in {"table", "numeric"}:
        return rules["type"]
    raise ValueError("rules must be a list, or a dict with type 'table' or 'numeric'")


def make_automaton_kernel(neighborhood) -> np.ndarray:
    """Vecinatatea poate fi "moore", "von_neumann", o lista de offset-uri (1D)
    sau un dict cu raza, ex. {"type": "moore", "radius": 2}."""

    if isinstance(neighborhood, dict):
        return make_kernel(neighborhood["type"], neighborhood.get("radius", 1))
    return make_kernel(neighborhood)


def step(automaton: Automaton, state: State, rng: np.random.Generator | None = None) -> State:
    """Intoarce starea urmatoare. Starea primita nu se schimba."""

    kind = rule_kind(automaton.rules)
    grid = state.grid
    boundary = automaton.boundary

    if kind == "counts":
        kernel = make_automaton_kernel(automaton.neighborhood)
        new_grid = apply_rules(grid, automaton.rules, kernel, boundary, rng)
    elif kind == "table":
        new_grid = apply_table(grid, automaton.rules["table"], boundary)
    else:
        new_grid = apply_numeric(grid, automaton.rules["expression"], boundary)

    return State(grid=new_grid, generation=state.generation + 1)
