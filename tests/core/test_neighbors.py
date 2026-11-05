import numpy as np
import pytest

from cellab.core.neighborhood import make_kernel
from cellab.core.neighbors import count_neighbors


def test_boat_example_prefix():
    grid = np.array(
        [
            [0, 0, 0, 0, 0],
            [0, 1, 1, 0, 0],
            [0, 1, 0, 1, 0],
            [0, 0, 1, 0, 0],
            [0, 0, 0, 0, 0],
        ]
    )
    counts = count_neighbors(grid, 1, make_kernel("moore"))
    np.testing.assert_array_equal(counts[0], [1, 2, 2, 1, 0])
    np.testing.assert_array_equal(counts[1], [2, 2, 3, 2, 1])


@pytest.mark.parametrize(
    "boundary, expected",
    [
        ("fixed", [[0, 1, 0], [1, 1, 0], [0, 0, 0]]),
        ("toroidal", [[0, 1, 1], [1, 1, 1], [1, 1, 1]]),
    ],
)
def test_corner_neighbors(boundary, expected):
    grid = np.array([[1, 0, 0], [0, 0, 0], [0, 0, 0]])
    np.testing.assert_array_equal(count_neighbors(grid, 1, make_kernel("moore"), boundary), expected)


def test_counts_only_target_state():
    grid = np.array([[2, 0, 0], [0, 1, 0], [0, 0, 0]])
    counts = count_neighbors(grid, 2, make_kernel("von_neumann"))
    assert counts[1, 1] == 0
    assert counts[0, 1] == 1


def test_one_dimensional_neighbors():
    grid = np.array([1, 0, 0, 1])
    np.testing.assert_array_equal(
        count_neighbors(grid, 1, make_kernel([-1, 1]), "toroidal"), [1, 1, 1, 1]
    )


def test_asymmetric_one_dimensional_offsets():
    grid = np.array([0, 0, 1, 0, 0])
    np.testing.assert_array_equal(
        count_neighbors(grid, 1, make_kernel([-2, 1], radius=2)), [0, 1, 0, 0, 1]
    )
