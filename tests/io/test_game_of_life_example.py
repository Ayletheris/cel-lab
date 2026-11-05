from pathlib import Path

import numpy as np

from cellab.core.step import step
from cellab.io import load_automaton, load_initial_state, load_initial_state_from_file, validate


EXAMPLES = Path(__file__).resolve().parents[2] / "automata" / "examples"


def test_game_of_life_example_is_valid_and_runs():
    automaton = load_automaton(EXAMPLES / "game_of_life.json")
    assert validate(automaton) == []
    state = load_initial_state(automaton)
    assert state.grid.shape == (8, 8)
    assert set(np.unique(state.grid)) <= {0, 1}
    assert step(automaton, state).generation == 1


def test_blinker_oscillates():
    automaton = load_automaton(EXAMPLES / "game_of_life.json")
    initial = load_initial_state_from_file(automaton, EXAMPLES / "blinker.txt")
    after_one = step(automaton, initial)
    after_two = step(automaton, after_one)

    assert not np.array_equal(after_one.grid, initial.grid)
    np.testing.assert_array_equal(after_two.grid, initial.grid)


def test_glider_moves_down_and_right():
    automaton = load_automaton(EXAMPLES / "game_of_life.json")
    initial = load_initial_state_from_file(automaton, EXAMPLES / "glider.txt")
    state = initial
    for _ in range(4):
        state = step(automaton, state)

    np.testing.assert_array_equal(state.grid, np.roll(initial.grid, (1, 1), axis=(0, 1)))
