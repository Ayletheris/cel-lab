from pathlib import Path

import numpy as np

from cellab.core.model import State
from cellab.core.step import step
from cellab.io import load_automaton, load_initial_state, validate


EXAMPLE = Path(__file__).resolve().parents[2] / "automata" / "examples" / "brians_brain.json"


def test_brians_brain_example_is_valid_and_runs():
    automaton = load_automaton(EXAMPLE)
    assert validate(automaton) == []
    initial = load_initial_state(automaton)
    assert initial.grid.shape == (20, 20)
    assert set(np.unique(initial.grid)) <= {0, 1}
    assert step(automaton, initial).generation == 1


def test_brians_brain_v_pattern_and_state_cycle():
    automaton = load_automaton(EXAMPLE)
    grid = np.zeros((20, 20), dtype=int)
    grid[9, 9] = 1
    grid[9, 11] = 1
    grid[13, 13] = 2

    first = step(automaton, State(grid))
    assert first.grid[10, 10] == 1  # doua vecine aprinse
    assert first.grid[9, 9] == first.grid[9, 11] == 2
    assert first.grid[13, 13] == 0

    second = step(automaton, first)
    assert second.grid[10, 10] == 2
    assert second.grid[9, 9] == second.grid[9, 11] == 0
