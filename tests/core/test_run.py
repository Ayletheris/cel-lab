from dataclasses import replace

import numpy as np

from cellab.core.experiment import Experiment
from cellab.core.model import State
from cellab.core.run import run
from cellab.core.step import step
from cellab.io import load_automaton, load_initial_state, load_state, save_state


def test_life_runs_twenty_generations():
    automaton = load_automaton("automata/examples/life_glider.json")
    initial = load_initial_state(automaton)
    result = run(automaton, initial, Experiment(N=20, checkpoint_interval=1))

    assert result.steps == 20
    assert result.duration >= 0
    assert result.final_state.generation == 20
    assert result.generations.count() == 21
    assert [result.generations.get(t).generation for t in range(21)] == list(range(21))

    expected = initial
    for _ in range(20):
        expected = step(automaton, expected)
    np.testing.assert_array_equal(result.final_state.grid, expected.grid)


def test_run_continues_from_restored_generation(tmp_path):
    automaton = load_automaton("automata/examples/life_glider.json")
    saved = State(load_initial_state(automaton).grid, generation=7)
    path = save_state(saved, automaton, tmp_path / "state.npz")
    restored = load_state(path, automaton)
    result = run(automaton, restored, Experiment(N=5, checkpoint_interval=5))

    assert result.final_state.generation == 12
    assert result.steps == 5
    assert [result.generations.get(t).generation for t in (7, 10, 12)] == [7, 10, 12]
    assert result.generations.count() == 3


def test_run_uses_experiment_seed():
    automaton = load_automaton("automata/examples/life.json")
    automaton = replace(automaton, rules=[{"state": 0, "prob": 0.5, "next_state": 1}])
    initial = State(np.zeros((5, 5), dtype=int))

    first = run(automaton, initial, Experiment(N=3, seed=42))
    second = run(automaton, initial, Experiment(N=3, seed=42))

    np.testing.assert_array_equal(first.final_state.grid, second.final_state.grid)


def test_run_can_continue_with_restored_rng(tmp_path):
    automaton = load_automaton("automata/examples/life.json")
    automaton = replace(automaton, rules=[{"state": 0, "prob": 0.5, "next_state": 1}])
    initial = State(np.zeros((5, 5), dtype=int))
    experiment = Experiment(N=4, seed=42)

    full = run(automaton, initial, experiment)
    rng = np.random.default_rng(experiment.seed)
    first = run(automaton, initial, Experiment(N=2, seed=42), rng=rng)
    path = save_state(first.final_state, automaton, tmp_path / "state.npz", rng=rng)
    restored_rng = np.random.default_rng(0)
    restored = load_state(path, automaton, rng=restored_rng)
    continued = run(automaton, restored, Experiment(N=2, seed=42), rng=restored_rng)

    assert continued.final_state.generation == 4
    np.testing.assert_array_equal(continued.final_state.grid, full.final_state.grid)
