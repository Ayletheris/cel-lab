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
from cellab.cli.render import render_generations, render_rows, render_text
from cellab.core.run import run
from cellab.io import load_automaton, load_initial_state, load_state, save_state, validate
from cellab.questions.basic import count_all, state_after
from cellab.questions.stability import MAX_STEPS, find_cycle, find_stable, generation_in_cycle

HELP = """folosire: python -m cellab.cli <comanda> fisier.json [optiuni]

comenzi:
  run          ruleaza automatul N generatii si salveaza starea finala
  validate     verifica fisierul json si arata problemele
  state-after  Q1: arata starea dupa N generatii (N = --generations)
  count        Q4: cate celule din fiecare tip sunt dupa N generatii
  stable       Q2: de la ce generatie grila nu se mai schimba
  cycle        Q5: daca si unde intra intr-un ciclu

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


def question_parser(name, description):
    """parser comun pt intrebari: fisierul json + parametrii experimentului"""
    parser = argparse.ArgumentParser(prog=f"python -m cellab.cli {name}", description=description)
    parser.add_argument("automaton", help="fisierul json al automatului")
    add_experiment_arguments(parser)
    return parser


def load_for_question(parser, argv, extra_options=()):
    """citeste automatul si starea initiala; N vine din --generations (sau din fisier).
    extra_options = optiuni in plus ale comenzii (ex. max_steps), care nu sunt ale experimentului"""
    values = vars(parser.parse_args(argv))
    path = values.pop("automaton")

    extras = {}
    for name in extra_options:
        extras[name] = values.pop(name)

    # ce a ramas in values sunt doar parametrii experimentului
    automaton = load_automaton(path, experiment_overrides=values)
    return automaton, load_initial_state(automaton), extras


def state_after_command(argv) -> int:
    parser = question_parser("state-after", "Q1: starea dupa N generatii")
    automaton, state, _ = load_for_question(parser, argv)
    n = automaton.experiment.N

    final = state_after(automaton, state, n)
    print(f"starea dupa {n} generatii:")
    print(render_text(final, automaton))
    return 0


def count_command(argv) -> int:
    parser = question_parser("count", "Q4: cate celule de fiecare tip sunt dupa N generatii")
    automaton, state, _ = load_for_question(parser, argv)
    n = automaton.experiment.N

    final = state_after(automaton, state, n)
    print(f"dupa {n} generatii:")
    for value, count in count_all(automaton, final).items():
        print(f"  starea {value}: {count} celule")
    return 0


def stable_command(argv) -> int:
    parser = question_parser("stable", "Q2: de la ce generatie grila nu se mai schimba")
    parser.add_argument("--max-steps", type=int, default=MAX_STEPS, help="cati pasi incercam cel mult")
    automaton, state, extras = load_for_question(parser, argv, ["max_steps"])
    max_steps = extras["max_steps"]

    generation = find_stable(automaton, state, max_steps)
    if generation is None:
        print(f"nu devine stabil in primii {max_steps} pasi "
              "(poate intra intr-un ciclu: incearca comanda cycle)")
    else:
        print(f"stabil de la generatia {generation}: de acolo grila nu se mai schimba")
    return 0


def cycle_command(argv) -> int:
    parser = question_parser("cycle", "Q5: daca si unde intra intr-un ciclu")
    parser.add_argument("--max-steps", type=int, default=MAX_STEPS, help="cati pasi incercam cel mult")
    automaton, state, extras = load_for_question(parser, argv, ["max_steps"])
    max_steps = extras["max_steps"]

    cycle = find_cycle(automaton, state, max_steps)
    if cycle is None:
        print(f"nu s-a gasit niciun ciclu in primii {max_steps} pasi (nedeterminat)")
        return 0

    mu, lam = cycle
    print(f"intra in ciclu: incepe la generatia {mu}, lungime {lam}")
    if lam == 1:
        print("(ciclu de lungime 1 = stare stabila)")
    n = automaton.experiment.N
    print(f"deci starea la generatia {n} e aceeasi cu starea la generatia {generation_in_cycle(n, mu, lam)}")
    return 0


COMMANDS = {
    "run": run_command,
    "validate": validate_command,
    "state-after": state_after_command,
    "count": count_command,
    "stable": stable_command,
    "cycle": cycle_command,
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
