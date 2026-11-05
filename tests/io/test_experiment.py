import json
from pathlib import Path

import pytest

from cellab.core.experiment import Experiment
from cellab.core.model import Automaton
from cellab.io import load_automaton, load_automaton_from_text, validate
from tests.io.test_load import EXAMPLES


def description(config):
    data = json.loads((EXAMPLES / "life.json").read_text(encoding="utf-8"))
    data["experiment"] = config
    return data


def test_defaults_from_code_json_and_model():
    default = Experiment()
    assert default.N == 100 and default.seed == 0
    assert default.save_intermediate is True
    assert default.checkpoint_interval == 10
    assert default.output_dir == Path("saves")
    assert load_automaton(EXAMPLES / "life.json").experiment == default
    assert load_automaton_from_text(json.dumps(description({}))).experiment == default
    assert Automaton([3, 3], "fixed", [0, 1], "moore", []).experiment == default


def test_all_parameters_from_code():
    experiment = Experiment(N=20, seed=7, save_intermediate=False, checkpoint_interval=3, output_dir="results")
    assert experiment.N == 20 and experiment.seed == 7
    assert experiment.save_intermediate is False
    assert experiment.checkpoint_interval == 3
    assert experiment.output_dir == Path("results")


def test_all_parameters_from_json():
    config = {"N": 20, "seed": 7, "save_intermediate": False, "checkpoint_interval": 3, "output_dir": "results"}
    model = load_automaton_from_text(json.dumps(description(config)))
    assert model.experiment == Experiment(**config)
    assert validate(model) == []
    assert validate(description(config)) == []


def test_user_overrides_file_and_file_overrides_defaults(tmp_path):
    path = tmp_path / "life.json"
    config = {"N": 250, "seed": 8, "save_intermediate": True, "output_dir": "file-results"}
    path.write_text(json.dumps(description(config)), encoding="utf-8")
    overrides = {"N": 5, "seed": 0, "save_intermediate": False}
    model = load_automaton(path, experiment_overrides=overrides)
    assert model.experiment == Experiment(N=5, seed=0, save_intermediate=False, output_dir="file-results")
    assert overrides == {"N": 5, "seed": 0, "save_intermediate": False}
    assert config["N"] == 250


def test_sources_can_start_from_an_existing_experiment():
    base = Experiment(N=250, seed=8, save_intermediate=False)
    result = Experiment.from_sources(base, N=5)
    assert result == Experiment(N=5, seed=8, save_intermediate=False)
    assert base.N == 250


def test_overrides_are_merged_before_validating():
    config = {"N": 0, "checkpoint_interval": -1}
    model = load_automaton_from_text(json.dumps(description(config)),
                                     experiment_overrides={"N": 5, "checkpoint_interval": 2})
    assert model.experiment == Experiment(N=5, checkpoint_interval=2)


@pytest.mark.parametrize("config, message", [
    ({"N": 0}, "experiment.N"),
    ({"N": -1}, "experiment.N"),
    ({"N": 1.5}, "experiment.N"),
    ({"N": True}, "experiment.N"),
    ({"N": "100"}, "experiment.N"),
    ({"N": None}, "experiment.N"),
    ({"checkpoint_interval": 0}, "checkpoint_interval"),
    ({"checkpoint_interval": -1}, "checkpoint_interval"),
    ({"checkpoint_interval": 1.5}, "checkpoint_interval"),
    ({"checkpoint_interval": True}, "checkpoint_interval"),
    ({"seed": -1}, "experiment.seed"),
    ({"seed": .5}, "experiment.seed"),
    ({"seed": True}, "experiment.seed"),
    ({"save_intermediate": "yes"}, "save_intermediate"),
    ({"save_intermediate": 1}, "save_intermediate"),
    ({"output_dir": ""}, "output_dir"),
    ({"output_dir": "  "}, "output_dir"),
    ({"output_dir": None}, "output_dir"),
    ({"output_dir": "bad\u0000path"}, "output_dir"),
])
def test_invalid_values_in_code_and_json(config, message):
    with pytest.raises(ValueError, match=message):
        Experiment(**config)
    with pytest.raises(ValueError, match=message):
        load_automaton_from_text(json.dumps(description(config)))
    assert any(message in problem for problem in validate(description(config)))


@pytest.mark.parametrize("config", [None, [], "invalid", {"generations": 5}])
def test_invalid_json_experiment(config):
    with pytest.raises(ValueError, match="experiment"):
        load_automaton_from_text(json.dumps(description(config)))
    assert any("experiment" in problem for problem in validate(description(config)))


def test_validator_reports_multiple_experiment_errors():
    problems = validate(description({"N": 0, "checkpoint_interval": 0, "seed": -1}))
    assert len(problems) == 3
    assert all(problem.startswith("Eroare: experiment.") for problem in problems)


def test_invalid_override_is_not_replaced_by_a_default():
    with pytest.raises(ValueError, match="experiment.N"):
        load_automaton(EXAMPLES / "life.json", experiment_overrides={"N": None})


def test_configuration_does_not_create_output_directories(tmp_path):
    directory = tmp_path / "results"
    assert Experiment(output_dir=directory).output_dir == directory
    assert not directory.exists()
