import json
from pathlib import Path

import numpy as np
import pytest

from cellab.core.model import Automaton, State
from cellab.core.step import step
from cellab.io import load_automaton, load_automaton_from_text, load_initial_state


EXAMPLES = Path(__file__).resolve().parents[2] / "automata" / "examples"


def load(data):
    return load_automaton_from_text(json.dumps(data))


def description(**changes):
    return {
        "grid": {"width": 3, "height": 3},
        "rules": [{"type": "count", "from": 0, "to": 1}],
        **changes,
    }


@pytest.mark.parametrize("name", ["life", "brians_brain", "rule30", "diffusion"])
def test_examples_load_and_run(name):
    automaton = load_automaton(EXAMPLES / f"{name}.json")
    assert isinstance(automaton, Automaton)
    initial = load_initial_state(automaton).grid
    result = step(automaton, State(initial.copy()))
    assert list(result.grid.shape) == automaton.grid_size
    assert result.generation == 1
    if name != "brians_brain":
        np.testing.assert_array_equal(initial, automaton.init)
    if name == "life":
        np.testing.assert_array_equal(step(automaton, result).grid, initial)
    elif name == "brians_brain":
        assert set(np.unique(result.grid)) <= {0, 1, 2}
    elif name == "rule30":
        np.testing.assert_array_equal(result.grid, [[0, 0, 1, 1, 1, 0, 0]])
    else:
        np.testing.assert_allclose(result.grid, [[0, .2, 0], [.2, .2, .2], [0, .2, 0]])


def test_defaults_and_independent_rows():
    automaton = load({"rules": [{"type": "count", "from": 0, "to": 1}]})
    assert automaton.grid_size == [50, 50]
    assert automaton.boundary == "toroidal"
    assert automaton.states == [0, 1]
    assert automaton.neighborhood == {"type": "moore", "radius": 1}
    assert automaton.init == [[0] * 50 for _ in range(50)]
    automaton.init[0][0] = 1
    assert automaton.init[1][0] == 0


def test_file_and_text_are_equivalent():
    path = EXAMPLES / "life.json"
    assert load_automaton(path) == load_automaton_from_text(path.read_text(encoding="utf-8"))


def test_utf8_bom_file(tmp_path):
    path = tmp_path / "automat.json"
    path.write_text(json.dumps(description()), encoding="utf-8-sig")
    assert load_automaton(path).grid_size == [3, 3]


def test_missing_file(tmp_path):
    with pytest.raises(ValueError, match="Fisierul nu exista"):
        load_automaton(tmp_path / "absent.json")


def test_unreadable_directory(tmp_path):
    with pytest.raises(ValueError, match="nu poate fi citit"):
        load_automaton(tmp_path)


def test_invalid_encoding(tmp_path):
    path = tmp_path / "invalid.json"
    path.write_bytes(b"\xff\xff")
    with pytest.raises(ValueError, match="UTF-8"):
        load_automaton(path)


def test_broken_file(tmp_path):
    path = tmp_path / "broken.json"
    path.write_text('{"grid":', encoding="utf-8")
    with pytest.raises(ValueError, match="JSON invalid la linia 1, coloana"):
        load_automaton(path)


@pytest.mark.parametrize("text, message", [
    ("[]", "automat"),
    ("null", "automat"),
    ('{"rules": [], "rules": []}', "apare de doua ori"),
    ('{"init": NaN}', "numar finit"),
    ('{"init": Infinity}', "numar finit"),
    ('{"init": ' + '9' * 5000 + '}', "numar prea mare"),
    (None, "se asteapta text"),
])
def test_invalid_text(text, message):
    with pytest.raises(ValueError, match=message):
        load_automaton_from_text(text)


