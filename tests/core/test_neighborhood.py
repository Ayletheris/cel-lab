import numpy as np
import pytest

from cellab.core.neighborhood import make_kernel


def test_moore_radius_one():
    kernel = make_kernel("moore")
    assert kernel.shape == (3, 3)
    assert kernel.sum() == 8
    assert kernel[1, 1] == 0


def test_von_neumann_radius_one():
    kernel = make_kernel("von Neumann")
    assert kernel.shape == (3, 3)
    np.testing.assert_array_equal(kernel, [[0, 1, 0], [1, 0, 1], [0, 1, 0]])


@pytest.mark.parametrize("kind, count", [("moore", 24), ("von_neumann", 12)])
def test_radius_two(kind, count):
    kernel = make_kernel(kind, radius=2)
    assert kernel.shape == (5, 5)
    assert kernel.sum() == count
    assert kernel[2, 2] == 0


def test_one_dimensional_offsets():
    np.testing.assert_array_equal(make_kernel([-2, 1], radius=2), [1, 0, 0, 1, 0])


def test_one_dimensional_offsets_define_their_own_radius():
    np.testing.assert_array_equal(make_kernel([-2, 1]), [1, 0, 0, 1, 0])
