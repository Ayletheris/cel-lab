"""Afiseaza evolutia Rule 30, cate o generatie pe rand."""

from pathlib import Path

from cellab.core.experiment import Experiment
from cellab.core.run import run
from cellab.io import load_automaton, load_initial_state


automaton = load_automaton(Path(__file__).resolve().parents[1] / "automata" / "examples" / "rule30.json")
experiment = Experiment(N=50, checkpoint_interval=1)
result = run(automaton, load_initial_state(automaton), experiment)

for generation in range(experiment.N + 1):
    row = result.generations.get(generation).grid[0]
    print("".join("#" if cell else " " for cell in row))
