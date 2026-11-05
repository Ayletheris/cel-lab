import json
import subprocess
import sys

import pytest

from cellab.cli import add_experiment_arguments, load_run_configuration, parse_experiment_args
from cellab.core.experiment import Experiment
from tests.io.test_load import EXAMPLES


def test_cli_defaults():
    assert parse_experiment_args([]) == Experiment()


def test_all_cli_parameters():
    experiment = parse_experiment_args([
        "--generations", "20", "--seed", "7", "--no-save-intermediate",
        "--checkpoint-interval", "3", "--output-dir", "results",
    ])
    assert experiment == Experiment(N=20, seed=7, save_intermediate=False,
                                    checkpoint_interval=3, output_dir="results")


def test_omitted_cli_flags_preserve_file_values():
    config = {"N": 250, "seed": 8, "save_intermediate": False, "checkpoint_interval": 2}
    assert parse_experiment_args(["--generations", "5"], config) == Experiment(**{**config, "N": 5})
    assert parse_experiment_args(["--save-intermediate"], config).save_intermediate is True
    assert config["N"] == 250 and config["save_intermediate"] is False


def test_cli_combines_file_and_explicit_flags(tmp_path):
    path = tmp_path / "life.json"
    data = json.loads((EXAMPLES / "life.json").read_text(encoding="utf-8"))
    data["experiment"] = {"N": 250, "seed": 8, "save_intermediate": False}
    path.write_text(json.dumps(data), encoding="utf-8")
    model = load_run_configuration([str(path), "--generations", "20", "--seed", "0"])
    assert model.experiment == Experiment(N=20, seed=0, save_intermediate=False)


@pytest.mark.parametrize("argv, message", [
    (["--generations", "0"], "experiment.N"),
    (["--generations", "-1"], "experiment.N"),
    (["--generations", "bad"], "--generations"),
    (["--checkpoint-interval", "0"], "checkpoint_interval"),
    (["--seed", "-1"], "experiment.seed"),
])
def test_invalid_cli_has_short_errors(argv, message, capsys):
    with pytest.raises(SystemExit) as error:
        parse_experiment_args(argv)
    assert error.value.code == 2
    stderr = capsys.readouterr().err
    assert message in stderr and "Traceback" not in stderr


def test_cli_file_error_is_short(tmp_path, capsys):
    with pytest.raises(SystemExit) as error:
        load_run_configuration([str(tmp_path / "missing.json")])
    assert error.value.code == 2
    assert "Fisierul nu exista" in capsys.readouterr().err


def test_arguments_can_be_added_to_the_runner_parser():
    import argparse

    parser = add_experiment_arguments(argparse.ArgumentParser())
    parser.add_argument("--runner-option")
    values = vars(parser.parse_args(["--generations", "2", "--runner-option", "test"]))
    assert values.pop("runner_option") == "test"
    assert Experiment.from_sources({}, **values).N == 2


def test_cli_module_entrypoint():
    result = subprocess.run(
        [sys.executable, "-m", "cellab.cli", str(EXAMPLES / "life.json"),
         "--generations", "2", "--no-save-intermediate"],
        capture_output=True, text=True, timeout=20,
    )
    assert result.returncode == 0, result.stderr
    config = json.loads(result.stdout)
    assert config["N"] == 2 and config["save_intermediate"] is False
    assert config["seed"] == 0 and config["checkpoint_interval"] == 10
