from pathlib import Path

from cellab.core.step import step
from cellab.io import load_automaton, load_initial_state, validate


EXAMPLE = Path(__file__).resolve().parents[2] / "automata" / "examples" / "rule30.json"


def test_rule30_example_first_rows():
    automaton = load_automaton(EXAMPLE)
    assert validate(automaton) == []

    state = load_initial_state(automaton)
    assert state.grid.shape == (1, 101)
    assert state.grid.sum() == 1 and state.grid[0, 50] == 1

    rows = []
    for _ in range(5):
        rows.append("".join(str(value) for value in state.grid[0, 43:58]))
        state = step(automaton, state)

    assert rows == [
        "000000010000000",
        "000000111000000",
        "000001100100000",
        "000011011110000",
        "000110010001000",
    ]
