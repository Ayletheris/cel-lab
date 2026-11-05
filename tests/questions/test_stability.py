from pathlib import Path

import pytest

from cellab.cli.commands import main
from cellab.io import load_automaton, load_initial_state
from cellab.questions.stability import find_cycle, find_stable, generation_in_cycle, grid_hash

EXAMPLES = Path(__file__).resolve().parents[2] / "automata" / "examples"

BLOCK_5X5 = """.....
.##..
.##..
.....
....."""


def load(name, source=None):
    automaton = load_automaton(EXAMPLES / name)
    return automaton, load_initial_state(automaton, source)


def test_block_is_stable_from_the_start():
    automaton, state = load("life.json", BLOCK_5X5)
    assert find_stable(automaton, state) == 0
    assert find_cycle(automaton, state) == (0, 1)


def test_blinker_is_not_stable_but_has_cycle_of_2():
    automaton, state = load("life.json")
    assert find_stable(automaton, state, max_steps=50) is None
    assert find_cycle(automaton, state) == (0, 2)


def test_glider_on_torus_comes_back():
    # game_of_life.json e 8x8 cu wrap; glider-ul revine dupa 4 * 8 = 32 generatii
    automaton, state = load("game_of_life.json", EXAMPLES / "glider.txt")
    assert find_cycle(automaton, state) == (0, 32)


def test_forest_fire_burns_out_and_stays():
    automaton, state = load("forest_fire.json")
    generation = find_stable(automaton, state)
    assert generation is not None and generation > 0
    mu, lam = find_cycle(automaton, state)
    assert lam == 1 and mu == generation


def test_limit_gives_none():
    automaton, state = load("game_of_life.json", EXAMPLES / "glider.txt")
    assert find_cycle(automaton, state, max_steps=10) is None


def test_random_automaton_is_refused():
    automaton, state = load("forest_fire_random.json")
    with pytest.raises(ValueError):
        find_stable(automaton, state)
    with pytest.raises(ValueError):
        find_cycle(automaton, state)


def test_generation_in_cycle():
    assert generation_in_cycle(1001, 0, 2) == 1
    assert generation_in_cycle(1000, 0, 2) == 0
    assert generation_in_cycle(3, 5, 4) == 3  # inainte sa inceapa ciclul
    assert generation_in_cycle(14, 5, 4) == 6  # 5 + (14 - 5) % 4


def test_hash_same_for_same_grid():
    automaton, state = load("life.json")
    assert grid_hash(state.grid) == grid_hash(state.grid.copy())
    other = state.grid.copy()
    other[0, 0] = 1
    assert grid_hash(state.grid) != grid_hash(other)


def test_cli_stable_and_cycle(capsys):
    assert main(["stable", str(EXAMPLES / "forest_fire.json")]) == 0
    assert "stabil de la generatia" in capsys.readouterr().out

    assert main(["stable", str(EXAMPLES / "life.json"), "--max-steps", "20"]) == 0
    assert "nu devine stabil in primii 20 pasi" in capsys.readouterr().out

    assert main(["cycle", str(EXAMPLES / "life.json"), "--generations", "1001"]) == 0
    out = capsys.readouterr().out
    assert "incepe la generatia 0, lungime 2" in out
    assert "generatia 1001 e aceeasi cu starea la generatia 1" in out


def test_cli_random_automaton_short_error(capsys):
    assert main(["cycle", str(EXAMPLES / "forest_fire_random.json")]) == 2
    assert "probabilitate" in capsys.readouterr().err
