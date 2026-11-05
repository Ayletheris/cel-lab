"""testul cap-coada pt livrabilul 2: citire json -> rulare -> salvare -> restaurare -> continuare.

daca testul asta trece, livrabilul 2 e functional cap-coada.
daca pica, mesajul spune in ce automat / ce pas; anunta persoana care se ocupa de modulul ala.
"""

from pathlib import Path

import numpy as np
import pytest

from cellab.core.experiment import Experiment
from cellab.core.run import run
from cellab.io import load_automaton, load_automaton_from_text, load_initial_state, load_state, save_state
from cellab.questions.basic import count_after, state_after
from cellab.questions.stability import find_cycle, find_stable

EXAMPLES = Path(__file__).resolve().parents[1] / "automata" / "examples"

# cele 4 automate din livrabil (forest_fire_random are si probabilitati)
AUTOMATA = ["game_of_life.json", "brians_brain.json", "rule30.json", "forest_fire_random.json"]


@pytest.mark.parametrize("name", AUTOMATA)
def test_run_save_restore_continue_is_same_as_one_run(name, tmp_path):
    automaton = load_automaton(EXAMPLES / name)
    start = load_initial_state(automaton)
    seed = 7

    # varianta 1: 10 generatii dintr-o bucata
    one_run = run(automaton, start, Experiment(N=10, seed=seed), np.random.default_rng(seed))

    # varianta 2: 5 generatii, salvare, restaurare, inca 5 generatii
    rng = np.random.default_rng(seed)
    first_half = run(automaton, start, Experiment(N=5, seed=seed), rng)
    path = save_state(first_half.final_state, automaton, tmp_path / "jumatate.npz", rng=rng)

    new_rng = np.random.default_rng(12345)  # alt seed; load_state ii pune starea salvata
    restored = load_state(path, automaton, rng=new_rng)
    assert restored.generation == 5
    second_half = run(automaton, restored, Experiment(N=5, seed=seed), new_rng)

    assert second_half.final_state.generation == 10
    np.testing.assert_array_equal(second_half.final_state.grid, one_run.final_state.grid,
                                  err_msg=f"{name}: rularea cu pauza difera de rularea continua")


def test_questions_on_known_examples():
    # life.json = blinker: perioada 2, nu e stabil, are mereu 3 celule vii
    life = load_automaton(EXAMPLES / "life.json")
    start = load_initial_state(life)
    assert state_after(life, start, 2).grid.tolist() == start.grid.tolist()  # Q1
    assert count_after(life, start, 7, 1) == 3  # Q4
    assert find_stable(life, start, max_steps=100) is None  # Q2
    assert find_cycle(life, start) == (0, 2)  # Q5

    # forest_fire.json: focul arde tot si apoi nu se mai schimba nimic
    fire = load_automaton(EXAMPLES / "forest_fire.json")
    fire_start = load_initial_state(fire)
    stable_from = find_stable(fire, fire_start)
    assert stable_from is not None
    assert count_after(fire, fire_start, stable_from, 2) == 0  # nu mai e niciun foc


def test_bad_json_is_refused_with_message():
    with pytest.raises(ValueError) as error:
        load_automaton_from_text("{ nu e json")
    assert str(error.value)  # are mesaj, nu e gol


def test_restore_on_wrong_automaton_is_refused(tmp_path):
    life = load_automaton(EXAMPLES / "game_of_life.json")  # 8x8
    brain = load_automaton(EXAMPLES / "brians_brain.json")  # 20x20
    path = save_state(load_initial_state(life), life, tmp_path / "life.npz")
    with pytest.raises(ValueError):
        load_state(path, brain)
