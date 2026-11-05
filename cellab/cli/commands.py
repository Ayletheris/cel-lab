"""comenzile din linia de comanda.

exemple (din folderul cel-lab):
    python -m cellab.cli run automata/examples/game_of_life.json --generations 20 --seed 1 --show
    python -m cellab.cli run automata/examples/game_of_life.json --resume saves/game-of-life-gen20.npz
    python -m cellab.cli validate automata/examples/life.json

fara comanda (doar un fisier json) se afiseaza configuratia experimentului, ca inainte.
"""

import argparse
import sys
from pathlib import Path

import numpy as np

from cellab.cli.experiment import add_experiment_arguments
from cellab.cli.experiment import main as show_experiment_config
from cellab.cli.render import render_generations, render_rows
from cellab.core.run import run
from cellab.io import load_automaton, load_initial_state, load_state, save_state, validate

HELP = """folosire: python -m cellab.cli <comanda> fisier.json [optiuni]

comenzi:
  run        ruleaza automatul N generatii si salveaza starea finala
  validate   verifica fisierul json si arata problemele

pt optiunile unei comenzi: python -m cellab.cli <comanda> --help"""


def file_name(text: str) -> str:
    """face din numele automatului un nume bun de fisier. ex. "Brian's Brain" -> "brians-brain" """
    name = ""
    for char in text.lower():
        if char.isalnum():
            name += char
        elif char in " -_" and not name.endswith("-"):
            name += "-"
    name = name.strip("-")
    if name == "":
        name = "automat"
    return name


def has_saved_rng(path) -> bool:
    """true daca fisierul salvat are si generatorul aleator in el"""
    try:
        with np.load(path) as archive:
            return "rng_state" in archive.files
    except (OSError, ValueError):
        # fisier lipsa / stricat: lasam load_state sa dea mesajul de eroare
        return False


def kept_states(result) -> list:
    """generatiile pastrate in store, in ordine"""
    first = result.final_state.generation - result.steps
    states = []
    for generation in range(first, result.final_state.generation + 1):
        try:
            states.append(result.generations.get(generation))
        except KeyError:
            # generatia asta nu a fost pastrata (nu e punct de control)
            continue
    return states


def run_command(argv) -> int:
    parser = argparse.ArgumentParser(prog="python -m cellab.cli run",
                                     description="ruleaza un automat si salveaza starea finala")
    parser.add_argument("automaton", help="fisierul json al automatului")
    add_experiment_arguments(parser)
    parser.add_argument("--resume", help="continua de la o stare salvata (.npz)")
    parser.add_argument("--show", action="store_true", help="afiseaza generatiile pastrate in text")
    values = vars(parser.parse_args(argv))

    path = values.pop("automaton")
    resume = values.pop("resume")
    show = values.pop("show")
    # ce a ramas in values sunt doar parametrii experimentului dati in linia de comanda
    automaton = load_automaton(path, experiment_overrides=values)
    experiment = automaton.experiment
    rng = np.random.default_rng(experiment.seed)

    # starea de start: din fisier salvat sau din "init" din json
    if resume:
        if has_saved_rng(resume):
            state = load_state(resume, automaton, rng=rng)
        else:
            state = load_state(resume, automaton)
            print("atentie: fisierul nu are generatorul aleator, deci la automate cu prob "
                  "continuarea nu e identica cu o rulare neintrerupta")
        print(f"continuam de la generatia {state.generation} din {resume}")
    else:
        state = load_initial_state(automaton)

    result = run(automaton, state, experiment, rng)
    states = kept_states(result)

    if show:
        if np.atleast_2d(result.final_state.grid).shape[0] == 1:
            print(render_rows(states, automaton))
        else:
            print(render_generations(states, automaton))
        print()

    # salvam: starea finala mereu (cu generatorul, ca sa se poata continua exact)
    out_dir = Path(experiment.output_dir)
    base = file_name(automaton.name)
    final = result.final_state
    final_path = save_state(final, automaton, out_dir / f"{base}-gen{final.generation}.npz",
                            overwrite=True, rng=rng)

    # + generatiile intermediare pastrate, daca s-a cerut (fara generator)
    saved_extra = 0
    if experiment.save_intermediate:
        for kept in states:
            if kept.generation == final.generation:
                continue
            save_state(kept, automaton, out_dir / f"{base}-gen{kept.generation}.npz", overwrite=True)
            saved_extra += 1

    print(f"gata: {result.steps} generatii (de la {final.generation - result.steps} "
          f"la {final.generation}) in {result.duration:.2f} s")
    print(f"stare finala salvata in: {final_path}")
    if saved_extra > 0:
        print(f"generatii intermediare salvate: {saved_extra} fisiere in {out_dir}")
    return 0


def validate_command(argv) -> int:
    parser = argparse.ArgumentParser(prog="python -m cellab.cli validate",
                                     description="verifica un fisier json de automat")
    parser.add_argument("automaton", help="fisierul json al automatului")
    path = parser.parse_args(argv).automaton

    automaton = load_automaton(path)
    problems = validate(automaton)
    if not problems:
        print(f"ok: {path} e valid")
        return 0

    has_errors = False
    for problem in problems:
        print(problem)
        if problem.startswith("Eroare"):
            has_errors = True
    return 1 if has_errors else 0


COMMANDS = {
    "run": run_command,
    "validate": validate_command,
}


def main(argv=None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    if not argv or argv[0] in ("-h", "--help", "help"):
        print(HELP)
        return 0

    if argv[0] not in COMMANDS:
        # mod vechi: "python -m cellab.cli fisier.json" afiseaza configuratia experimentului
        show_experiment_config(argv)
        return 0

    command = COMMANDS[argv[0]]
    try:
        return command(argv[1:])
    except (ValueError, FileExistsError) as error:
        # mesaj scurt, fara traceback python
        print(f"eroare: {error}", file=sys.stderr)
        return 2
