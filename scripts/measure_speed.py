"""Masoara cat dureaza simularea pe grile mari.

Rulare (din folderul cel-lab):
    .venv\\Scripts\\python scripts/measure_speed.py
"""

import platform
import time

import numpy as np

from cellab.core.model import Automaton, State
from cellab.core.step import step

LIFE_RULES = [
    {"state": 0, "neighbor_state": 1, "counts": [3], "next_state": 1},
    {"state": 1, "neighbor_state": 1, "counts": [2, 3], "next_state": 1},
    {"state": 1, "next_state": 0},
]
DIFFUSION = {"type": "numeric", "expression": "media(celula, nord, sud, est, vest)"}
RULE30 = {"type": "table", "table": 30}


def measure(name, automaton, grid, generations):
    state = State(grid)
    rng = np.random.default_rng(0)
    start = time.perf_counter()
    for _ in range(generations):
        state = step(automaton, state, rng)
    seconds = time.perf_counter() - start
    print(f"{name}: {generations} generatii in {seconds:.2f} s")


def main():
    print(f"Python {platform.python_version()}, numpy {np.__version__}")
    rng = np.random.default_rng(0)

    for size in (100, 500):
        grid = (rng.random((size, size)) < 0.3).astype(np.uint8)
        life = Automaton([size, size], "toroidal", [0, 1], "moore", LIFE_RULES)
        measure(f"Game of Life {size}x{size}", life, grid, 100)

    grid = rng.random((500, 500))
    diffusion = Automaton([500, 500], "toroidal", [], "moore", DIFFUSION)
    measure("Difuzie 500x500", diffusion, grid, 100)

    row = np.zeros(10000, dtype=np.uint8)
    row[5000] = 1
    rule30 = Automaton([10000, 1], "toroidal", [0, 1], [-1, 1], RULE30)
    measure("Rule 30, 10000 celule", rule30, row, 1000)


main()
