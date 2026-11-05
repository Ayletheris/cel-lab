import argparse
import json
from dataclasses import asdict

from cellab.core.experiment import Experiment
from cellab.io import load_automaton


def add_experiment_arguments(parser):
    parser.add_argument("--generations", dest="N", type=int, default=argparse.SUPPRESS)
    parser.add_argument("--seed", type=int, default=argparse.SUPPRESS)
    parser.add_argument("--save-intermediate", action=argparse.BooleanOptionalAction, default=argparse.SUPPRESS)
    parser.add_argument("--checkpoint-interval", dest="checkpoint_interval", type=int, default=argparse.SUPPRESS)
    parser.add_argument("--output-dir", dest="output_dir", default=argparse.SUPPRESS)
    return parser


def parse_experiment_args(argv=None, config=None) -> Experiment:
    parser = add_experiment_arguments(argparse.ArgumentParser(description="Parametrii experimentului CelLab"))
    values = vars(parser.parse_args(argv))
    try:
        return Experiment.from_sources(config, **values)
    except ValueError as issue:
        parser.error(str(issue))


def load_run_configuration(argv=None):
    parser = add_experiment_arguments(argparse.ArgumentParser(description="Configuratia experimentului CelLab"))
    parser.add_argument("automaton", help="Calea fisierului JSON al automatului")
    values = vars(parser.parse_args(argv))
    path = values.pop("automaton")
    try:
        return load_automaton(path, experiment_overrides=values)
    except ValueError as issue:
        parser.error(str(issue))


def main(argv=None):
    automaton = load_run_configuration(argv)
    print(json.dumps(asdict(automaton.experiment), default=str, indent=2))
