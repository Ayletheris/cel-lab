import json

import numpy as np
import pytest

from cellab.core.model import Automaton, Experiment, State
from cellab.core.step import step
from cellab.io import GenerationStore, load_state, save_state
from tests.core.test_probability import FOREST


ENGINES = [np.random.PCG64, np.random.PCG64DXSM, np.random.MT19937, np.random.Philox, np.random.SFC64]


def forest():
    return Automaton([20, 20], "toroidal", [0, 1, 2], "moore", FOREST, name="Forest Fire")


def run(automaton, state, rng, steps):
    for _ in range(steps):
        state = step(automaton, state, rng)
    return state


@pytest.mark.parametrize("engine", ENGINES, ids=lambda cls: cls.__name__)
def test_forest_fire_resume_matches_ten_uninterrupted_steps(tmp_path, engine):
    automaton = forest()
    continuous_rng = np.random.Generator(engine(123))
    continuous = State(continuous_rng.integers(0, 2, size=(20, 20), dtype=np.uint8))
    continuous = run(automaton, continuous, continuous_rng, 10)

    interrupted_rng = np.random.Generator(engine(123))
    interrupted = State(interrupted_rng.integers(0, 2, size=(20, 20), dtype=np.uint8))
    interrupted = run(automaton, interrupted, interrupted_rng, 5)
    path = save_state(interrupted, automaton, tmp_path / "forest.npz", rng=interrupted_rng)

    restored_rng = np.random.Generator(engine(999))
    restored = load_state(path, automaton, rng=restored_rng)
    assert restored.generation == 5
    assert np.array_equal(restored.grid, interrupted.grid)
    restored = run(automaton, restored, restored_rng, 5)
    assert restored.generation == continuous.generation == 10
    assert np.array_equal(restored.grid, continuous.grid)
    assert np.array_equal(restored_rng.random(100), continuous_rng.random(100))


@pytest.mark.parametrize("engine", ENGINES, ids=lambda cls: cls.__name__)
def test_forest_fire_resume_from_generation_store_checkpoint(tmp_path, engine):
    automaton = forest()
    initial = np.random.default_rng(1).integers(0, 2, size=(20, 20), dtype=np.uint8)
    uninterrupted_rng = np.random.Generator(engine(123))
    expected = run(automaton, State(initial.copy()), uninterrupted_rng, 10)

    rng = np.random.Generator(engine(123))
    experiment = Experiment(N=10, seed=123, checkpoint_interval=5, output_dir=tmp_path / "first")
    store = GenerationStore(experiment, automaton, mode="disk", rng=rng)
    state = State(initial.copy())
    store.add(state)
    for _ in range(5):
        state = step(automaton, state, rng)
        store.add(state)
    assert store.count() == 2
    checkpoint = experiment.output_dir / "generation-0000000005.npz"
    restored_rng = np.random.Generator(engine(999))
    restored = load_state(checkpoint, automaton, restored_rng)
    resumed = GenerationStore(
        Experiment(N=10, seed=123, checkpoint_interval=5, output_dir=tmp_path / "resumed"),
        automaton, mode="disk", rng=restored_rng,
    )
    resumed.add(restored)
    for _ in range(5):
        restored = step(automaton, restored, restored_rng)
        resumed.add(restored)
    assert resumed.count() == 2
    assert resumed.get(5).generation == 5 and resumed.last().generation == 10
    assert np.array_equal(resumed.get(10).grid, expected.grid)
    assert np.array_equal(restored_rng.random(100), uninterrupted_rng.random(100))


@pytest.mark.parametrize("engine", ENGINES, ids=lambda cls: cls.__name__)
def test_rng_buffers_and_cached_integer_bits_are_preserved(tmp_path, engine):
    automaton = forest()
    rng = np.random.Generator(engine(42))
    rng.integers(0, 10, size=3, dtype=np.uint32)
    path = save_state(State(np.zeros((20, 20), dtype=np.uint8)), automaton, tmp_path / "rng.npz", rng=rng)
    expected_integers = rng.integers(0, 1000, size=51, dtype=np.uint32)
    expected_normals = rng.normal(size=51)
    restored_rng = np.random.Generator(engine(0))
    load_state(path, automaton, restored_rng)
    assert np.array_equal(restored_rng.integers(0, 1000, size=51, dtype=np.uint32), expected_integers)
    assert np.array_equal(restored_rng.normal(size=51), expected_normals)


