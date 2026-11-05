import numpy as np
import pytest

from cellab.core.neighborhood import make_kernel
from cellab.core.rules import apply_rules

KERNEL = make_kernel("moore")
# 0 = gol, 1 = copac, 2 = foc (padure)
FOREST = [
    {"state": 2, "next_state": 0},
    {"state": 1, "condition": {"neighbor_state": 2, "at_least": 1}, "next_state": 2},
    {"state": 1, "prob": 0.3, "next_state": 2},  # foc spontan
    {"state": 0, "prob": 0.5, "next_state": 1},  # copac nou
]


def run(seed, steps=5):
    rng = np.random.default_rng(seed)
    grid = rng.integers(0, 2, size=(20, 20)).astype(np.uint8)
    for _ in range(steps):
        grid = apply_rules(grid, FOREST, KERNEL, "toroidal", rng)
    return grid


def test_same_seed_same_result():
    np.testing.assert_array_equal(run(1), run(1))


def test_different_seed_different_result():
    assert not np.array_equal(run(1), run(2))


def test_prob_zero_never_applies():
    grid = np.zeros((10, 10), dtype=np.uint8)
    rule = [{"state": 0, "prob": 0, "next_state": 1}]
    out = apply_rules(grid, rule, KERNEL, rng=np.random.default_rng(0))
    assert out.sum() == 0


def test_prob_one_always_applies():
    grid = np.zeros((10, 10), dtype=np.uint8)
    rule = [{"state": 0, "prob": 1, "next_state": 1}]
    out = apply_rules(grid, rule, KERNEL, rng=np.random.default_rng(0))
    assert out.sum() == 100


def test_prob_about_right():
    grid = np.zeros((100, 100), dtype=np.uint8)
    rule = [{"state": 0, "prob": 0.3, "next_state": 1}]
    out = apply_rules(grid, rule, KERNEL, rng=np.random.default_rng(0))
    assert 2700 < out.sum() < 3300


def test_failed_prob_goes_to_next_rule():
    grid = np.zeros((10, 10), dtype=np.uint8)
    rules = [{"state": 0, "prob": 0, "next_state": 1}, {"state": 0, "next_state": 2}]
    out = apply_rules(grid, rules, KERNEL, rng=np.random.default_rng(0))
    assert (out == 2).all()


def test_prob_without_rng_is_refused():
    with pytest.raises(ValueError):
        apply_rules(np.zeros((3, 3), dtype=np.uint8), [{"prob": 0.5, "next_state": 1}], KERNEL)


def test_prob_out_of_range_is_refused():
    with pytest.raises(ValueError):
        apply_rules(np.zeros((3, 3), dtype=np.uint8), [{"prob": 1.5, "next_state": 1}], KERNEL, rng=np.random.default_rng(0))
