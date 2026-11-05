"""demo pt laboratorul 6 (livrabil 2).

arata, pt 3 automate simple, exact ce cere livrabilul:
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

from cellab.cli.render import render_text
from cellab.core.experiment import Experiment
from cellab.core.run import run
from cellab.core.step import step
from cellab.io import load_automaton, load_initial_state, load_state, save_state

EXAMPLES = Path(__file__).resolve().parents[1] / "automata" / "examples"
AUTOMATA = ["life.json", "brians_brain.json", "forest_fire.json"]


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
    print(f"nr. reguli: {len(automaton.rules)}")


def demo(automaton, folder):
    # 2 + 3. generatia curenta si generatia noua dupa reguli
    current = load_initial_state(automaton)
    print()
    print(render_text(current, automaton))
    new = step(automaton, current)
    print()
    print("dupa aplicarea regulilor:")
    print(render_text(new, automaton))

    # 4. mai rulam 4 pasi, salvam, restauram, continuam
    result = run(automaton, new, Experiment(N=4))
    path = save_state(result.final_state, automaton, folder / "stare.npz", overwrite=True)
    print()
    print(f"salvat generatia {result.final_state.generation} in {path.name}")

    restored = load_state(path, automaton)
    same = np.array_equal(restored.grid, result.final_state.grid)
    print(f"restaurat generatia {restored.generation}, grila identica: {'da' if same else 'NU'}")
    after = step(automaton, restored)
    print(f"continuam de la restaurare -> generatia {after.generation}")


def main():
    with tempfile.TemporaryDirectory() as temp:
        folder = Path(temp)
        for name in AUTOMATA:
            line(name)
            # 1. citim descrierea
            automaton = load_automaton(EXAMPLES / name)
            show_description(automaton)
            demo(automaton, folder)


main()
