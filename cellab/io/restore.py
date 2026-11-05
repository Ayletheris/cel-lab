import json
import zlib
from datetime import datetime
from pathlib import Path
from zipfile import BadZipFile

import numpy as np

from cellab.core.model import Automaton, State
from cellab.io.load import _constant, _pairs
from cellab.io.save import STATE_FORMAT_VERSION, _valid_size, _valid_states
from cellab.io.rng import _restore_rng


def _check(condition, message):
    if not condition:
        raise ValueError(message)


def _read_archive(cale):
    try:
        archive = np.load(cale, allow_pickle=False)
        _check(isinstance(archive, np.lib.npyio.NpzFile), "Format NPZ invalid.")
        with archive:
            names = set(archive.files)
            _check(len(names) == len(archive.files) and {"grid", "metadata"} <= names
                   and names <= {"grid", "metadata", "rng_state"},
                   "Campurile arhivei sunt invalide.")
            return archive["grid"], archive["metadata"], archive["rng_state"] if "rng_state" in names else None
    except FileNotFoundError:
        raise ValueError(f"Fisierul nu exista: {cale}") from None
    except OSError:
        raise ValueError(f"Fisierul nu poate fi citit: {cale}") from None
    except (ValueError, EOFError, BadZipFile, KeyError, zlib.error):
        raise ValueError("Fisierul de stare este stricat sau nu este o arhiva NPZ valida.") from None


def load_state(cale: str | Path, automaton: Automaton, rng: np.random.Generator | None = None) -> State:
    _check(rng is None or isinstance(rng, np.random.Generator), "rng trebuie sa fie un generator NumPy.")
    _check(isinstance(automaton, Automaton), "Se asteapta un obiect Automaton.")
    _check(_valid_size(automaton.grid_size), "Dimensiunile automatului sunt invalide.")
    _check(_valid_states(automaton.states), "Lista de stari a automatului este invalida.")
    grid, encoded, rng_state = _read_archive(cale)
    _check(encoded.shape == () and encoded.dtype.kind == "U", "Metadatele trebuie sa fie un sir JSON scalar.")
    try:
        metadata = json.loads(encoded.item(), object_pairs_hook=_pairs, parse_constant=_constant)
    except (ValueError, RecursionError):
        raise ValueError("Metadatele JSON din fisier sunt invalide.") from None
    _check(isinstance(metadata, dict), "Metadatele din fisier trebuie sa fie un obiect JSON.")
    version = metadata.get("format_version")
    _check(type(version) is int and version == STATE_FORMAT_VERSION,
           f"Versiunea formatului nu este suportata; este necesara versiunea {STATE_FORMAT_VERSION}.")
    required = {"generation", "automaton_name", "grid_size", "states", "seed", "saved_at"}
    _check(required <= metadata.keys(), "Metadatele fisierului sunt incomplete.")
    generation = metadata["generation"]
    _check(type(generation) is int and generation >= 0, "Generatia din fisier trebuie sa fie un intreg nenegativ.")
    _check(type(metadata["seed"]) is int and metadata["seed"] >= 0, "Seedul din fisier este invalid.")
    name = metadata["automaton_name"]
    _check(isinstance(name, str) and bool(name.strip()), "Numele automatului din fisier este invalid.")
    try:
        saved_at = datetime.fromisoformat(metadata["saved_at"])
        _check(saved_at.tzinfo is not None, "Data fara fus orar.")
    except (ValueError, TypeError):
        raise ValueError("Data salvarii din fisier este invalida.") from None
    size, states = metadata["grid_size"], metadata["states"]
    _check(_valid_size(size), "Dimensiunile din metadate sunt invalide.")
    _check(_valid_states(states), "Starile declarate in metadate sunt invalide.")
    _check(grid.dtype.kind in "iuf" and np.isfinite(grid).all(), "Grila din fisier trebuie sa contina numere reale finite.")
    _check(grid.shape == tuple(size) or grid.ndim == 1 and size == [1, grid.size],
           "Dimensiunile grilei din fisier nu corespund metadatelor.")
    _check(size == list(automaton.grid_size),
           f"Fisierul este pentru un automat de {size[1]}x{size[0]}; automatul dat are {automaton.grid_size[1]}x{automaton.grid_size[0]}.")
    numeric = states == ["number"] or automaton.states == ["number"]
    same_states = states == automaton.states if numeric else set(states) == set(automaton.states)
    _check(same_states, "Starile declarate in fisier nu coincid cu starile automatului dat.")
    _check(states == ["number"] or np.isin(grid, states).all(), "Grila din fisier contine stari nedeclarate.")
    _restore_rng(rng_state, rng)
    return State(grid=grid, generation=generation)
