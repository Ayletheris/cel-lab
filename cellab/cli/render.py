"""afisarea grilei ca text, ca sa se poata vedea in terminal."""

import numpy as np

from cellab.core.model import Automaton, State

# caracterele pt starile discrete, in ordinea din automaton.states
# prima stare (de obicei 0 = gol/mort) e "." ca sa nu incarce ecranul
STATE_CHARS = [".", "#", "o", "+", "*", "@", "%", "x", "=", "~"]

# pt automate numerice (ex. difuzie): de la valoare mica la valoare mare
NUMBER_CHARS = [".", ":", "-", "=", "+", "*", "#", "%", "@"]


def is_numeric(automaton: Automaton) -> bool:
    """automat cu numere (states = ["number"]) in loc de stari fixe"""
    return automaton.states == ["number"]


def state_symbols(automaton: Automaton) -> dict:
    """dict valoare stare -> caracter. ex. {0: ".", 1: "#"}"""
    if len(automaton.states) > len(STATE_CHARS):
        raise ValueError(f"pot afisa cel mult {len(STATE_CHARS)} stari in text")

    symbols = {}
    for index, value in enumerate(automaton.states):
        symbols[value] = STATE_CHARS[index]
    return symbols


def number_to_char(value, low, high) -> str:
    """alege un caracter dupa cat de mare e valoarea intre low si high"""
    if high == low:
        return NUMBER_CHARS[0]
    # pozitia valorii intre low si high, de la 0 la 1
    fraction = (value - low) / (high - low)
    index = int(round(fraction * (len(NUMBER_CHARS) - 1)))
    return NUMBER_CHARS[index]


def crop(grid: np.ndarray, max_width: int, max_height: int):
    """taie grila daca e prea mare pt ecran; intoarce grila taiata + mesaj (sau "")"""
    height, width = grid.shape
    message = ""
    if width > max_width or height > max_height:
        shown_width = min(width, max_width)
        shown_height = min(height, max_height)
        message = f"(se vede doar coltul de {shown_height}x{shown_width} din grila de {height}x{width})"
    return grid[:max_height, :max_width], message


def grid_lines(grid: np.ndarray, automaton: Automaton) -> list:
    """transforma grila in randuri de text (fara legenda)"""
    lines = []

    if is_numeric(automaton):
        low = float(grid.min())
        high = float(grid.max())
        for row in grid:
            line = ""
            for value in row:
                line += number_to_char(float(value), low, high)
            lines.append(line)
        return lines

    symbols = state_symbols(automaton)
    for row in grid:
        line = ""
        for value in row:
            line += symbols.get(value.item(), "?")
        lines.append(line)
    return lines


def legend(grid: np.ndarray, automaton: Automaton) -> str:
    """textul de sub grila care spune ce inseamna fiecare caracter"""
    if is_numeric(automaton):
        return f"legenda: '{NUMBER_CHARS[0]}' = minim ({grid.min():.3g}), '{NUMBER_CHARS[-1]}' = maxim ({grid.max():.3g})"

    parts = []
    for value, char in state_symbols(automaton).items():
        parts.append(f"'{char}' = {value}")
    return "legenda: " + ", ".join(parts)


def render_text(state: State, automaton: Automaton, max_width: int = 80, max_height: int = 40) -> str:
    """o generatie ca text: titlu, grila, legenda"""
    # grila 1D (un singur rand) o tratam ca grila cu 1 rand
    grid = np.atleast_2d(state.grid)
    shown, message = crop(grid, max_width, max_height)

    lines = [f"generatia {state.generation}"]
    lines.extend(grid_lines(shown, automaton))
    if message:
        lines.append(message)
    lines.append(legend(grid, automaton))
    return "\n".join(lines)


def render_generations(states: list, automaton: Automaton, max_width: int = 80, max_height: int = 40) -> str:
    """mai multe generatii una sub alta, cu un rand gol intre ele"""
    blocks = []
    for state in states:
        blocks.append(render_text(state, automaton, max_width, max_height))
    return "\n\n".join(blocks)


def render_rows(states: list, automaton: Automaton, max_width: int = 80) -> str:
    """pt automate 1D (ex. Rule 30): fiecare generatie e un rand al aceleiasi imagini"""
    lines = []
    message = ""
    for state in states:
        grid = np.atleast_2d(state.grid)
        if grid.shape[0] != 1:
            raise ValueError("render_rows merge doar pt automate cu un singur rand")
        shown, message = crop(grid, max_width, 1)
        lines.append(grid_lines(shown, automaton)[0])

    if message:
        lines.append(message)
    lines.append(legend(np.atleast_2d(states[-1].grid), automaton))
    return "\n".join(lines)
