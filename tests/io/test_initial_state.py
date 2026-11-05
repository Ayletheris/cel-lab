import json

import numpy as np
import pytest

from cellab.core.model import State
from cellab.core.step import step
from cellab.io import load_automaton, load_initial_state, load_initial_state_from_file
from tests.io.test_load import EXAMPLES


BLINKER = ". # .\n. # .\n. # ."
GLIDER = ". # .\n. . #\n# # #"


def automaton(size=(3, 3), states=None):
    life = load_automaton(EXAMPLES / "life.json")
    life.grid_size = list(size)
    if states is not None:
        life.states = states
    return life


def test_blinker_from_text_runs_with_period_two():
    life = automaton()
    state = load_initial_state(life, BLINKER)
    assert isinstance(state, State)
    assert state.generation == 0
    np.testing.assert_array_equal(state.grid, [[0, 1, 0]] * 3)
    next_state = step(life, state)
    np.testing.assert_array_equal(next_state.grid, [[0, 0, 0], [1, 1, 1], [0, 0, 0]])
    np.testing.assert_array_equal(step(life, next_state).grid, state.grid)


def test_glider_from_text_moves_diagonally_after_four_steps():
    life = automaton((5, 5))
    text = ".#...\n..#..\n###..\n.....\n....."
    state = load_initial_state(life, text)
    expected = np.roll(state.grid, (1, 1), axis=(0, 1))
    for _ in range(4):
        state = step(life, state)
    np.testing.assert_array_equal(state.grid, expected)


@pytest.mark.parametrize("source", [
    [[0, 1, 0]] * 3,
    ((0, 1, 0),) * 3,
    np.array([[0, 1, 0]] * 3),
    BLINKER,
    ".#.\n.#.\n.#.",
    "\n  . # .\n  .\t#\t.\n  . # .\n\n",
])
def test_equivalent_sources(source):
    state = load_initial_state(automaton(), source)
    np.testing.assert_array_equal(state.grid, [[0, 1, 0]] * 3)
    assert state.generation == 0


def test_default_source_uses_automaton_init_without_sharing_memory():
    life = load_automaton(EXAMPLES / "life.json")
    state = load_initial_state(life)
    state.grid[0, 0] = 1
    assert life.init[0][0] == 0


def test_numpy_source_is_copied():
    source = np.zeros((3, 3), dtype=int)
    state = load_initial_state(automaton(), source)
    state.grid[0, 0] = 1
    assert source[0, 0] == 0


def test_custom_symbols_for_three_states():
    state = load_initial_state(automaton((1, 3), [0, 1, 2]), ".#x", {".": 0, "#": 1, "x": 2})
    np.testing.assert_array_equal(state.grid, [[0, 1, 2]])


def test_numeric_domain_preserves_fractional_values():
    state = load_initial_state(automaton((1, 3), ["number"]), [[0, .25, -2.5]])
    np.testing.assert_array_equal(state.grid, [[0, .25, -2.5]])
    assert np.issubdtype(state.grid.dtype, np.floating)


@pytest.mark.parametrize("source, message", [
    ([[0, 1, 0]], "3 randuri si 3 coloane"),
    ([[0, 1], [0, 1, 0], [0, 1, 0]], "Randul 1.*3 coloane"),
    ([], "3 randuri"),
    ("", "3 randuri"),
    ("...\n...", "3 randuri"),
    ("..\n..\n..", "Randul 1.*3 coloane"),
    ("....\n....\n....", "Randul 1.*3 coloane"),
    (". # .\n. #\n. # .", "Randul 2.*3 coloane"),
    (np.zeros(9), "matrice 2D"),
    ([[0, 2, 0]] * 3, "Stare nedeclarata 2.*linia 1, coloana 2"),
    ([[0, .5, 0]] * 3, "Stare nedeclarata 0.5"),
    ([[0, True, 0]] * 3, "nenumerica"),
    ([[0, "1", 0]] * 3, "nenumerica"),
    ([[0, float("nan"), 0]] * 3, "finit"),
    ([[0, float("inf"), 0]] * 3, "finit"),
    (".x.\n...\n...", "Caracter necunoscut 'x'.*linia 1, coloana 2"),
])
def test_invalid_sources_have_clear_errors(source, message):
    with pytest.raises(ValueError, match=message):
        load_initial_state(automaton(), source)


@pytest.mark.parametrize("symbols", [[], {"xx": 1}, {" ": 0}, {0: 0}])
def test_invalid_symbol_mapping(symbols):
    with pytest.raises(ValueError, match="Legenda"):
        load_initial_state(automaton(), BLINKER, symbols)


def test_symbol_must_map_to_a_declared_state():
    with pytest.raises(ValueError, match="Stare nedeclarata 7"):
        load_initial_state(automaton(), BLINKER, {".": 0, "#": 7})


@pytest.mark.parametrize("text, expected", [
    (BLINKER, [[0, 1, 0]] * 3),
    (GLIDER, [[0, 1, 0], [0, 0, 1], [1, 1, 1]]),
])
def test_text_files_support_paths_and_utf8_bom(tmp_path, text, expected):
    path = tmp_path / "pattern.txt"
    path.write_text(text, encoding="utf-8-sig")
    np.testing.assert_array_equal(load_initial_state(automaton(), path).grid, expected)
    np.testing.assert_array_equal(load_initial_state_from_file(automaton(), str(path)).grid, expected)


def test_json_matrix_file(tmp_path):
    path = tmp_path / "matrix.json"
    matrix = [[0, 1, 0]] * 3
    path.write_text(json.dumps(matrix), encoding="utf-8")
    np.testing.assert_array_equal(load_initial_state_from_file(automaton(), path).grid, matrix)


@pytest.mark.parametrize("text, message", [
    ("[", "JSON invalid la linia 1, coloana"),
    ("[[0]]", "3 randuri"),
    ('{"grid": []}', "matrice de numere"),
    ("null", "matrice de numere"),
    ('"..."', "matrice de numere"),
    ("[[0,2,0],[0,0,0],[0,0,0]]", "Stare nedeclarata"),
])
def test_invalid_json_files(tmp_path, text, message):
    path = tmp_path / "bad.json"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(ValueError, match=message):
        load_initial_state_from_file(automaton(), path)


def test_missing_file(tmp_path):
    with pytest.raises(ValueError, match="Fisierul nu exista"):
        load_initial_state_from_file(automaton(), tmp_path / "missing.txt")


def test_invalid_utf8_file(tmp_path):
    path = tmp_path / "bad.txt"
    path.write_bytes(b"\xff")
    with pytest.raises(ValueError, match="UTF-8"):
        load_initial_state_from_file(automaton(), path)


def test_missing_initial_state():
    life = automaton()
    life.init = None
    with pytest.raises(ValueError, match="Starea initiala lipseste"):
        load_initial_state(life)


@pytest.mark.parametrize("size", [[0, 3], [-1, 3], [3], None])
def test_invalid_automaton_size(size):
    life = automaton()
    life.grid_size = size
    with pytest.raises(ValueError, match="Grila"):
        load_initial_state(life, BLINKER)
