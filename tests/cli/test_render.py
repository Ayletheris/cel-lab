from pathlib import Path

import numpy as np
import pytest

from cellab.cli.render import render_generations, render_rows, render_text
from cellab.core.model import Automaton, State
from cellab.core.run import run
from cellab.core.experiment import Experiment
from cellab.io import load_automaton, load_initial_state

EXAMPLES = Path(__file__).resolve().parents[2] / "automata" / "examples"


def automaton_with(states, size):
    return Automaton(grid_size=list(size), boundary="fixed", states=states,
                     neighborhood={"type": "moore", "radius": 1}, rules=[])


def test_blinker_looks_right():
    grid = np.zeros((5, 5), dtype=np.uint8)
    grid[2, 1:4] = 1
    text = render_text(State(grid, 3), automaton_with([0, 1], (5, 5)))
    assert text.splitlines() == [
        "generatia 3",
        ".....",
        ".....",
        ".###.",
        ".....",
        ".....",
        "legenda: '.' = 0, '#' = 1",
    ]


def test_three_states_get_three_chars():
    grid = np.array([[0, 1, 2]])
    text = render_text(State(grid), automaton_with([0, 1, 2], (1, 3)))
    assert ".#o" in text.splitlines()
    assert "'o' = 2" in text


def test_big_grid_is_cut_with_message():
    grid = np.zeros((100, 120), dtype=np.uint8)
    text = render_text(State(grid), automaton_with([0, 1], (100, 120)), max_width=80, max_height=40)
    lines = text.splitlines()
    assert len(lines[1]) == 80
    assert "40x80 din grila de 100x120" in text


def test_numbers_use_shades():
    grid = np.array([[0.0, 0.5, 1.0]])
    text = render_text(State(grid), automaton_with(["number"], (1, 3)))
    assert text.splitlines()[1] == ".+@"
    assert "minim (0)" in text and "maxim (1)" in text


def test_rule30_rows_make_a_triangle():
    automaton = load_automaton(EXAMPLES / "rule30.json")
    result = run(automaton, load_initial_state(automaton), Experiment(N=3, checkpoint_interval=1))
    states = [result.generations.get(t) for t in range(4)]
    lines = render_rows(states, automaton, max_width=101).splitlines()
    assert lines[0].strip(".") == "#"
    assert lines[1].strip(".") == "###"
    assert lines[2].strip(".") == "##..#"
    assert lines[3].strip(".") == "##.####"


def test_several_generations_one_under_another():
    grid = np.zeros((2, 2), dtype=np.uint8)
    text = render_generations([State(grid, 0), State(grid, 1)], automaton_with([0, 1], (2, 2)))
    assert "generatia 0" in text and "generatia 1" in text


def test_rows_only_for_one_row_automata():
    with pytest.raises(ValueError):
        render_rows([State(np.zeros((2, 2)))], automaton_with([0, 1], (2, 2)))
