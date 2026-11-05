import copy
import json

import numpy as np
import pytest

from cellab.core.model import State
from cellab.core.step import step
from cellab.io import generate_initial_state, load_automaton, load_automaton_from_text, load_initial_state, validate
from tests.io.test_load import EXAMPLES


def description(spec, size=(5, 7), states=None):
    name = "rule30" if size[0] == 1 else "life"
    data = json.loads((EXAMPLES / f"{name}.json").read_text(encoding="utf-8"))
    data["grid"] = {"height": size[0], "width": size[1], "boundary": "wrap"}
    if states is not None:
        data["states"] = states
    data["init"] = spec
    return data


def automaton(spec, size=(5, 7)):
    return load_automaton_from_text(json.dumps(description(spec, size)))


def test_random_thirty_percent_and_seed_reproducibility():
    spec = {"type": "random", "percentages": {"1": 30}, "seed": 42}
    model = automaton(spec, (100, 100))
    first = load_initial_state(model)
    second = load_initial_state(model)
    assert isinstance(first, State) and first.generation == 0
    assert first.grid.shape == (100, 100)
    assert .28 < np.mean(first.grid == 1) < .32
    np.testing.assert_array_equal(first.grid, second.grid)
    assert not np.array_equal(first.grid, generate_initial_state(model, {**spec, "seed": 43}).grid)


@pytest.mark.parametrize("name", ["life_random", "rule30_center", "life_glider", "life_empty"])
def test_generated_examples_load_validate_and_run(name):
    model = load_automaton(EXAMPLES / f"{name}.json")
    assert validate(model) == []
    state = load_initial_state(model)
    result = step(model, state)
    assert state.generation == 0 and result.generation == 1
    assert list(result.grid.shape) == model.grid_size


def test_default_seed_is_zero_and_does_not_use_global_rng():
    spec = {"type": "random", "percentages": {"1": 30}}
    model = automaton(spec)
    before = np.random.get_state()
    first = load_initial_state(model)
    after = np.random.get_state()
    assert before[0] == after[0] and before[2:] == after[2:]
    np.testing.assert_array_equal(before[1], after[1])
    np.testing.assert_array_equal(first.grid, generate_initial_state(model, {**spec, "seed": 0}).grid)


def test_partial_and_complete_percentages_are_equivalent():
    model = automaton({"type": "empty"}, (100, 100))
    partial = {"type": "random", "percentages": {"1": 30}, "seed": 13}
    complete = {**partial, "percentages": {"0": 70, "1": 30}}
    np.testing.assert_array_equal(generate_initial_state(model, partial).grid,
                                  generate_initial_state(model, complete).grid)


def test_percentage_key_order_does_not_change_seeded_result():
    model = automaton({"type": "empty"})
    model.states = [0, 1, 2]
    first = {"type": "random", "percentages": {"0": 33.3, "1": 33.3, "2": 33.4}, "seed": 123}
    second = {**first, "percentages": {"2": 33.4, "1": 33.3, "0": 33.3}}
    np.testing.assert_array_equal(generate_initial_state(model, first).grid,
                                  generate_initial_state(model, second).grid)


def test_remainder_is_added_to_first_state_even_when_it_has_a_percentage():
    model = automaton({"type": "empty"})
    model.states = [2, 0, 1]
    partial = {"type": "random", "percentages": {"2": 10, "1": 20}}
    complete = {"type": "random", "percentages": {"2": 80, "1": 20}}
    state = generate_initial_state(model, partial)
    np.testing.assert_array_equal(state.grid, generate_initial_state(model, complete).grid)
    assert set(np.unique(state.grid)) <= {1, 2}


def test_empty_percentages_mean_first_state_everywhere():
    model = automaton({"type": "random", "percentages": {}})
    assert not load_initial_state(model).grid.any()


