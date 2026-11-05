"""Structurile de date folosite de motorul automatelor celulare."""

from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass
class Automaton:
    """Descrierea unui automat citită din JSON, independentă de regulile sale."""

    grid_size: list[int]
    boundary: str
    states: list[Any]
    neighborhood: Any
    rules: Any
    init: Any = None
    experiment: Any = None


@dataclass
class State:
    """Grila curentă a automatului și numărul generației sale."""

    grid: np.ndarray
    generation: int = 0
