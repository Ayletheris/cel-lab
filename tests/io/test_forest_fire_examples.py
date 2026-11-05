from pathlib import Path

import numpy as np
import pytest

from cellab.core.experiment import Experiment
from cellab.core.run import run
from cellab.core.step import step
from cellab.io import load_automaton, load_initial_state, load_state, save_state, validate


EXAMPLES = Path(__file__).resolve().parents[2] / "automata" / "examples"


@pytest.mark.parametrize("name", ["forest_fire", "forest_fire_random"])
def test_forest_fire_examples_are_valid(name):
    automaton = load_automaton(EXAMPLES / f"{name}.json")
    assert validate(automaton) == []
    assert load_initial_state(automaton).grid.shape == tuple(automaton.grid_size)


def test_simple_forest_burns_connected_trees():
    automaton = load_automaton(EXAMPLES / "forest_fire.json")
    initial = load_initial_state(automaton)
    first = step(automaton, initial)
    assert first.grid[1, 2] == 0
    assert first.grid[0, 2] == 2

    result = run(automaton, initial, Experiment(N=8))
    assert result.final_state.generation == 8
    assert not result.final_state.grid.any()


def test_random_forest_repeats_with_seed_and_restored_rng(tmp_path):
    automaton = load_automaton(EXAMPLES / "forest_fire_random.json")
    initial = load_initial_state(automaton)
    full = run(automaton, initial, Experiment(N=10, seed=7))
    again = run(automaton, initial, Experiment(N=10, seed=7))
    np.testing.assert_array_equal(full.final_state.grid, again.final_state.grid)

    rng = np.random.default_rng(7)
    first = run(automaton, initial, Experiment(N=5, seed=7), rng=rng)
    path = save_state(first.final_state, automaton, tmp_path / "forest.npz", rng=rng)
    restored_rng = np.random.default_rng(0)
    restored = load_state(path, automaton, rng=restored_rng)
    continued = run(automaton, restored, Experiment(N=5, seed=7), rng=restored_rng)
    np.testing.assert_array_equal(continued.final_state.grid, full.final_state.grid)
