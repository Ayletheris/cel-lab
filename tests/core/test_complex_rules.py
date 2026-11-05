import json

import numpy as np

from cellab.core.model import Automaton
from cellab.core.neighborhood import make_kernel
from cellab.core.rules import apply_rules


def test_voter_rule_from_json_with_zero_fixed_boundary():
    automaton = Automaton(**json.loads(
        '{"grid_size":[3,3],"boundary":"fixed","states":[0,1],'
        '"neighborhood":"moore","rules":['
        '{"condition":{"more_than":[1,0]},"next_state":1},'
        '{"condition":{"more_than":[0,1]},"next_state":0}]}'
    ))
    grid = np.array([[0, 0, 0], [0, 1, 1], [0, 1, 1]])
    expected = np.zeros((3, 3), dtype=int)
    np.testing.assert_array_equal(
        apply_rules(grid, automaton.rules, make_kernel(automaton.neighborhood), automaton.boundary),
        expected,
    )


def test_cyclic_rule_from_json():
    automaton = Automaton(**json.loads(
        '{"grid_size":[3,3],"boundary":"fixed","states":[0,1,2],'
        '"neighborhood":"moore","rules":['
        '{"condition":{"neighbor_state":{"next_mod":3},"at_least":2},'
        '"next_state":{"next_mod":3}}]}'
    ))
    grid = np.array([[0, 1, 0], [1, 0, 2], [0, 2, 0]])
    expected = np.array([[1, 1, 0], [1, 1, 0], [0, 0, 0]])
    np.testing.assert_array_equal(
        apply_rules(grid, automaton.rules, make_kernel(automaton.neighborhood), automaton.boundary),
        expected,
    )
    assert grid[1, 1] == 0


def test_and_or_and_count_ranges():
    grid = np.array([[1, 0, 0], [0, 0, 0], [0, 0, 0]])
    rules = [
        {
            "state": 0,
            "condition": {
                "all": [
                    {"neighbor_state": 1, "at_least": 1},
                    {"neighbor_state": 1, "at_most": 1},
                    {
                        "any": [
                            {"neighbor_state": 1, "exact": 1},
                            {"neighbor_state": 1, "between": [2, 3]},
                        ]
                    },
                ]
            },
            "next_state": 1,
        }
    ]
    expected = np.array([[1, 1, 0], [1, 1, 0], [0, 0, 0]])
    np.testing.assert_array_equal(apply_rules(grid, rules, make_kernel("moore")), expected)


def test_between_branch_of_or():
    grid = np.array([[1, 1, 0], [0, 0, 0], [0, 0, 0]])
    rules = [{
        "state": 0,
        "condition": {"all": [
            {"neighbor_state": 1, "at_least": 2},
            {"neighbor_state": 1, "at_most": 2},
            {"any": [
                {"neighbor_state": 1, "exact": 3},
                {"neighbor_state": 1, "between": [2, 3]},
            ]},
        ]},
        "next_state": 2,
    }]
    expected = np.array([[1, 1, 0], [2, 2, 0], [0, 0, 0]])
    np.testing.assert_array_equal(apply_rules(grid, rules, make_kernel("moore")), expected)
