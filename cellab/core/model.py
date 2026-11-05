"""Structurile de date folosite de motorul automatelor celulare."""

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from cellab.core.experiment import Experiment


@dataclass
class Automaton:
    """Descrierea unui automat citită din JSON, independentă de regulile sale."""

    grid_size: list[int]
    boundary: str
    states: list[Any]
    neighborhood: Any
    rules: Any
    init: Any = None
    experiment: Experiment = field(default_factory=Experiment)
    defaults_used: list[str] = field(default_factory=list, repr=False, compare=False)
    name: str = "automaton"


@dataclass
class State:
    """Grila curentă a automatului și numărul generației sale."""

    grid: np.ndarray
    generation: int = 0
