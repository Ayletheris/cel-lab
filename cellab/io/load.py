import ast
import json
import math
from pathlib import Path

from cellab.core.model import Automaton
from cellab.core.numeric import COMPARISONS, DIRECTIONS, FUNCTIONS, OPERATORS


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _object(value, allowed, required, path):
    _require(isinstance(value, dict), f"{path}: se asteapta un obiect.")
    _require(not value.keys() - allowed, f"{path}: campuri necunoscute.")
    missing = required - value.keys()
    _require(not missing, f"{path}: lipsesc {', '.join(sorted(missing))}.")


def _integer(value, path, minimum=None):
    _require(type(value) is int, f"{path}: se asteapta un intreg.")
    if minimum is not None:
        _require(value >= minimum, f"{path}: valoarea minima este {minimum}.")


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        _require(key not in result, f"JSON: cheia '{key}' apare de doua ori.")
        result[key] = value
    return result


def _constant(value):
    raise ValueError(f"JSON: valoarea {value} nu este un numar finit.")


def _expression(expression, neighborhood, height):
    _require(isinstance(expression, str) and expression.strip(),
             "rules.expression: se asteapta o expresie numerica.")
    try:
        tree = ast.parse(expression, mode="eval")
    except (SyntaxError, ValueError):
        raise ValueError("rules.expression: sintaxa invalida.") from None
    names = {"celula"}
    for name, (dy, dx) in DIRECTIONS.items():
        if height == 1 and dy or neighborhood["type"] == "von_neumann" and dy and dx:
            continue
        names.add(name)

    def valid(node):
        if isinstance(node, ast.Constant):
            try:
                return type(node.value) in (int, float) and math.isfinite(node.value)
            except OverflowError:
                return False
        if isinstance(node, ast.Name):
            return node.id in names
        if isinstance(node, ast.UnaryOp):
            return isinstance(node.op, ast.USub) and valid(node.operand)
        if isinstance(node, ast.BinOp):
            return type(node.op) in OPERATORS and valid(node.left) and valid(node.right)
        if isinstance(node, ast.Compare):
            return (len(node.ops) == 1 and type(node.ops[0]) in COMPARISONS
                    and valid(node.left) and valid(node.comparators[0]))
        if isinstance(node, ast.Call):
            return (isinstance(node.func, ast.Name) and node.func.id in FUNCTIONS
                    and bool(node.args) and not node.keywords and all(map(valid, node.args)))
        return False

    _require(valid(tree.body), "rules.expression: operatie sau directie nepermisa.")


def _rules(rules, states, neighborhood, height):
    _require(isinstance(rules, list) and bool(rules), "rules: se asteapta o lista nevida.")
    for index, rule in enumerate(rules):
        _require(isinstance(rule, dict), f"rules[{index}]: se asteapta un obiect.")
    kind = rules[0].get("type")
    _require(kind in ("count", "table", "numeric"), "rules.type: tip necunoscut.")
    _require(all(rule.get("type") == kind for rule in rules),
             "rules: nu se pot combina tipuri diferite.")
    if kind != "count":
        _require(len(rules) == 1, "rules: este permisa exact o regula table sau numeric.")
        rule = rules[0]
        field = "table" if kind == "table" else "expression"
        _object(rule, {"type", field}, {"type", field}, "rules[0]")
        _require(neighborhood["radius"] == 1, "neighborhood.radius: trebuie sa fie 1.")
        if kind == "numeric":
            _require(states == ["number"], "states: regulile numerice cer [\"number\"].")
            _expression(rule[field], neighborhood, height)
        else:
            _require(states == [0, 1] and height == 1 and neighborhood["type"] == "moore",
                     "table: sunt necesare states [0, 1], height 1 si vecinatate moore.")
            patterns = {format(i, "03b") for i in range(8)}
            _object(rule[field], patterns, patterns, "rules.table")
            _require(all(type(v) is int and v in (0, 1) for v in rule[field].values()),
                     "rules.table: rezultatele trebuie sa fie 0 sau 1.")
        return rule

    _require(states != ["number"], "states: regulile count cer stari intregi.")
    radius = neighborhood["radius"]
    maximum = (2 * radius if height == 1 else
               (2 * radius + 1) ** 2 - 1 if neighborhood["type"] == "moore" else
               2 * radius * (radius + 1))
    result, seen = [], set()
    for index, rule in enumerate(rules):
        path = f"rules[{index}]"
        _object(rule, {"type", "from", "count", "in", "to", "otherwise"},
                {"type", "from", "to"}, path)
        conditional = {"count", "in", "otherwise"} & rule.keys()
        _require(not conditional or len(conditional) == 3,
                 f"{path}: count, in si otherwise trebuie specificate impreuna.")
        for key in ("from", "count", "to", "otherwise"):
            if key in rule:
                _integer(rule[key], f"{path}.{key}")
                _require(rule[key] in states, f"{path}.{key}: stare nedeclarata.")
        if conditional:
            counts = rule["in"]
            _require(isinstance(counts, list) and bool(counts), f"{path}.in: lista nevida necesara.")
            for count in counts:
                _integer(count, f"{path}.in", 0)
                _require(count <= maximum, f"{path}.in: maxim {maximum} vecini.")
            _require(len(set(counts)) == len(counts), f"{path}.in: valori duplicate.")
        if rule["from"] in seen:
            continue
        seen.add(rule["from"])
        converted = {"state": rule["from"], "next_state": rule["to"]}
        if conditional:
            converted.update(neighbor_state=rule["count"], counts=rule["in"])
            result.append(converted)
            result.append({"state": rule["from"], "next_state": rule["otherwise"]})
        else:
            result.append(converted)
    return result


