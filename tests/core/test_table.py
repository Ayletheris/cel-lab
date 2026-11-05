import numpy as np
import pytest

from cellab.core.table import apply_table, make_table

RULE30_TABLE = {"111": 0, "110": 0, "101": 0, "100": 1, "011": 1, "010": 1, "001": 1, "000": 0}


def start(width=15):
    grid = np.zeros(width, dtype=np.uint8)
    grid[width // 2] = 1
    return grid


def rows(rule, steps, boundary="toroidal"):
    grid = start()
    out = [grid]
    for _ in range(steps):
        grid = apply_table(grid, rule, boundary)
        out.append(grid)
    return ["".join(str(c) for c in r) for r in out]


def test_rule30_first_rows():
    assert rows(30, 4) == [
        "000000010000000",
        "000000111000000",
        "000001100100000",
        "000011011110000",
        "000110010001000",
    ]


def test_rule90_makes_sierpinski():
    assert rows(90, 3) == [
        "000000010000000",
        "000000101000000",
        "000001000100000",
        "000010101010000",
    ]


def test_table_dict_same_as_wolfram_number():
    assert make_table(30) == RULE30_TABLE
    assert rows(RULE30_TABLE, 4) == rows(30, 4)


def test_fixed_and_toroidal_differ_at_edge():
    grid = np.zeros(5, dtype=np.uint8)
    grid[0] = 1
    fixed = apply_table(grid, 30, "fixed")
    wrap = apply_table(grid, 30, "toroidal")
    assert not np.array_equal(fixed, wrap)


def test_one_row_grid_and_input_not_changed():
    grid = start()[np.newaxis, :]
    before = grid.copy()
    out = apply_table(grid, 30)
    assert out.shape == grid.shape
    np.testing.assert_array_equal(grid, before)


def test_bad_rules_are_refused():
    with pytest.raises(ValueError):
        make_table(256)
    with pytest.raises(ValueError):
        make_table({"111": 0})
    with pytest.raises(ValueError):
        apply_table(np.zeros((3, 3), dtype=np.uint8), 30)
