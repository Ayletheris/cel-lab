import numpy as np
import pytest

from cellab.core.numeric import apply_numeric

DIFFUSION = "media(celula, nord, sud, est, vest)"
SANDPILE = "celula - 4*(celula >= 4) + (nord >= 4) + (sud >= 4) + (est >= 4) + (vest >= 4)"


def test_diffusion_one_step():
    grid = np.zeros((3, 3))
    grid[1, 1] = 100
    out = apply_numeric(grid, DIFFUSION, "fixed")
    expected = np.array([[0, 20, 0], [20, 20, 20], [0, 20, 0]])
    np.testing.assert_allclose(out, expected)


def test_diffusion_keeps_sum_and_evens_out_on_torus():
    grid = np.zeros((3, 3))
    grid[1, 1] = 100
    for _ in range(200):
        grid = apply_numeric(grid, DIFFUSION, "toroidal")
    assert grid.sum() == pytest.approx(100)
    np.testing.assert_allclose(grid, np.full((3, 3), 100 / 9), atol=0.01)


def test_sandpile_one_step():
    grid = np.array([[0, 1, 2], [2, 8, 1], [1, 2, 0]])
    out = apply_numeric(grid, SANDPILE, "fixed")
    expected = np.array([[0, 2, 2], [3, 4, 2], [1, 3, 0]])
    np.testing.assert_array_equal(out, expected)


def test_sandpile_stops_at_some_point():
    grid = np.array([[0, 1, 2], [2, 8, 1], [1, 2, 0]])
    for _ in range(100):
        grid = apply_numeric(grid, SANDPILE, "fixed")
    assert grid.max() < 4


def test_comparisons_are_added_as_numbers():
    grid = np.array([[0, 5, 0], [0, 0, 0], [0, 5, 0]])
    # celula din mijloc are nord si sud >= 4, deci 2 (nu "True or True")
    out = apply_numeric(grid, "(nord >= 4) + (sud >= 4)", "fixed")
    assert out[1, 1] == 2


def test_min_max_suma_and_plain_number():
    grid = np.array([[1, 7], [3, 9]])
    np.testing.assert_array_equal(apply_numeric(grid, "max(celula, 5)", "fixed"), [[5, 7], [5, 9]])
    np.testing.assert_array_equal(apply_numeric(grid, "min(celula, 5)", "fixed"), [[1, 5], [3, 5]])
    np.testing.assert_array_equal(apply_numeric(grid, "suma(celula, 1)", "fixed"), [[2, 8], [4, 10]])
    np.testing.assert_array_equal(apply_numeric(grid, "5", "fixed"), [[5, 5], [5, 5]])


def test_input_not_changed():
    grid = np.array([[0, 1, 2], [2, 8, 1], [1, 2, 0]])
    before = grid.copy()
    apply_numeric(grid, SANDPILE, "fixed")
    np.testing.assert_array_equal(grid, before)


@pytest.mark.parametrize(
    "expression",
    [
        "__import__('os').system('echo hi')",  # apel nepermis
        "celula ** 2",  # operatie nepermisa
        "open('x')",  # functie nepermisa
        "celula.sum()",  # atribut nepermis
        "altceva + 1",  # nume necunoscut
        "celula +",  # nu se poate citi
        "'text'",  # doar numere
        "media()",  # fara valori
    ],
)
def test_bad_expressions_are_refused(expression):
    with pytest.raises(ValueError):
        apply_numeric(np.zeros((3, 3)), expression)