def test_rng_snapshot_is_json_in_same_archive_and_save_does_not_advance_rng(tmp_path):
    automaton = forest()
    rng = np.random.default_rng(42)
    before = rng.bit_generator.state
    path = save_state(State(np.zeros((20, 20), dtype=int)), automaton, tmp_path / "rng.npz", rng=rng)
    assert rng.bit_generator.state == before
    with np.load(path, allow_pickle=False) as archive:
        assert set(archive.files) == {"grid", "metadata", "rng_state"}
        assert json.loads(archive["rng_state"].item()) == before


def test_archive_without_rng_stays_compatible_when_rng_is_not_requested(tmp_path):
    automaton = forest()
    state = State(np.zeros((20, 20), dtype=int), 5)
    path = save_state(state, automaton, tmp_path / "plain.npz")
    assert load_state(path, automaton).generation == 5
    rng = np.random.default_rng(42)
    before = rng.bit_generator.state
    with pytest.raises(ValueError, match="nu contine starea RNG"):
        load_state(path, automaton, rng)
    assert rng.bit_generator.state == before


def test_grid_can_be_restored_without_requesting_rng(tmp_path):
    automaton = forest()
    state = State(np.zeros((20, 20), dtype=int), 5)
    path = save_state(state, automaton, tmp_path / "rng.npz", rng=np.random.default_rng(42))
    assert load_state(path, automaton).generation == 5


def test_incompatible_generator_is_refused_without_mutation(tmp_path):
    automaton = forest()
    state = State(np.zeros((20, 20), dtype=int))
    path = save_state(state, automaton, tmp_path / "rng.npz", rng=np.random.Generator(np.random.Philox(42)))
    rng = np.random.default_rng(7)
    before = rng.bit_generator.state
    with pytest.raises(ValueError, match="nu coincide.*Philox"):
        load_state(path, automaton, rng)
    assert rng.bit_generator.state == before


@pytest.mark.parametrize("snapshot", [
    "{", "[]", '{"bit_generator":"Unknown"}', '{"bit_generator":"PCG64"}',
    '{"bit_generator":"PCG64","state":null}',
    '{"bit_generator":"MT19937","state":{"key":[],"pos":0}}',
    '{"bit_generator":"PCG64","bit_generator":"Philox"}',
])
def test_bad_rng_snapshot_is_refused_without_mutation(tmp_path, snapshot):
    automaton = forest()
    path = save_state(State(np.zeros((20, 20), dtype=int)), automaton, tmp_path / "bad.npz")
    with np.load(path, allow_pickle=False) as archive:
        payload = {name: archive[name] for name in archive.files}
    np.savez_compressed(path, **payload, rng_state=snapshot)
    rng = np.random.default_rng(7)
    before = rng.bit_generator.state
    with pytest.raises(ValueError, match="RNG.*invalid"):
        load_state(path, automaton, rng)
    assert rng.bit_generator.state == before


def test_automaton_mismatch_does_not_change_rng(tmp_path):
    automaton = forest()
    path = save_state(State(np.zeros((20, 20), dtype=int)), automaton, tmp_path / "rng.npz", rng=np.random.default_rng(42))
    automaton.grid_size = [30, 30]
    rng = np.random.default_rng(7)
    before = rng.bit_generator.state
    with pytest.raises(ValueError, match="20x20.*30x30"):
        load_state(path, automaton, rng)
    assert rng.bit_generator.state == before


def test_invalid_rng_parameter_is_clear_and_does_not_create_a_file(tmp_path):
    automaton = forest()
    path = tmp_path / "bad.npz"
    with pytest.raises(ValueError, match="generator NumPy"):
        save_state(State(np.zeros((20, 20), dtype=int)), automaton, path, rng=42)
    assert not path.exists()
    with pytest.raises(ValueError, match="generator NumPy"):
        load_state(path, automaton, rng=42)
