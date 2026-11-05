import json

from cellab.core.model import Automaton
from cellab.core.experiment import experiment_problems
from cellab.io.defaults import DEFAULTS
from cellab.io.generation import _prepare_generation


def _canonical(value, key=""):
    if isinstance(value, dict):
        return {k: _canonical(v, k) for k, v in value.items()}
    if isinstance(value, list):
        values = [_canonical(v) for v in value]
        if key in ("counts", "in", "all", "any"):
            values.sort(key=lambda v: json.dumps(v, sort_keys=True))
        return values
    return value


def validate(automaton: Automaton | dict) -> list[str]:
    problems = []

    def error(message):
        problems.append(f"Eroare: {message}")

    def warning(message):
        problems.append(f"Avertisment: {message}")

    def default(key):
        value = DEFAULTS[key]
        message = f"lipseste {key}; se foloseste {value}."
        if f"Avertisment: {message}" not in problems:
            warning(message)
        return value

    if isinstance(automaton, Automaton):
        data = vars(automaton)
        size = data.get("grid_size")
        boundary = data.get("boundary")
        defaults = data.get("defaults_used", [])
        if isinstance(defaults, list):
            for key in defaults:
                if isinstance(key, str) and key in DEFAULTS:
                    default(key)
    elif isinstance(automaton, dict):
        data = automaton
        grid = data.get("grid", {})
        if grid is None:
            grid = {}
        if not isinstance(grid, dict):
            error("grid trebuie sa fie un obiect.")
            grid = {}
        size = [grid.get("height"), grid.get("width")]
        boundary = grid.get("boundary")
    else:
        return ["Eroare: se asteapta un Automaton sau un obiect JSON."]

    if size is None:
        size = [None, None]
    if not isinstance(size, (list, tuple)) or len(size) != 2:
        error("grid_size trebuie sa contina inaltimea si latimea.")
    else:
        for key, value in zip(("grid.height", "grid.width"), size):
            if value is None:
                default(key)
            elif type(value) is not int or value <= 0:
                error(f"{key} trebuie sa fie un intreg pozitiv.")
    if boundary is None:
        boundary = default("grid.boundary")
    if boundary not in ("fixed", "wrap", "toroidal"):
        error("margine necunoscuta; foloseste fixed sau wrap.")

    neighborhood = data.get("neighborhood")
    if neighborhood is None:
        neighborhood = {}
    if isinstance(neighborhood, dict):
        kind = neighborhood.get("type")
        radius = neighborhood.get("radius")
        if kind is None:
            kind = default("neighborhood.type")
        if radius is None:
            radius = default("neighborhood.radius")
        if type(radius) is not int or radius <= 0:
            error("neighborhood.radius trebuie sa fie un intreg pozitiv.")
    elif isinstance(neighborhood, list):
        kind = "offsets"
        if not neighborhood or any(type(v) is not int for v in neighborhood):
            error("vecinatatea 1D necesita o lista nevida de offseturi intregi.")
    else:
        kind = neighborhood
    if isinstance(kind, str):
        kind = kind.lower().replace(" ", "_").replace("-", "_")
    if kind not in ("moore", "von_neumann", "offsets"):
        error("vecinatate necunoscuta; foloseste moore sau von_neumann.")

    states = data.get("states")
    if states is None:
        states = default("states")
    if not isinstance(states, list) or not states:
        error("states trebuie sa fie o lista nevida.")
        states = []
    numeric = states == ["number"]
    if not numeric and any(type(v) is not int for v in states):
        error("states trebuie sa contina stari intregi sau doar number.")
        states = [v for v in states if type(v) is int]
    if not numeric and len(set(states)) != len(states):
        error("states contine stari duplicate.")

    def reference(value, path):
        if isinstance(value, dict) and "next_mod" in value:
            modulus = value["next_mod"]
            if type(modulus) is not int or modulus <= 0:
                error(f"{path}: next_mod trebuie sa fie un intreg pozitiv.")
            elif not all(v in states for v in range(min(modulus, len(states) + 1))):
                error(f"{path}: next_mod foloseste stari nedeclarate.")
        elif type(value) is not int or value not in states:
            error(f"{path}: stare nedeclarata.")

    def condition_references(condition, path, depth=0):
        if depth > 30 or not isinstance(condition, dict):
            error(f"{path}: conditie invalida.")
            return
        if "neighbor_state" in condition:
            reference(condition["neighbor_state"], f"{path}.neighbor_state")
        for key in ("all", "any"):
            if key in condition:
                items = condition[key]
                if not isinstance(items, list) or not items:
                    error(f"{path}.{key}: lista de conditii nevida necesara.")
                else:
                    for index, item in enumerate(items):
                        condition_references(item, f"{path}.{key}[{index}]", depth + 1)
        if "more_than" in condition:
            pair = condition["more_than"]
            if not isinstance(pair, list) or len(pair) != 2:
                error(f"{path}.more_than: sunt necesare doua stari.")
            else:
                for value in pair:
                    reference(value, f"{path}.more_than")

    rules = data.get("rules")
    if isinstance(rules, dict):
        rules = [rules]
    if not isinstance(rules, list):
        error("rules trebuie sa fie o lista de reguli sau o regula table/numeric.")
        rules = []
    signatures, covered = {}, []
    for index, rule in enumerate(rules):
        path = f"rules[{index}]"
        if not isinstance(rule, dict):
            error(f"{path}: regula trebuie sa fie un obiect.")
            continue
        if "prob" in rule:
            probability = rule["prob"]
            if (type(probability) not in (int, float)
                    or not 0 <= probability <= 1):
                error(f"{path}.prob: probabilitatea trebuie sa fie intre 0 si 1.")
        kind = rule.get("type", "count")
        if kind == "numeric":
            if not numeric:
                error(f"{path}: regulile numerice necesita states [\"number\"].")
            covered.extend(states)
            continue
        if kind == "table":
            table = rule.get("table")
            if isinstance(table, dict):
                for value in table.values():
                    reference(value, f"{path}.table")
            elif type(table) is not int or not 0 <= table <= 255:
                error(f"{path}.table: tabel sau numar Wolfram invalid.")
            for value in (0, 1):
                reference(value, f"{path}.table")
            covered.extend(value for value in (0, 1) if value in states)
            continue
        if kind != "count":
            error(f"{path}: tip de regula necunoscut.")
            continue
        source_key = "from" if "from" in rule else "state"
        target_key = "to" if "to" in rule else "next_state"
        for key in (source_key, target_key, "count", "neighbor_state", "otherwise"):
            if key in rule:
                reference(rule[key], f"{path}.{key}")
        if target_key not in rule:
            error(f"{path}: lipseste starea rezultat.")
        if source_key in rule:
            if type(rule[source_key]) is int:
                covered.append(rule[source_key])
        else:
            covered.extend(states)
        condition = rule.get("condition")
        if "condition" in rule:
            condition_references(condition, f"{path}.condition")
        elif "count" in rule or "counts" in rule:
            condition = {"neighbor_state": rule.get("count", rule.get("neighbor_state", 1)),
                         "counts": rule.get("in", rule.get("counts"))}
        try:
            signature = json.dumps(_canonical([source_key in rule, rule.get(source_key), condition]), sort_keys=True)
            result = json.dumps(_canonical([rule.get(target_key), rule.get("otherwise")]), sort_keys=True)
        except (TypeError, ValueError, RecursionError):
            error(f"{path}: structura regulii este invalida.")
            continue
        if signature in signatures and signatures[signature][1] != result:
            error(f"{path} contrazice rules[{signatures[signature][0]}]: aceeasi stare si conditie, rezultate diferite.")
        else:
            signatures[signature] = (index, result)
    if not numeric:
        for state in states:
            if state not in covered:
                warning(f"starea {state} nu are nicio regula; va ramane la fel.")
    if isinstance(data.get("init"), dict):
        effective_size = size
        if isinstance(size, (list, tuple)) and len(size) == 2:
            effective_size = [DEFAULTS[key] if value is None else value
                              for key, value in zip(("grid.height", "grid.width"), size)]
        try:
            _prepare_generation(effective_size, states, data["init"])
        except ValueError as issue:
            error(str(issue))
    if "experiment" in data:
        for issue in experiment_problems(data["experiment"]):
            error(issue)
    return problems
