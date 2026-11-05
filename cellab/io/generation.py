import math

import numpy as np

from cellab.core.model import Automaton, State


def _check(condition, message):
    if not condition:
        raise ValueError(f"init: {message}")


def _prepare_generation(size, states, spec):
    _check(isinstance(size, (list, tuple)) and len(size) == 2
           and all(type(v) is int and v > 0 for v in size), "dimensiuni de grila invalide.")
    height, width = size
    _check(isinstance(states, list) and bool(states), "lista de stari este invalida.")
    numeric = states == ["number"]
    _check(numeric or all(type(v) is int for v in states), "starile trebuie sa fie intregi.")
    _check(numeric or len(set(states)) == len(states), "starile declarate sunt duplicate.")
    if not numeric:
        try:
            np.asarray(states, dtype=int)
        except (ValueError, OverflowError):
            raise ValueError("init: starile declarate nu pot fi reprezentate numeric.") from None
    _check(isinstance(spec, dict), "se asteapta un obiect de generare.")
    kind = spec.get("type")
    fields = {
        "empty": {"type", "background"},
        "center": {"type", "background", "state"},
        "pattern": {"type", "background", "pattern", "position"},
        "random": {"type", "percentages", "seed"},
    }
    _check(isinstance(kind, str) and kind in fields, "tip de generare necunoscut.")
    _check(not spec.keys() - fields[kind], "campuri de generare necunoscute.")
    result = {"type": kind}

    def state(value, field):
        _check(type(value) in (int, float) and (numeric or type(value) is int),
               f"{field} trebuie sa fie o stare numerica valida.")
        try:
            finite = math.isfinite(value)
        except OverflowError:
            finite = False
        _check(finite, f"{field} trebuie sa fie finit.")
        _check(numeric or value in states, f"{field} foloseste o stare nedeclarata.")
        return value

    if kind == "random":
        _check(not numeric, "random necesita o lista de stari discrete.")
        percentages = spec.get("percentages")
        _check(isinstance(percentages, dict), "percentages trebuie sa fie un obiect cu procente pe stari.")
        declared = {str(value): index for index, value in enumerate(states)}
        weights = np.zeros(len(states), dtype=float)
        for key, value in percentages.items():
            _check(isinstance(key, str) and key in declared,
                   "percentages foloseste o stare nedeclarata sau o cheie invalida.")
            _check(type(value) in (int, float) and 0 <= value <= 100,
                   f"procentul pentru starea {key} trebuie sa fie intre 0 si 100.")
            weights[declared[key]] = value
        total = math.fsum(weights)
        _check(total <= 100 or math.isclose(total, 100, rel_tol=0, abs_tol=1e-9),
               "suma procentelor depaseste 100%.")
        weights[0] += max(0, 100 - total)
        seed = spec.get("seed", 0)
        _check(type(seed) is int and seed >= 0, "seed trebuie sa fie un intreg nenegativ.")
        result.update(weights=weights / weights.sum(), seed=seed)
        return result

    result["background"] = state(spec.get("background", 0 if numeric else states[0]), "background")
    if kind == "center":
        active = 1 if numeric else states[min(1, len(states) - 1)]
        result["state"] = state(spec.get("state", active), "state")
    if kind == "pattern":
        pattern = spec.get("pattern")
        if isinstance(pattern, str):
            rows = [line.split() for line in pattern.splitlines() if line.strip()]
            size = [len(rows), len("".join(rows[0])) if rows else 0]
        elif isinstance(pattern, (list, tuple)) and pattern and isinstance(pattern[0], (list, tuple)):
            size = [len(pattern), len(pattern[0])]
        else:
            raise ValueError("init: pattern trebuie sa fie o matrice nevida sau text cu caractere.")
        _check(all(v > 0 for v in size), "pattern nu poate fi gol.")
        from cellab.io.initial_state import load_initial_state

        template = Automaton(size, "fixed", states, "moore", [])
        result["pattern"] = load_initial_state(template, pattern).grid
        position = spec.get("position")
        _check(isinstance(position, dict) and set(position) == {"x", "y"},
               "position trebuie sa contina x si y.")
        _check(all(type(value) is int and value >= 0 for value in position.values()),
               "coordonatele x si y trebuie sa fie intregi nenegativi.")
        result["position"] = (position["y"], position["x"])
        _check(position["y"] + size[0] <= height and position["x"] + size[1] <= width,
               "tiparul nu incape in grila la pozitia aleasa.")
    return result


def generate_initial_state(automaton: Automaton, spec: dict) -> State:
    if not isinstance(automaton, Automaton):
        raise ValueError("Se asteapta un obiect Automaton.")
    config = _prepare_generation(automaton.grid_size, automaton.states, spec)
    height, width = automaton.grid_size
    if config["type"] == "random":
        rng = np.random.Generator(np.random.PCG64(config["seed"]))
        grid = rng.choice(automaton.states, size=(height, width), p=config["weights"])
    else:
        dtype = float if automaton.states == ["number"] else int
        grid = np.full((height, width), config["background"], dtype=dtype)
        if config["type"] == "center":
            grid[height // 2, width // 2] = config["state"]
        elif config["type"] == "pattern":
            y, x = config["position"]
            pattern = config["pattern"]
            ph, pw = pattern.shape
            grid[y:y + ph, x:x + pw] = pattern
    return State(grid=grid, generation=0)