@pytest.mark.parametrize("changes, message", [
    ({"version": 2}, "version"),
    ({"version": True}, "version"),
    ({"unexpected": 1}, "necunoscute"),
    ({"grid": None}, "grid"),
    ({"grid": {"width": 0}}, "grid.width"),
    ({"grid": {"height": True}}, "grid.height"),
    ({"grid": {"boundary": "toroidal"}}, "grid.boundary"),
    ({"neighborhood": {"radius": 0}}, "radius"),
    ({"neighborhood": {"type": "other"}}, "neighborhood.type"),
    ({"states": [0, 0]}, "duplicate"),
    ({"states": [False, 1]}, "states"),
    ({"states": [1, 2], "grid": {"boundary": "fixed"}}, "starea 0"),
    ({"init": [[0]]}, "init"),
    ({"init": [[0], [0], [0]]}, "lungime"),
    ({"init": [[0, 0, 2]] * 3}, "stare nedeclarata"),
    ({"init": [[0, 0, True]] * 3}, "numar"),
    ({"rules": []}, "rules"),
    ({"rules": [None]}, "rules"),
    ({"rules": [{"type": "other"}]}, "tip necunoscut"),
    ({"rules": [{"type": "count", "from": 0}]}, "lipsesc to"),
    ({"rules": [{"type": "count", "from": 0, "to": 2}]}, "stare nedeclarata"),
    ({"rules": [{"type": "count", "from": 0, "to": 1, "count": 1}]}, "impreuna"),
])
def test_invalid_description(changes, message):
    with pytest.raises(ValueError, match=message):
        load(description(**changes))


@pytest.mark.parametrize("counts", [[9], [-1], [True], [1, 1], []])
def test_invalid_counts(counts):
    rule = {"type": "count", "from": 0, "count": 1, "in": counts, "to": 1, "otherwise": 0}
    with pytest.raises(ValueError, match=r"rules\[0\].in"):
        load(description(rules=[rule]))


def test_first_from_rule_decides_even_when_condition_fails():
    automaton = load(description(rules=[
        {"type": "count", "from": 0, "count": 1, "in": [1], "to": 1, "otherwise": 0},
        {"type": "count", "from": 0, "to": 1},
    ]))
    assert not step(automaton, State(np.array(automaton.init))).grid.any()


def test_wrap_single_row_counts_only_horizontal_offsets():
    automaton = load(description(
        grid={"width": 3, "height": 1, "boundary": "wrap"},
        rules=[{"type": "count", "from": 0, "count": 1, "in": [1], "to": 1, "otherwise": 0}],
        init=[[1, 0, 0]],
    ))
    assert automaton.boundary == "toroidal"
    np.testing.assert_array_equal(step(automaton, State(np.array(automaton.init))).grid, [[1, 1, 1]])


def test_fixed_boundary_counts_zero_outside_grid():
    automaton = load(description(
        rules=[{"type": "count", "from": 0, "count": 0, "in": [8], "to": 1, "otherwise": 0}],
    ))
    assert step(automaton, State(np.array(automaton.init))).grid.all()


@pytest.mark.parametrize("expression", ["celula.__class__", "open('x')", "media()", "1 < celula < 3", "nord_est", "celula ** 2", "("])
def test_invalid_numeric_expression(expression):
    with pytest.raises(ValueError, match="rules.expression"):
        load(description(states=["number"], neighborhood={"type": "von_neumann"},
                         rules=[{"type": "numeric", "expression": expression}]))


def test_nonfinite_numeric_init():
    text = json.dumps(description(states=["number"], init=[[0, 0, 0]] * 3,
                                 rules=[{"type": "numeric", "expression": "celula"}]))
    with pytest.raises(ValueError, match="finit"):
        load_automaton_from_text(text.replace('"init": [[0', '"init": [[1e999'))


def test_incomplete_table():
    data = json.loads((EXAMPLES / "rule30.json").read_text(encoding="utf-8"))
    del data["rules"][0]["table"]["000"]
    with pytest.raises(ValueError, match="lipsesc 000"):
        load(data)
