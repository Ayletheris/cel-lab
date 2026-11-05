import json
from pathlib import Path

import numpy as np
import pytest

from cellab.core.experiment import Experiment
from cellab.core.model import State
from cellab.core.step import step
from cellab.io import GenerationStore, load_automaton, load_initial_state, load_state
from tests.io.test_load import EXAMPLES


def simulate(store, automaton, count=20):
    state = load_initial_state(automaton)
    snapshots = {0: state.grid.copy()}
    store.add(state)
    for _ in range(count):
        state = step(automaton, state)
        snapshots[state.generation] = state.grid.copy()
        store.add(state)
    return snapshots


@pytest.mark.parametrize("mode", ["checkpoint", "disk"])
def test_twenty_generations_keep_every_fifth(tmp_path, mode):
    automaton = load_automaton(EXAMPLES / "life_glider.json")
    experiment = Experiment(N=20, checkpoint_interval=5, output_dir=tmp_path / "generations")
    store = GenerationStore(experiment, automaton, mode=mode)
    snapshots = simulate(store, automaton)
    assert store.count() == 5
    for t in (0, 5, 10, 15, 20):
        state = store.get(t)
        assert state.generation == t
        assert np.array_equal(state.grid, snapshots[t])
    for t in set(range(21)) - {0, 5, 10, 15, 20}:
        with pytest.raises(KeyError, match=f"Generatia {t} nu este pastrata"):
            store.get(t)
    assert store.last().generation == 20
    if mode == "disk":
        assert len(list(experiment.output_dir.glob("*.npz"))) == 5


@pytest.mark.parametrize("mode", ["memory", "checkpoint", "disk"])
def test_no_intermediates_keeps_only_first_and_last(tmp_path, mode):
    automaton = load_automaton(EXAMPLES / "life.json")
    experiment = Experiment(N=20, save_intermediate=False, checkpoint_interval=5, output_dir=tmp_path)
    store = GenerationStore(experiment, automaton, mode)
    snapshots = simulate(store, automaton)
    assert store.count() == 2
    assert np.array_equal(store.get(0).grid, snapshots[0])
    assert np.array_equal(store.get(20).grid, snapshots[20])
    assert store.last().generation == 20
    for t in range(1, 20):
        with pytest.raises(KeyError, match=f"Generatia {t} nu este pastrata"):
            store.get(t)
    if mode == "disk":
        assert len(list(tmp_path.glob("*.npz"))) == 2


def test_memory_mode_keeps_all_generations():
    automaton = load_automaton(EXAMPLES / "life.json")
    store = GenerationStore(Experiment(checkpoint_interval=5), mode="memory")
    snapshots = simulate(store, automaton)
    assert store.count() == 21
    for t, grid in snapshots.items():
        assert np.array_equal(store.get(t).grid, grid)


def test_default_mode_uses_experiment_interval():
    store = GenerationStore(Experiment(checkpoint_interval=5))
    for t in range(21):
        store.add(State(np.full((2, 2), t), t))
    assert store.count() == 5
    assert [store.get(t).generation for t in (0, 5, 10, 15, 20)] == [0, 5, 10, 15, 20]


@pytest.mark.parametrize("mode", ["checkpoint", "disk"])
def test_last_is_kept_between_checkpoints(tmp_path, mode):
    automaton = load_automaton(EXAMPLES / "life.json")
    store = GenerationStore(Experiment(checkpoint_interval=5, output_dir=tmp_path), automaton, mode)
    simulate(store, automaton, count=7)
    assert store.count() == 3
    assert [store.get(t).generation for t in (0, 5, 7)] == [0, 5, 7]
    assert store.last().generation == 7
    with pytest.raises(KeyError):
        store.get(6)


def test_empty_store_and_one_state():
    store = GenerationStore(Experiment())
    assert store.count() == 0 and store.last() is None
    with pytest.raises(KeyError):
        store.get(0)
    store.add(State(np.zeros((2, 2)), 0))
    assert store.count() == 1 and store.last().generation == 0


