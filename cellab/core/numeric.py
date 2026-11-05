"""Reguli numerice: celulele tin numere, regula e o expresie text.

Ex. difuzie:  "media(celula, nord, sud, est, vest)"
Ex. sandpile: "celula - 4*(celula >= 4) + (nord >= 4) + (sud >= 4) + (est >= 4) + (vest >= 4)"
"""

import ast
import operator

import numpy as np

# singurele operatii permise in expresii (nimic altceva nu se executa)
OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}
COMPARISONS = {
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
}

# directii: (schimbare de rand, schimbare de coloana)
DIRECTIONS = {
    "nord": (-1, 0),
    "sud": (1, 0),
    "est": (0, 1),
    "vest": (0, -1),
    "nord_est": (-1, 1),
    "nord_vest": (-1, -1),
    "sud_est": (1, 1),
    "sud_vest": (1, -1),
}


def suma(values):
    total = values[0]
    for value in values[1:]:
        total = total + value
    return total


def media(values):
    return suma(values) / len(values)


def minim(values):
    result = values[0]
    for value in values[1:]:
        result = np.minimum(result, value)
    return result


def maxim(values):
    result = values[0]
    for value in values[1:]:
        result = np.maximum(result, value)
    return result


# functiile permise in expresii
FUNCTIONS = {"suma": suma, "media": media, "min": minim, "max": maxim}


def neighbor_values(grid: np.ndarray, row_step: int, col_step: int, boundary: str) -> np.ndarray:
    """Pt fiecare celula (r, c) intoarce valoarea celulei (r + row_step, c + col_step)."""

    if boundary == "toroidal":
        # marginea se continua pe partea opusa
        return np.roll(grid, (-row_step, -col_step), axis=(0, 1))

    # margine fixa: in afara grilei e 0
    height, width = grid.shape
    padded = np.pad(grid, 1)
    first_row = 1 + row_step
    first_col = 1 + col_step
    return padded[first_row : first_row + height, first_col : first_col + width]


def evaluate(node, variables: dict):
    """Calculeaza un nod din expresie. Orice altceva decat ce e permis da eroare."""

    # numar simplu, ex. 4 sau 0.5
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            return node.value
        raise ValueError("only numbers are allowed in expressions")

    # nume de variabila, ex. celula sau nord
    if isinstance(node, ast.Name):
        if node.id not in variables:
            raise ValueError(f"unknown name in expression: {node.id}")
        return variables[node.id]

    # minus in fata, ex. -celula
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -evaluate(node.operand, variables)

    # + - * /
    if isinstance(node, ast.BinOp) and type(node.op) in OPERATORS:
        left = evaluate(node.left, variables)
        right = evaluate(node.right, variables)
        return OPERATORS[type(node.op)](left, right)

    # comparatie, ex. celula >= 4. Rezultatul e 1 sau 0 (numar), nu True/False,
    # ca sa se poata aduna: (nord >= 4) + (sud >= 4) = 2 daca amandoua sunt adevarate
    if isinstance(node, ast.Compare) and len(node.ops) == 1 and type(node.ops[0]) in COMPARISONS:
        left = evaluate(node.left, variables)
        right = evaluate(node.comparators[0], variables)
        answer = COMPARISONS[type(node.ops[0])](left, right)
        return np.asarray(answer).astype(int)

    # apel de functie, ex. media(celula, nord)
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and not node.keywords:
        if node.func.id not in FUNCTIONS:
            raise ValueError(f"function not allowed in expression: {node.func.id}")
        values = [evaluate(argument, variables) for argument in node.args]
        if len(values) == 0:
            raise ValueError(f"{node.func.id}() needs at least one value")
        return FUNCTIONS[node.func.id](values)

    raise ValueError("operation not allowed in expression")


def apply_numeric(grid: np.ndarray, expression: str, boundary: str = "fixed") -> np.ndarray:
    """Un pas: noua valoare a fiecarei celule = expresia calculata pe grila veche."""

    if boundary not in {"fixed", "toroidal"}:
        raise ValueError(f"unknown boundary: {boundary}")
    if grid.ndim != 2:
        raise ValueError("numeric rules work on a 2D grid")

    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError:
        raise ValueError(f"cannot read expression: {expression}")

    # variabilele pe care le poate folosi expresia
    variables = {"celula": grid}
    for name, (row_step, col_step) in DIRECTIONS.items():
        variables[name] = neighbor_values(grid, row_step, col_step, boundary)

    result = np.asarray(evaluate(tree.body, variables))

    # expresie fara variabile (ex. "5") da un singur numar, il punem pe toata grila
    if result.shape != grid.shape:
        result = np.broadcast_to(result, grid.shape).copy()
    return result
