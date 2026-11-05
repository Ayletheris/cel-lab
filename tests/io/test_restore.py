import json

import numpy as np
import pytest

from cellab.core.model import State
from cellab.core.step import step
from cellab.io import load_automaton, load_initial_state, load_state, save_state
from tests.io.test_load import EXAMPLES


def saved(tmp_path, name="life", generation=7):
    automaton = load_automaton(EXAMPLES / f"{name}.json")
    state = State(load_initial_state(automaton).grid, generation)
    path = save_state(state, automaton, tmp_path / "state.npz")
    return automaton, state, path


def rewrite(path, changes=None, grid=None, remove=None):
    with np.load(path, allow_pickle=False) as archive:
        metadata = json.loads(archive["metadata"].item())
        original = archive["grid"]
    metadata.update(changes or {})
    if remove:
        del metadata[remove]
    with path.open("wb") as file:
        np.savez_compressed(file, grid=original if grid is None else grid, metadata=json.dumps(metadata))


@pytest.mark.parametrize("name", ["life", "brians_brain", "rule30", "diffusion", "life_random"])
def test_round_trip_keeps_grid_dtype_and_generation(tmp_path, name):
    automaton, original, path = saved(tmp_path, name)
    restored = load_state(path, automaton)
    assert isinstance(restored, State)
    assert np.array_equal(restored.grid, original.grid)
    assert restored.grid.dtype == original.grid.dtype
    assert restored.generation == original.generation == 7


def test_simulation_continues_from_restored_generation(tmp_path):
    automaton = load_automaton(EXAMPLES / "life_glider.json")
    state = load_initial_state(automaton)
    for _ in range(3):
        state = step(automaton, state)
    path = save_state(state, automaton, tmp_path / "glider.npz")
    uninterrupted = state
    restored = load_state(path, automaton)
    for _ in range(5):
        uninterrupted = step(automaton, uninterrupted)
        restored = step(automaton, restored)
    assert restored.generation == uninterrupted.generation == 8
    assert np.array_equal(restored.grid, uninterrupted.grid)


def test_wrong_grid_size_has_explicit_dimensions(tmp_path):
    automaton = load_automaton(EXAMPLES / "life_empty.json")
    automaton.grid_size = [30, 30]
    state = load_initial_state(automaton)
    path = save_state(state, automaton, tmp_path / "30.npz")
    automaton.grid_size = [50, 50]
    with pytest.raises(ValueError, match="30x30.*50x50"):
        load_state(path, automaton)


def test_rectangular_size_message_uses_width_then_height(tmp_path):
    automaton = load_automaton(EXAMPLES / "life_empty.json")
    automaton.grid_size = [3, 7]
    path = save_state(load_initial_state(automaton), automaton, tmp_path / "rectangle.npz")
    automaton.grid_size = [4, 9]
    with pytest.raises(ValueError, match="7x3.*9x4"):
        load_state(path, automaton)


def test_full_declared_state_set_is_checked_even_when_unused(tmp_path):
    automaton, state, path = saved(tmp_path, "life_empty")
    assert not state.grid.any()
    automaton.states = [0, 1, 2]
    with pytest.raises(ValueError, match="Starile declarate.*nu coincid"):
        load_state(path, automaton)


def test_same_declared_states_in_different_order_are_accepted(tmp_path):
    automaton, original, path = saved(tmp_path)
    automaton.states = [1, 0]
    assert np.array_equal(load_state(path, automaton).grid, original.grid)


def test_numeric_and_discrete_domains_are_incompatible(tmp_path):
    automaton, _, path = saved(tmp_path)
    automaton.states = ["number"]
    with pytest.raises(ValueError, match="Starile declarate.*nu coincid"):
        load_state(path, automaton)