def load_automaton_from_text(text: str) -> Automaton:
    _require(isinstance(text, str), "JSON: se asteapta text.")
    try:
        data = json.loads(text, object_pairs_hook=_pairs, parse_constant=_constant)
    except json.JSONDecodeError as error:
        raise ValueError(f"JSON invalid la linia {error.lineno}, coloana {error.colno}.") from None
    except ValueError as error:
        message = str(error)
        raise ValueError(message if message.startswith("JSON:") else "JSON invalid: numar prea mare.") from None
    _object(data, {"version", "grid", "states", "neighborhood", "rules", "init"}, {"rules"}, "automat")
    _integer(data.get("version", 1), "version")
    _require(data.get("version", 1) == 1, "version: este acceptata doar versiunea 1.")
    grid = data.get("grid", {})
    _object(grid, {"width", "height", "boundary"}, set(), "grid")
    width, height = grid.get("width", 10), grid.get("height", 10)
    _integer(width, "grid.width", 1)
    _integer(height, "grid.height", 1)
    boundary = grid.get("boundary", "fixed")
    _require(boundary in ("fixed", "wrap"), "grid.boundary: foloseste fixed sau wrap.")
    states = data.get("states", [0, 1])
    _require(isinstance(states, list) and bool(states), "states: lista nevida necesara.")
    numeric = states == ["number"]
    if not numeric:
        for value in states:
            _integer(value, "states")
        _require(len(set(states)) == len(states), "states: valori duplicate.")
        _require(boundary != "fixed" or 0 in states, "states: marginea fixed necesita starea 0.")
    neighborhood = {"type": "moore", "radius": 1}
    supplied = data.get("neighborhood", {})
    _object(supplied, {"type", "radius"}, set(), "neighborhood")
    neighborhood.update(supplied)
    _require(neighborhood["type"] in ("moore", "von_neumann"), "neighborhood.type: tip necunoscut.")
    _integer(neighborhood["radius"], "neighborhood.radius", 1)
    rules = _rules(data["rules"], states, neighborhood, height)
    init = data["init"] if "init" in data else [[0] * width for _ in range(height)]
    _require(isinstance(init, list) and len(init) == height, "init: numar de randuri diferit de grid.height.")
    for y, row in enumerate(init):
        _require(isinstance(row, list) and len(row) == width, f"init[{y}]: lungime diferita de grid.width.")
        for x, value in enumerate(row):
            path = f"init[{y}][{x}]"
            _require(type(value) in (int, float), f"{path}: se asteapta un numar.")
            if numeric:
                try:
                    finite = math.isfinite(value)
                except OverflowError:
                    finite = False
                _require(finite, f"{path}: numarul trebuie sa fie finit.")
            else:
                _integer(value, path)
                _require(value in states, f"{path}: stare nedeclarata.")
    return Automaton([height, width], "toroidal" if boundary == "wrap" else "fixed",
                     states, neighborhood, rules, init)


def load_automaton(cale: str | Path) -> Automaton:
    try:
        text = Path(cale).read_text(encoding="utf-8-sig")
    except FileNotFoundError:
        raise ValueError(f"Fisierul nu exista: {cale}") from None
    except UnicodeError:
        raise ValueError(f"Fisierul nu este text UTF-8: {cale}") from None
    except OSError:
        raise ValueError(f"Fisierul nu poate fi citit: {cale}") from None
    return load_automaton_from_text(text)
