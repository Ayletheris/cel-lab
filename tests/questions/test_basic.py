from pathlib import Path

import numpy as np
import pytest

from cellab.cli.commands import main
from cellab.cli.render import render_rows
from cellab.core.experiment import Experiment
from cellab.core.run import run
from cellab.io import load_automaton, load_initial_state
from cellab.questions.basic import count_after, count_all, count_cells, state_after

EXAMPLES = Path(__file__).resolve().parents[2] / "automata" / "examples"


def load(name):
    automaton = load_automaton(EXAMPLES / name)
    return automaton, load_initial_state(automaton)


def test_q1_blinker_turns_vertical():
    # life.json are un blinker orizontal pe randul 2
    automaton, state = load("life.json")
    after = state_after(automaton, state, 1)
    assert after.generation == 1
    assert after.grid[1:4, 2].all() and after.grid.sum() == 3


def test_q1_zero_steps_gives_same_state():
    automaton, state = load("life.json")
    np.testing.assert_array_equal(state_after(automaton, state, 0).grid, state.grid)


def test_q4_blinker_has_3_alive_cells():
    automaton, state = load("life.json")
    assert count_after(automaton, state, 1, 1) == 3
    assert count_after(automaton, state, 1, 0) == 22


def test_q4_rule30_matches_text_view():
    automaton, state = load("rule30.json")
    n = 20
    result = run(automaton, state, Experiment(N=n, checkpoint_interval=1))
    last_row = render_rows([result.final_state], automaton, max_width=101).splitlines()[0]
    assert count_after(automaton, state, n, 1) == last_row.count("#")


def test_q1_same_as_run_for_random_automaton():
    # acelasi seed ca run(), deci aceeasi stare finala
    automaton, state = load("forest_fire_random.json")
    result = run(automaton, state, Experiment(N=15, seed=automaton.experiment.seed))
    np.testing.assert_array_equal(state_after(automaton, state, 15).grid, result.final_state.grid)


def test_count_all_states():
    automaton, state = load("life.json")
    assert count_all(automaton, state) == {0: 22, 1: 3}
    assert count_cells(state, 1) == 3


def test_bad_questions_are_refused():
    automaton, state = load("life.json")
    with pytest.raises(ValueError):
        state_after(automaton, state, -1)
    with pytest.raises(ValueError):
        count_after(automaton, state, 1, 7)

    numeric, numeric_state = load("diffusion.json")
    with pytest.raises(ValueError):
        count_all(numeric, numeric_state)


def test_cli_state_after_and_count(capsys):
    assert main(["state-after", str(EXAMPLES / "life.json"), "--generations", "1"]) == 0
    out = capsys.readouterr().out
    assert "starea dupa 1 generatii" in out and "..#.." in out

    assert main(["count", str(EXAMPLES / "life.json"), "--generations", "1"]) == 0
    out = capsys.readouterr().out
    assert "starea 1: 3 celule" in out and "starea 0: 22 celule" in out