def test_input_and_returned_grids_do_not_change_history():
    store = GenerationStore(Experiment(), mode="memory")
    state = State(np.ones((2, 2), dtype=int), 0)
    store.add(state)
    state.grid[:] = 0
    assert store.get(0).grid.all()
    returned = store.get(0)
    returned.grid[:] = 0
    returned.generation = 99
    assert store.get(0).grid.all() and store.get(0).generation == 0


def test_resumed_simulation_keeps_first_received_generation():
    store = GenerationStore(Experiment(checkpoint_interval=5))
    for t in range(7, 13):
        store.add(State(np.zeros((2, 2)), t))
    assert store.count() == 3
    assert [store.get(t).generation for t in (7, 10, 12)] == [7, 10, 12]


def test_disk_refuses_overwrite_and_preserves_other_files(tmp_path):
    automaton = load_automaton(EXAMPLES / "life.json")
    experiment = Experiment(output_dir=tmp_path)
    unrelated = tmp_path / "notes.txt"
    unrelated.write_text("keep", encoding="utf-8")
    first = GenerationStore(experiment, automaton, "disk")
    first.add(load_initial_state(automaton))
    second = GenerationStore(experiment, automaton, "disk")
    with pytest.raises(FileExistsError):
        second.add(load_initial_state(automaton))
    assert second.count() == 0 and second.last() is None
    assert unrelated.read_text(encoding="utf-8") == "keep"


def test_disk_snapshots_include_rng_but_get_does_not_rewind_it(tmp_path):
    automaton = load_automaton(EXAMPLES / "life.json")
    rng = np.random.default_rng(42)
    store = GenerationStore(Experiment(output_dir=tmp_path), automaton, "disk", rng)
    store.add(load_initial_state(automaton))
    expected = rng.random(10)
    before = rng.bit_generator.state
    assert store.get(0).generation == 0
    assert rng.bit_generator.state == before
    restored_rng = np.random.default_rng(0)
    load_state(tmp_path / "generation-0000000000.npz", automaton, restored_rng)
    assert np.array_equal(restored_rng.random(10), expected)


def test_disk_uses_store_experiment_without_changing_automaton(tmp_path):
    automaton = load_automaton(EXAMPLES / "life.json")
    store = GenerationStore(Experiment(seed=7, output_dir=tmp_path), automaton, "disk")
    store.add(load_initial_state(automaton))
    with np.load(tmp_path / "generation-0000000000.npz", allow_pickle=False) as archive:
        assert json.loads(archive["metadata"].item())["seed"] == 7
    assert automaton.experiment.seed == 0


def test_failed_pruning_preserves_existing_history(tmp_path, monkeypatch):
    automaton = load_automaton(EXAMPLES / "life.json")
    store = GenerationStore(Experiment(output_dir=tmp_path), automaton, "disk")
    initial = load_initial_state(automaton)
    store.add(initial)
    store.add(State(initial.grid, 1))
    unlink = Path.unlink

    def refuse_previous(path, *args, **kwargs):
        if path.name == "generation-0000000001.npz":
            raise PermissionError("locked")
        return unlink(path, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", refuse_previous)
    with pytest.raises(ValueError, match="nu poate fi eliminata"):
        store.add(State(initial.grid, 2))
    assert store.count() == 2 and store.last().generation == 1
    assert not (tmp_path / "generation-0000000002.npz").exists()


@pytest.mark.parametrize("t", [-1, True, 1.5])
def test_invalid_generation_query(t):
    with pytest.raises(ValueError, match="Generatia ceruta"):
        GenerationStore(Experiment()).get(t)


@pytest.mark.parametrize("t", [0, -1])
def test_duplicate_or_out_of_order_add_is_refused(t):
    store = GenerationStore(Experiment())
    store.add(State(np.zeros((2, 2)), 0))
    with pytest.raises(ValueError):
        store.add(State(np.zeros((2, 2)), t))
    assert store.count() == 1


@pytest.mark.parametrize("kwargs", [
    {"experiment": None}, {"mode": "unknown"}, {"mode": "disk"}, {"rng": 42},
])
def test_invalid_configuration(kwargs):
    with pytest.raises(ValueError):
        GenerationStore(**{"experiment": Experiment(), **kwargs})
