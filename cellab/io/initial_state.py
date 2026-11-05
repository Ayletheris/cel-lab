import json
import math
from pathlib import Path

import numpy as np

from cellab.core.model import Automaton, State


def load_initial_state(automaton: Automaton, source=None, symbols=None) -> State:
    if not isinstance(automaton, Automaton):
        raise ValueError("Se asteapta un obiect Automaton.")
    size = automaton.grid_size
    if (not isinstance(size, (list, tuple)) or len(size) != 2
            or any(type(v) is not int or v <= 0 for v in size)):
        raise ValueError("Grila trebuie sa aiba inaltime si latime intregi pozitive.")
    states = automaton.states
    if not isinstance(states, list) or not states:
        raise ValueError("Lista de stari declarate este invalida.")
    numeric = states == ["number"]
    if not numeric and any(type(v) is not int for v in states):
        raise ValueError("Starile declarate trebuie sa fie intregi sau doar number.")
    if source is None:
        source = automaton.init
    if source is None:
        raise ValueError("Starea initiala lipseste.")
    if isinstance(source, Path):
        return load_initial_state_from_file(automaton, source, symbols)
    if isinstance(source, str):
        symbols = {".": 0, "#": 1} if symbols is None else symbols
        if (not isinstance(symbols, dict)
                or any(not isinstance(k, str) or len(k) != 1 or k.isspace() for k in symbols)):
            raise ValueError("Legenda trebuie sa asocieze cate un caracter unei stari.")
        rows = []
        for y, line in enumerate(source.splitlines(), 1):
            row = []
            for x, char in enumerate(line, 1):
                if char.isspace():
                    continue
                if char not in symbols:
                    raise ValueError(f"Caracter necunoscut '{char}' la linia {y}, coloana {x}.")
                row.append(symbols[char])
            if row:
                rows.append(row)
        source = rows
    if isinstance(source, np.ndarray):
        if source.ndim != 2:
            raise ValueError("Starea initiala trebuie sa fie o matrice 2D.")
        source = source.tolist()
    height, width = size
    if not isinstance(source, (list, tuple)) or len(source) != height:
        raise ValueError(f"Starea initiala trebuie sa aiba {height} randuri si {width} coloane.")
    for y, row in enumerate(source):
        if not isinstance(row, (list, tuple)) or len(row) != width:
            raise ValueError(f"Randul {y + 1} trebuie sa aiba {width} coloane.")
        for x, value in enumerate(row):
            position = f"linia {y + 1}, coloana {x + 1}"
            if type(value) not in (int, float):
                raise ValueError(f"Valoare nenumerica la {position}.")
            try:
                finite = math.isfinite(value)
            except OverflowError:
                finite = False
            if not finite:
                raise ValueError(f"Numarul de la {position} trebuie sa fie finit.")
            if not numeric and value not in states:
                raise ValueError(f"Stare nedeclarata {value} la {position}.")
    try:
        grid = np.array(source, dtype=float if numeric else int, copy=True)
    except (ValueError, TypeError, OverflowError):
        raise ValueError("Valorile starii initiale nu pot fi reprezentate numeric.") from None
    return State(grid=grid, generation=0)


def load_initial_state_from_file(automaton: Automaton, cale: str | Path, symbols=None) -> State:
    try:
        path = Path(cale)
        text = path.read_text(encoding="utf-8-sig")
    except FileNotFoundError:
        raise ValueError(f"Fisierul nu exista: {cale}") from None
    except UnicodeError:
        raise ValueError(f"Fisierul nu este text UTF-8: {cale}") from None
    except OSError:
        raise ValueError(f"Fisierul nu poate fi citit: {cale}") from None
    if path.suffix.lower() == ".json":
        try:
            source = json.loads(text)
        except json.JSONDecodeError as error:
            raise ValueError(f"JSON invalid la linia {error.lineno}, coloana {error.colno}.") from None
        except ValueError:
            raise ValueError("JSON invalid: valoare numerica prea mare.") from None
        if not isinstance(source, list):
            raise ValueError("Fisierul JSON trebuie sa contina o matrice de numere.")
    else:
        source = text
    return load_initial_state(automaton, source, symbols)
