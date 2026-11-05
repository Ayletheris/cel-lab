import numpy as np

from cellab.core.neighborhood import make_kernel
from cellab.core.rules import apply_rules


KERNEL = make_kernel("moore")
LIFE_RULES = [
    {"state": 0, "neighbor_state": 1, "counts": [3], "next_state": 1},
    {"state": 1, "neighbor_state": 1, "counts": [2, 3], "next_state": 1},
    {"state": 1, "next_state": 0},
]
BRAIN_RULES = [
    {"state": 0, "neighbor_state": 1, "counts": [2], "next_state": 1},
    {"state": 1, "next_state": 2},
    {"state": 2, "next_state": 0},
]


def test_life_blinker_oscillates_without_mutating_input():
    original = np.array(
        [[0, 0, 0, 0, 0], [0, 0, 1, 0, 0], [0, 0, 1, 0, 0],
         [0, 0, 1, 0, 0], [0, 0, 0, 0, 0]]
    )
    horizontal = np.array(
        [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 1, 1, 1, 0],
         [0, 0, 0, 0, 0], [0, 0, 0, 0, 0]]
    )
    next_grid = apply_rules(original, LIFE_RULES, KERNEL)
    np.testing.assert_array_equal(next_grid, horizontal)
    np.testing.assert_array_equal(apply_rules(next_grid, LIFE_RULES, KERNEL), original)
    assert original[1, 2] == 1


def test_life_block_remains_stable():
    block = np.array([[0, 0, 0, 0], [0, 1, 1, 0], [0, 1, 1, 0], [0, 0, 0, 0]])
    np.testing.assert_array_equal(apply_rules(block, LIFE_RULES, KERNEL), block)


def test_otherwise_applies_only_after_conditional_rules():
    block = np.array([[0, 0, 0, 0], [0, 1, 1, 0], [0, 1, 1, 0], [0, 0, 0, 0]])
    reordered = [LIFE_RULES[2], *LIFE_RULES[:2]]
    np.testing.assert_array_equal(apply_rules(block, reordered, KERNEL), block)


def test_brians_brain_birth_and_dying():
    original = np.zeros((5, 5), dtype=int)
    original[2, 2:4] = 1
    expected = np.zeros((5, 5), dtype=int)
    expected[1, 2:4] = 1
    expected[2, 2:4] = 2
    expected[3, 2:4] = 1
    np.testing.assert_array_equal(apply_rules(original, BRAIN_RULES, KERNEL), expected)


def test_brians_brain_dying_cells_turn_off():
    grid = np.array([[2, 0, 0], [0, 1, 0], [0, 0, 0]])
    expected = np.array([[0, 0, 0], [0, 2, 0], [0, 0, 0]])
    np.testing.assert_array_equal(apply_rules(grid, BRAIN_RULES, KERNEL), expected)