@pytest.mark.parametrize("size", [(5, 7), (4, 6), (1, 101)])
def test_center_coordinates(size):
    model = automaton({"type": "center"}, size)
    state = load_initial_state(model)
    assert state.grid.sum() == 1
    assert state.grid[size[0] // 2, size[1] // 2] == 1
    assert state.generation == 0


def test_center_with_custom_state_and_background():
    model = automaton({"type": "empty"})
    model.states = [0, 2, 5]
    state = generate_initial_state(model, {"type": "center", "state": 5, "background": 2})
    assert state.grid[2, 3] == 5
    assert np.count_nonzero(state.grid == 2) == 34


def test_numeric_center_and_empty():
    model = load_automaton(EXAMPLES / "diffusion.json")
    state = generate_initial_state(model, {"type": "center", "state": .5, "background": -.25})
    assert state.grid[1, 1] == .5
    assert np.count_nonzero(state.grid == -.25) == 8
    assert not generate_initial_state(model, {"type": "empty"}).grid.any()


@pytest.mark.parametrize("pattern", [".#.\n..#\n###", [[0, 1, 0], [0, 0, 1], [1, 1, 1]]])
def test_pattern_placement_and_no_mutation(pattern):
    spec = {"type": "pattern", "pattern": pattern, "position": {"x": 3, "y": 1}}
    before = copy.deepcopy(spec)
    model = automaton(spec)
    expected = np.zeros((5, 7), dtype=int)
    expected[1:4, 3:6] = [[0, 1, 0], [0, 0, 1], [1, 1, 1]]
    state = load_initial_state(model)
    np.testing.assert_array_equal(state.grid, expected)
    assert model.init == before and spec == before
    state.grid[:] = 0
    np.testing.assert_array_equal(load_initial_state(model).grid, expected)


def test_pattern_may_touch_last_row_and_column():
    spec = {"type": "pattern", "pattern": [[1]], "position": {"x": 6, "y": 4}}
    state = load_initial_state(automaton(spec))
    assert state.grid[4, 6] == 1 and state.grid.sum() == 1


def test_empty_uses_first_declared_state():
    model = automaton({"type": "empty"})
    model.states = [2, 0, 1]
    assert np.all(load_initial_state(model).grid == 2)
    assert not generate_initial_state(model, {"type": "empty", "background": 0}).grid.any()


@pytest.mark.parametrize("spec, message", [
    ({"type": "other"}, "tip de generare necunoscut"),
    ({"type": []}, "tip de generare necunoscut"),
    ({"type": "empty", "extra": 1}, "campuri.*necunoscute"),
    ({"type": "empty", "background": 9}, "stare nedeclarata"),
    ({"type": "center", "state": 9}, "stare nedeclarata"),
    ({"type": "center", "state": True}, "stare numerica valida"),
    ({"type": "random"}, "percentages"),
    ({"type": "random", "percentages": []}, "percentages"),
    ({"type": "random", "percentages": {"9": 30}}, "stare nedeclarata"),
    ({"type": "random", "percentages": {"01": 30}}, "cheie invalida"),
    ({"type": "random", "percentages": {"1": -1}}, "intre 0 si 100"),
    ({"type": "random", "percentages": {"1": 101}}, "intre 0 si 100"),
    ({"type": "random", "percentages": {"1": "30"}}, "intre 0 si 100"),
    ({"type": "random", "percentages": {"1": True}}, "intre 0 si 100"),
    ({"type": "random", "percentages": {"0": 80, "1": 30}}, "depaseste 100"),
    ({"type": "random", "percentages": {}, "seed": -1}, "seed"),
    ({"type": "random", "percentages": {}, "seed": True}, "seed"),
    ({"type": "random", "percentages": {}, "seed": 1.5}, "seed"),
    ({"type": "pattern", "pattern": [[1]]}, "position"),
    ({"type": "pattern", "pattern": [[1]], "position": {"x": 0}}, "position"),
    ({"type": "pattern", "pattern": [[1]], "position": {"x": -1, "y": 0}}, "coordonatele"),
    ({"type": "pattern", "pattern": [[1]], "position": {"x": True, "y": 0}}, "coordonatele"),
    ({"type": "pattern", "pattern": [[1]], "position": {"x": 7, "y": 0}}, "nu incape"),
    ({"type": "pattern", "pattern": [[1], [1]], "position": {"x": 0, "y": 4}}, "nu incape"),
    ({"type": "pattern", "pattern": []}, "pattern"),
    ({"type": "pattern", "pattern": " "}, "pattern nu poate fi gol"),
    ({"type": "pattern", "pattern": [[9]], "position": {"x": 0, "y": 0}}, "Stare nedeclarata"),
])
def test_invalid_specs_fail_in_loader_and_appear_in_validation(spec, message):
    data = description(spec)
    with pytest.raises(ValueError, match=message):
        load_automaton_from_text(json.dumps(data))
    problems = validate(data)
    assert any(p.startswith("Eroare:") for p in problems)
    model = automaton({"type": "empty"})
    with pytest.raises(ValueError, match=message):
        generate_initial_state(model, spec)


@pytest.mark.parametrize("percentage", [float("nan"), float("inf")])
def test_nonfinite_percentages(percentage):
    model = automaton({"type": "empty"})
    with pytest.raises(ValueError, match="intre 0 si 100"):
        generate_initial_state(model, {"type": "random", "percentages": {"1": percentage}})


def test_random_rejects_continuous_domain():
    model = load_automaton(EXAMPLES / "diffusion.json")
    with pytest.raises(ValueError, match="stari discrete"):
        generate_initial_state(model, {"type": "random", "percentages": {}})


def test_states_must_fit_numeric_array():
    model = automaton({"type": "empty"})
    model.states = [0, 10 ** 100]
    with pytest.raises(ValueError, match="nu pot fi reprezentate numeric"):
        generate_initial_state(model, {"type": "center"})


def test_generation_validation_accumulates_with_other_errors():
    data = description({"type": "random", "percentages": {"0": 80, "1": 30}})
    data["neighborhood"]["type"] = "unknown"
    assert len([p for p in validate(data) if p.startswith("Eroare:")]) == 2
