import numpy as np
import pytest

from cellab.core.model import Automaton, State
from cellab.core.step import step

LIFE_RULES = [
    {"state": 0, "neighbor_state": 1, "counts": [3], "next_state": 1},
    {"state": 1, "neighbor_state": 1, "counts": [2, 3], "next_state": 1},
    {"state": 1, "next_state": 0},
]
# 0 = stinsa, 1 = aprinsa, 2 = murind
BRAIN_RULES = [
    {"state": 0, "condition": {"neighbor_state": 1, "exact": 2}, "next_state": 1},
    {"state": 1, "next_state": 2},
    {"state": 2, "next_state": 0},
]


def make_automaton(rules, neighborhood="moore", boundary="toroidal", size=(5, 5)):
    return Automaton(
        grid_size=list(size),
        boundary=boundary,
        states=[0, 1],
        neighborhood=neighborhood,
        rules=rules,
    )


def test_life_blinker_with_step_and_generation_counter():
    grid = np.zeros((5, 5), dtype=np.uint8)
    grid[2, 1:4] = 1
    life = make_automaton(LIFE_RULES)

    state1 = step(life, State(grid))
    state2 = step(life, state1)

    assert state1.generation == 1
    assert state2.generation == 2
    assert state1.grid[1:4, 2].all() and state1.grid.sum() == 3
    np.testing.assert_array_equal(state2.grid, grid)


def test_brians_brain_with_step():
    grid = np.zeros((5, 5), dtype=np.uint8)
    grid[1, 1] = 1
    grid[1, 3] = 1
    brain = make_automaton(BRAIN_RULES, boundary="fixed")

    new_state = step(brain, State(grid))

    assert new_state.grid[1, 1] == 2
    assert new_state.grid[1, 3] == 2
    assert new_state.grid[1, 2] == 1


def test_rule30_with_step():
    grid = np.zeros(15, dtype=np.uint8)
    grid[7] = 1
    rule30 = make_automaton({"type": "table", "table": 30}, neighborhood=[-1, 1], size=(15, 1))

    new_state = step(rule30, State(grid))

    assert "".join(str(c) for c in new_state.grid) == "000000111000000"


def test_diffusion_with_step():
    grid = np.zeros((3, 3))
    grid[1, 1] = 100
    diffusion = make_automaton(
        {"type": "numeric", "expression": "media(celula, nord, sud, est, vest)"},
        boundary="fixed",
        size=(3, 3),
    )

    new_state = step(diffusion, State(grid))

    assert new_state.grid[1, 1] == 20
    assert new_state.grid[0, 1] == 20
    assert new_state.generation == 1


def test_old_state_is_not_changed():
    grid = np.zeros((5, 5), dtype=np.uint8)
    grid[2, 1:4] = 1
    old_state = State(grid.copy(), generation=7)

    step(make_automaton(LIFE_RULES), old_state)

    np.testing.assert_array_equal(old_state.grid, grid)
    assert old_state.generation == 7


def test_radius_from_dict_neighborhood():
    # cu raza 2 vecinii sunt la 2 pasi distanta, nu doar la 1
    rules = [{"state": 0, "condition": {"neighbor_state": 1, "at_least": 1}, "next_state": 1}]
    grid = np.zeros((5, 5), dtype=np.uint8)
    grid[0, 2] = 1
    near = make_automaton(rules, neighborhood={"type": "moore", "radius": 1}, boundary="fixed")
    far = make_automaton(rules, neighborhood={"type": "moore", "radius": 2}, boundary="fixed")

    assert step(near, State(grid)).grid.sum() == 6
    assert step(far, State(grid)).grid.sum() == 15


def test_probability_rules_use_rng_and_are_reproducible():
    rules = [{"state": 0, "prob": 0.5, "next_state": 1}]
    automaton = make_automaton(rules)
    grid = np.zeros((10, 10), dtype=np.uint8)

    first = step(automaton, State(grid), np.random.default_rng(3))
    second = step(automaton, State(grid), np.random.default_rng(3))

    np.testing.assert_array_equal(first.grid, second.grid)
    assert 0 < first.grid.sum() < 100


def test_bad_rules_type_is_refused():
    state = State(np.zeros((3, 3), dtype=np.uint8))
    with pytest.raises(ValueError):
        step(make_automaton({"type": "magic"}), state)
    with pytest.raises(ValueError):
        step(make_automaton("nu sunt reguli"), state)