def test_one_dimensional_rule30_can_continue(tmp_path):
    automaton = load_automaton(EXAMPLES / "rule30.json")
    state = State(load_initial_state(automaton).grid[0], 3)
    path = save_state(state, automaton, tmp_path / "rule30.npz")
    restored = load_state(path, automaton)
    assert restored.grid.ndim == 1
    assert restored.generation == 3
    assert np.array_equal(step(automaton, restored).grid, step(automaton, state).grid)


@pytest.mark.parametrize("version", [1, 3, 999, True, "2", None])
def test_unsupported_or_invalid_version(tmp_path, version):
    automaton, _, path = saved(tmp_path)
    rewrite(path, {"format_version": version})
    with pytest.raises(ValueError, match="Versiunea.*versiunea 2"):
        load_state(path, automaton)


@pytest.mark.parametrize("changes, message", [
    ({"generation": -1}, "Generatia"),
    ({"generation": True}, "Generatia"),
    ({"generation": 1.5}, "Generatia"),
    ({"seed": -1}, "Seedul"),
    ({"automaton_name": ""}, "Numele"),
    ({"saved_at": "invalid"}, "Data salvarii"),
    ({"saved_at": "2026-11-05T12:00:00"}, "Data salvarii"),
    ({"grid_size": [0, 5]}, "Dimensiunile din metadate"),
    ({"grid_size": [3, 3]}, "nu corespund metadatelor"),
    ({"states": [0, 0]}, "Starile declarate in metadate"),
    ({"states": [[0]]}, "Starile declarate in metadate"),
])
def test_bad_metadata_has_clear_errors(tmp_path, changes, message):
    automaton, _, path = saved(tmp_path)
    rewrite(path, changes)
    with pytest.raises(ValueError, match=message):
        load_state(path, automaton)


def test_missing_metadata_field(tmp_path):
    automaton, _, path = saved(tmp_path)
    rewrite(path, remove="states")
    with pytest.raises(ValueError, match="incomplete"):
        load_state(path, automaton)


@pytest.mark.parametrize("grid", [np.full((5, 5), 9), np.full((5, 5), np.inf), np.full((5, 5), np.nan)])
def test_corrupted_grid_is_rejected(tmp_path, grid):
    automaton, _, path = saved(tmp_path)
    rewrite(path, grid=grid)
    with pytest.raises(ValueError, match="finite|nedeclarate"):
        load_state(path, automaton)


def test_missing_file(tmp_path):
    automaton = load_automaton(EXAMPLES / "life.json")
    with pytest.raises(ValueError, match="Fisierul nu exista"):
        load_state(tmp_path / "missing.npz", automaton)


@pytest.mark.parametrize("content", [b"", b"not an archive", b"PK\x03\x04truncated"])
def test_broken_archive(tmp_path, content):
    automaton = load_automaton(EXAMPLES / "life.json")
    path = tmp_path / "broken.npz"
    path.write_bytes(content)
    with pytest.raises(ValueError, match="stricat|NPZ"):
        load_state(path, automaton)


@pytest.mark.parametrize("metadata", ["{", "[]", '{"format_version":2,"format_version":3}'])
def test_invalid_json_metadata(tmp_path, metadata):
    automaton = load_automaton(EXAMPLES / "life.json")
    path = tmp_path / "bad.npz"
    np.savez_compressed(path, grid=np.zeros((5, 5)), metadata=metadata)
    with pytest.raises(ValueError, match="JSON"):
        load_state(path, automaton)


def test_object_arrays_are_never_unpickled(tmp_path):
    automaton = load_automaton(EXAMPLES / "life.json")
    path = tmp_path / "objects.npz"
    np.savez_compressed(path, grid=np.array([{"not": "numeric"}], dtype=object), metadata="{}")
    with pytest.raises(ValueError, match="stricat"):
        load_state(path, automaton)


def test_archive_file_is_closed_after_loading(tmp_path):
    automaton, _, path = saved(tmp_path)
    restored = load_state(path, automaton)
    path.rename(tmp_path / "moved.npz")
    assert restored.grid.shape == (5, 5)
