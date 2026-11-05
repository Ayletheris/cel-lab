"""Rularea unui experiment pentru un numar fix de generatii."""

from dataclasses import dataclass
from time import perf_counter

import numpy as np

from cellab.core.experiment import Experiment
from cellab.core.model import Automaton, State
from cellab.core.step import step
from cellab.io.store import GenerationStore


@dataclass
class RunResult:
    final_state: State
    generations: GenerationStore
    steps: int
    duration: float


def run(automaton: Automaton, state: State, experiment: Experiment,
        rng: np.random.Generator | None = None) -> RunResult:
    """Ruleaza N pasi, pornind de la generatia din state."""
    if rng is None:
        rng = np.random.default_rng(experiment.seed)
    generations = GenerationStore(experiment)
    generations.add(state)

    start = perf_counter()
    for _ in range(experiment.N):
        state = step(automaton, state, rng)
        generations.add(state)

    return RunResult(state, generations, experiment.N, perf_counter() - start)
