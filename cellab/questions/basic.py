"""intrebarile Q1 si Q4.

Q1: care e starea dupa N iteratii?
Q4: cate celule de tip X exista dupa N iteratii?
"""

import numpy as np

from cellab.core.model import Automaton, State
from cellab.core.step import step


def is_numeric(automaton: Automaton) -> bool:
    """automat cu numere (states = ["number"]) in loc de stari fixe"""
    return automaton.states == ["number"]


def make_rng(automaton: Automaton, rng=None):
    """daca nu primim generator, il facem din seed-ul experimentului (la fel ca run())"""
    if rng is None:
        return np.random.default_rng(automaton.experiment.seed)
    return rng


def check_n(n):
    if type(n) is not int or n < 0:
        raise ValueError("N trebuie sa fie un intreg >= 0")


def state_after(automaton: Automaton, state: State, n: int, rng=None) -> State:
    """Q1: simulam n pasi de la state si intoarcem starea la care ajungem"""
    check_n(n)
    rng = make_rng(automaton, rng)
    for _ in range(n):
        state = step(automaton, state, rng)
    return state


def count_cells(state: State, cell_state) -> int:
    """cate celule din grila sunt in starea cell_state"""
    return int(np.count_nonzero(state.grid == cell_state))


def count_all(automaton: Automaton, state: State) -> dict:
    """numarul de celule pt fiecare stare declarata. ex. {0: 20, 1: 5}"""
    if is_numeric(automaton):
        raise ValueError("la automate cu numere (ex. difuzie) nu exista tipuri de celule de numarat")

    counts = {}
    for value in automaton.states:
        counts[value] = count_cells(state, value)
    return counts


def count_after(automaton: Automaton, state: State, n: int, cell_state, rng=None) -> int:
    """Q4: cate celule de tip cell_state sunt dupa n pasi"""
    if is_numeric(automaton):
        raise ValueError("la automate cu numere (ex. difuzie) nu exista tipuri de celule de numarat")
    if cell_state not in automaton.states:
        raise ValueError(f"starea {cell_state} nu e declarata in automat (stari: {automaton.states})")

    final = state_after(automaton, state, n, rng)
    return count_cells(final, cell_state)
