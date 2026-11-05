import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from cellab.core.model import Automaton, Experiment, State


STATE_FORMAT_VERSION = 2


def _valid_size(value):
    return (isinstance(value, (list, tuple)) and len(value) == 2
            and all(type(v) is int and v > 0 for v in value))


def _valid_states(value):
    return (isinstance(value, list) and bool(value)
            and (value == ["number"] or
                 all(type(v) is int for v in value) and len(set(value)) == len(value)))


def save_state(state: State, automaton: Automaton, cale: str | Path, overwrite: bool = False) -> Path:
    if not isinstance(state, State) or not isinstance(automaton, Automaton):
        raise ValueError("Se asteapta obiecte State si Automaton.")
    if type(overwrite) is not bool:
        raise ValueError("overwrite trebuie sa fie true sau false.")
    if type(state.generation) is not int or state.generation < 0:
        raise ValueError("Generatia trebuie sa fie un intreg nenegativ.")
    if not _valid_size(automaton.grid_size):
        raise ValueError("Dimensiunile automatului sunt invalide.")
    if not _valid_states(automaton.states):
        raise ValueError("Lista de stari a automatului este invalida.")
    grid = state.grid
    if not isinstance(grid, np.ndarray) or grid.dtype.kind not in "iuf":
        raise ValueError("Grila trebuie sa fie o matrice NumPy numerica.")
    expected = tuple(automaton.grid_size)
    if grid.shape != expected and not (grid.ndim == 1 and expected == (1, grid.size)):
        raise ValueError("Dimensiunile starii nu corespund grilei automatului.")
    if not np.isfinite(grid).all():
        raise ValueError("Grila trebuie sa contina numai numere finite.")
    if automaton.states != ["number"] and not np.isin(grid, automaton.states).all():
        raise ValueError("Grila contine stari nedeclarate.")
    if not isinstance(automaton.name, str) or not automaton.name.strip():
        raise ValueError("Numele automatului trebuie sa fie un text nevid.")
    if not isinstance(automaton.experiment, Experiment):
        raise ValueError("Automatul trebuie sa aiba un Experiment valid.")
    metadata = {
        "format_version": STATE_FORMAT_VERSION,
        "generation": state.generation,
        "automaton_name": automaton.name,
        "grid_size": list(automaton.grid_size),
        "states": automaton.states,
        "seed": automaton.experiment.seed,
        "saved_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        path = Path(cale)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("wb" if overwrite else "xb") as file:
            np.savez_compressed(file, grid=grid, metadata=json.dumps(metadata, ensure_ascii=False))
    except FileExistsError:
        raise FileExistsError(f"Fisierul exista deja: {cale}. Foloseste overwrite=True pentru suprascriere.") from None
    except OSError:
        raise ValueError(f"Starea nu poate fi salvata: {cale}") from None
    return path
