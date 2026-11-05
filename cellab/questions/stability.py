"""intrebarile Q2 si Q5.

Q2: cand devine stabil? (grila nu se mai schimba: stare(t+1) == stare(t))
Q5: intra intr-un ciclu? (grila revine la o stare deja vazuta si apoi se repeta)

grila e finita si regulile sunt deterministe, deci pana la urma sigur ajunge
intr-un ciclu (stare stabila = ciclu de lungime 1). doar ca poate dura mult,
de aceea avem o limita de pasi (max_steps).
"""

import hashlib

import numpy as np

from cellab.core.model import Automaton, State
from cellab.core.step import step

MAX_STEPS = 10000


def has_probability(automaton: Automaton) -> bool:
    """true daca vreo regula are "prob" (automat cu sansa)"""
    if not isinstance(automaton.rules, list):
        return False
    for rule in automaton.rules:
        if "prob" in rule:
            return True
    return False


def check_deterministic(automaton: Automaton):
    # la automatele cu prob, aceeasi grila poate continua diferit (generatorul a mers mai departe),
    # deci "s-a repetat grila" nu inseamna ca e stabil sau ca e ciclu
    if has_probability(automaton):
        raise ValueError("automatul are reguli cu probabilitate: stabilitatea si ciclurile "
                         "nu se pot stabili doar din grila")


def grid_hash(grid: np.ndarray) -> str:
    """amprenta grilei: un text scurt in loc de toata grila.
    doua grile diferite au practic sigur amprente diferite (sha256)"""
    data = str(grid.shape).encode() + str(grid.dtype).encode() + grid.tobytes()
    return hashlib.sha256(data).hexdigest()


def find_stable(automaton: Automaton, state: State, max_steps: int = MAX_STEPS):
    """Q2: generatia de la care grila nu se mai schimba, sau None daca nu se gaseste in max_steps pasi"""
    check_deterministic(automaton)

    for _ in range(max_steps):
        new_state = step(automaton, state)
        if np.array_equal(new_state.grid, state.grid):
            return state.generation
        state = new_state
    return None


def find_cycle(automaton: Automaton, state: State, max_steps: int = MAX_STEPS):
    """Q5: intoarce (mu, lam) sau None.
    mu  = generatia la care incepe ciclul
    lam = lungimea ciclului (1 = stare stabila)"""
    check_deterministic(automaton)

    seen = {}  # amprenta grilei -> generatia la care am vazut-o prima data
    for _ in range(max_steps + 1):
        key = grid_hash(state.grid)
        if key in seen:
            mu = seen[key]
            lam = state.generation - mu
            return mu, lam
        seen[key] = state.generation
        state = step(automaton, state)
    return None


def generation_in_cycle(n: int, mu: int, lam: int) -> int:
    """dupa ce stim ciclul, starea la generatia n e aceeasi cu starea la generatia intoarsa aici.
    ex. blinker (mu=0, lam=2): generatia 1001 arata ca generatia 1"""
    if n < mu:
        return n
    return mu + (n - mu) % lam
