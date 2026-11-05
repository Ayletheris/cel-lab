"""demo pt laboratorul 6 (livrabil 2).

arata, pt 4 automate, exact ce cere livrabilul:
  1. citim descrierea (json)
  2. citim generatia curenta
  3. aplicam regulile -> generatia noua
  4. salvam starea si o restauram, apoi continuam

rulare (din folderul cel-lab):
    .venv\\Scripts\\python scripts/demo_l6.py
"""

import tempfile
from pathlib import Path

import numpy as np

from cellab.cli.render import render_rows, render_text
from cellab.core.experiment import Experiment
from cellab.core.run import run
from cellab.core.step import rule_kind, step
from cellab.io import load_automaton, load_initial_state, load_state, save_state
from cellab.questions.stability import find_cycle, has_probability

EXAMPLES = Path(__file__).resolve().parents[1] / "automata" / "examples"
AUTOMATA = ["life.json", "brians_brain.json", "rule30.json", "forest_fire_random.json"]

KIND_NAMES = {
    "counts": "reguli pe numarul de vecini",
    "table": "tabel cu 8 cazuri (automat 1D)",
    "numeric": "expresie numerica",
}


def line(title):
    print()
    print("=" * 60)
    print(title)
    print("=" * 60)


def show_description(automaton):
    height, width = automaton.grid_size
    print(f"nume: {automaton.name}")
    print(f"grila: {height} x {width}, margine: {automaton.boundary}")
    print(f"stari: {automaton.states}")
    print(f"tip reguli: {KIND_NAMES[rule_kind(automaton.rules)]}")
    if has_probability(automaton):
        print("are reguli cu probabilitate (seed fix -> rezultat reproductibil)")


def demo_2d(automaton, folder):
    rng = np.random.default_rng(automaton.experiment.seed)

    # 2 + 3. generatia curenta si generatia noua dupa reguli
    current = load_initial_state(automaton)
    print()
    print(render_text(current, automaton, max_width=40, max_height=12))
    new = step(automaton, current, rng)
    print()
    print("dupa aplicarea regulilor:")
    print(render_text(new, automaton, max_width=40, max_height=12))

    # 4. mai rulam 4 pasi, salvam, restauram, continuam
    result = run(automaton, new, Experiment(N=4, seed=automaton.experiment.seed), rng)
    path = save_state(result.final_state, automaton, folder / "stare.npz", overwrite=True, rng=rng)
    print()
    print(f"salvat generatia {result.final_state.generation} in {path.name}")

    # load_state pune in restored_rng starea generatorului salvat, ca sa continuam identic
    restored_rng = np.random.default_rng(0)
    restored = load_state(path, automaton, rng=restored_rng)
    same = np.array_equal(restored.grid, result.final_state.grid)
    print(f"restaurat generatia {restored.generation}, grila identica: {'da' if same else 'NU'}")
    after = step(automaton, restored, restored_rng)
    print(f"continuam de la restaurare -> generatia {after.generation}")


def demo_rule30(automaton, folder):
    # la 1D fiecare generatie e un rand nou, ca sa se vada triunghiul
    start = load_initial_state(automaton)
    result = run(automaton, start, Experiment(N=20, checkpoint_interval=1))
    states = [result.generations.get(t) for t in range(21)]
    print()
    print("generatiile 0..20, una sub alta:")
    print(render_rows(states, automaton, max_width=101))

    path = save_state(result.final_state, automaton, folder / "rule30.npz", overwrite=True)
    restored = load_state(path, automaton)
    same = np.array_equal(restored.grid, result.final_state.grid)
    print()
    print(f"salvat + restaurat generatia {restored.generation}, grila identica: {'da' if same else 'NU'}")


def main():
    with tempfile.TemporaryDirectory() as temp:
        folder = Path(temp)
        for name in AUTOMATA:
            line(name)
            # 1. citim descrierea
            automaton = load_automaton(EXAMPLES / name)
            show_description(automaton)
            if rule_kind(automaton.rules) == "table":
                demo_rule30(automaton, folder)
            else:
                demo_2d(automaton, folder)

    line("bonus: intrebarea Q5 pe life.json (blinker)")
    life = load_automaton(EXAMPLES / "life.json")
    mu, lam = find_cycle(life, load_initial_state(life))
    print(f"intra in ciclu de la generatia {mu}, lungime {lam}")


main()
