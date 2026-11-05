"""Teste cu forme cunoscute din Game of Life, rulate prin step()."""

import numpy as np

from cellab.core.model import Automaton, State
from cellab.core.step import step

LIFE_RULES = [
    {"state": 0, "neighbor_state": 1, "counts": [3], "next_state": 1},
    {"state": 1, "neighbor_state": 1, "counts": [2, 3], "next_state": 1},
    {"state": 1, "next_state": 0},
]


def life(boundary, size):
    return Automaton(
        grid_size=[size, size],
        boundary=boundary,
        states=[0, 1],
        neighborhood="moore",
        rules=LIFE_RULES,
    )


def grid_with(size, cells):
    grid = np.zeros((size, size), dtype=np.uint8)
    for row, col in cells:
        grid[row, col] = 1
    return grid


GLIDER = [(0, 1), (1, 2), (2, 0), (2, 1), (2, 2)]
BOAT = [(1, 1), (1, 2), (2, 1), (2, 3), (3, 2)]
BLOCK = [(1, 1), (1, 2), (2, 1), (2, 2)]


def run(automaton, grid, steps):
    state = State(grid)
    for _ in range(steps):
        state = step(automaton, state)
    return state


def test_block_stays_the_same():
    grid = grid_with(5, BLOCK)
    result = run(life("fixed", 5), grid, 10)
    np.testing.assert_array_equal(result.grid, grid)


def test_boat_stays_the_same():
    grid = grid_with(5, BOAT)
    result = run(life("fixed", 5), grid, 10)
    np.testing.assert_array_equal(result.grid, grid)


def test_glider_moves_one_cell_down_right_every_4_generations():
    grid = grid_with(8, GLIDER)
    result = run(life("toroidal", 8), grid, 4)
    np.testing.assert_array_equal(result.grid, np.roll(grid, (1, 1), axis=(0, 1)))


def test_glider_comes_back_on_torus():
    # pe un tor de 8x8 se intoarce dupa 4 * 8 = 32 generatii
    grid = grid_with(8, GLIDER)
    result = run(life("toroidal", 8), grid, 32)
    np.testing.assert_array_equal(result.grid, grid)
    assert result.generation == 32


def test_glider_dies_into_a_block_on_fixed_edge():
    # pe margine fixa glider-ul ajunge in colt si ramane un patrat 2x2
    grid = grid_with(8, GLIDER)
    result = run(life("fixed", 8), grid, 40)
    assert result.grid.sum() == 4


def test_fixed_and_toroidal_give_different_results_at_edge():
    grid = grid_with(5, [(0, 0), (0, 1), (0, 2)])
    fixed = run(life("fixed", 5), grid, 1)
    wrap = run(life("toroidal", 5), grid, 1)
    assert not np.array_equal(fixed.grid, wrap.grid)
