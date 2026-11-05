import json
import zipfile
from datetime import datetime, timezone

import numpy as np
import pytest

from cellab.core.experiment import Experiment
from cellab.core.model import State
from cellab.io import load_automaton, load_automaton_from_text, load_initial_state, save_state, validate
from tests.io.test_load import EXAMPLES


def test_archive_contains_compressed_grid_and_json_metadata(tmp_path):
    automaton = load_automaton(EXAMPLES / "life.json", experiment_overrides={"seed": 17})
    state = State(load_initial_state(automaton).grid, generation=12)
    path = tmp_path / "nested" / "results" / "state.npz"
    before = datetime.now(timezone.utc)
    assert save_state(state, automaton, path) == path
    after = datetime.now(timezone.utc)
    assert path.is_file()
    with np.load(path, allow_pickle=False) as archive:
        assert set(archive.files) == {"grid", "metadata"}
        np.testing.assert_array_equal(archive["grid"], state.grid)
        assert archive["grid"].dtype == state.grid.dtype
        metadata = json.loads(archive["metadata"].item())
    assert metadata["generation"] == 12
    assert metadata["automaton_name"] == "Game of Life"
    assert metadata["seed"] == 17
    assert metadata["format_version"] == 1
    saved_at = datetime.fromisoformat(metadata["saved_at"])
    assert before <= saved_at <= after
    assert saved_at.utcoffset().total_seconds() == 0
    with zipfile.ZipFile(path) as archive:
        assert all(info.compress_type == zipfile.ZIP_DEFLATED for info in archive.infolist())


def test_existing_file_is_not_changed_without_overwrite(tmp_path):
    automaton = load_automaton(EXAMPLES / "life.json")
    state = load_initial_state(automaton)
    path = save_state(state, automaton, tmp_path / "state.npz")
    original = path.read_bytes()
    with pytest.raises(FileExistsError, match="overwrite=True"):
        save_state(State(np.zeros_like(state.grid), 5), automaton, path)
    assert path.read_bytes() == original


def test_explicit_overwrite_replaces_grid_and_metadata(tmp_path):
    automaton = load_automaton(EXAMPLES / "life.json")
    state = load_initial_state(automaton)
    path = save_state(state, automaton, tmp_path / "state.npz")
    updated = State(np.zeros_like(state.grid), generation=5)
    save_state(updated, automaton, path, overwrite=True)
    with np.load(path, allow_pickle=False) as archive:
        np.testing.assert_array_equal(archive["grid"], updated.grid)
        assert json.loads(archive["metadata"].item())["generation"] == 5


def test_numeric_grid_keeps_dtype_and_values(tmp_path):
    automaton = load_automaton(EXAMPLES / "diffusion.json")
    grid = np.arange(9, dtype=np.float32).reshape(3, 3) / 10
    path = save_state(State(grid), automaton, tmp_path / "numeric.npz")
    with np.load(path, allow_pickle=False) as archive:
        assert archive["grid"].dtype == np.float32
        np.testing.assert_array_equal(archive["grid"], grid)


def test_name_from_json_and_unicode_metadata(tmp_path):
    data = json.loads((EXAMPLES / "life.json").read_text(encoding="utf-8"))
    data["name"] = "Viață — automat celular"
    automaton = load_automaton_from_text(json.dumps(data))
    assert validate(automaton) == []
    path = save_state(load_initial_state(automaton), automaton, tmp_path / "state.npz")
    with np.load(path, allow_pickle=False) as archive:
        assert json.loads(archive["metadata"].item())["automaton_name"] == data["name"]


def test_unnamed_automaton_uses_default_name(tmp_path):
    automaton = load_automaton(EXAMPLES / "rule30.json")
    path = save_state(load_initial_state(automaton), automaton, tmp_path / "state.npz")
    with np.load(path, allow_pickle=False) as archive:
        assert json.loads(archive["metadata"].item())["automaton_name"] == "automaton"


def test_one_dimensional_rule30_grid_keeps_its_shape(tmp_path):
    automaton = load_automaton(EXAMPLES / "rule30.json")
    grid = load_initial_state(automaton).grid[0]
    path = save_state(State(grid), automaton, tmp_path / "rule30.npz")
    with np.load(path, allow_pickle=False) as archive:
        np.testing.assert_array_equal(archive["grid"], grid)
        assert archive["grid"].ndim == 1


def test_exact_path_is_used_without_adding_an_extension(tmp_path):
    automaton = load_automaton(EXAMPLES / "life.json")
    path = tmp_path / "checkpoint"
    save_state(load_initial_state(automaton), automaton, str(path))
    assert path.is_file() and not path.with_suffix(".npz").exists()


def test_save_does_not_change_the_state_or_automaton(tmp_path):
    automaton = load_automaton(EXAMPLES / "life.json")
    state = load_initial_state(automaton)
    original = state.grid.copy()
    save_state(state, automaton, tmp_path / "state.npz")
    np.testing.assert_array_equal(state.grid, original)
    assert state.generation == 0 and automaton.experiment == Experiment()


@pytest.mark.parametrize("generation", [-1, 1.5, True])
def test_invalid_generation(tmp_path, generation):
    automaton = load_automaton(EXAMPLES / "life.json")
    state = load_initial_state(automaton)
    state.generation = generation
    with pytest.raises(ValueError, match="Generatia"):
        save_state(state, automaton, tmp_path / "state.npz")


@pytest.mark.parametrize("grid, message", [
    (np.zeros((2, 2)), "Dimensiunile"),
    (np.full((5, 5), 9), "stari nedeclarate"),
    (np.full((5, 5), np.nan), "finite"),
    (np.full((5, 5), np.inf), "finite"),
    (np.full((5, 5), "0", dtype=object), "NumPy numerica"),
])
def test_invalid_grid_is_rejected_before_writing(tmp_path, grid, message):
    automaton = load_automaton(EXAMPLES / "life.json")
    path = tmp_path / "new" / "state.npz"
    with pytest.raises(ValueError, match=message):
        save_state(State(grid), automaton, path)
    assert not path.parent.exists()


@pytest.mark.parametrize("name", [None, "", "  ", 42])
def test_invalid_name_from_json(name):
    data = json.loads((EXAMPLES / "life.json").read_text(encoding="utf-8"))
    data["name"] = name
    with pytest.raises(ValueError, match="name"):
        load_automaton_from_text(json.dumps(data))
    assert any("name" in problem for problem in validate(data))


def test_invalid_overwrite_option(tmp_path):
    automaton = load_automaton(EXAMPLES / "life.json")
    with pytest.raises(ValueError, match="overwrite"):
        save_state(load_initial_state(automaton), automaton, tmp_path / "state.npz", overwrite="yes")
