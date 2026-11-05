"""Reguli de tip tabel pentru automate 1D (ex. Rule 30)."""

import numpy as np

# cele 8 tipare "stanga-centru-dreapta", in ordinea din tabelul Wolfram
PATTERNS = ["111", "110", "101", "100", "011", "010", "001", "000"]


def make_table(rule) -> dict:
    """Intoarce tabelul ca dict: tipar -> iesire (0 sau 1)."""

    # varianta 1: nr Wolfram (0-255), ex. 30
    if isinstance(rule, int):
        if rule < 0 or rule > 255:
            raise ValueError("Wolfram rule number must be between 0 and 255")

        # 30 in binar cu 8 cifre = "00011110"
        # prima cifra e pt tiparul 111, a doua pt 110, ... ultima pt 000
        digits = format(rule, "08b")
        table = {}
        for i in range(8):
            pattern = PATTERNS[i]
            table[pattern] = int(digits[i])
        return table

    # varianta 2: dict cu cele 8 cazuri, ex. {"111": 0, "110": 0, ...}
    if sorted(rule.keys()) != sorted(PATTERNS):
        raise ValueError("table needs exactly the 8 patterns 000 .. 111")
    for output in rule.values():
        if output != 0 and output != 1:
            raise ValueError("table outputs must be 0 or 1")
    return dict(rule)


def apply_table(grid: np.ndarray, rule, boundary: str = "fixed") -> np.ndarray:
    """Un pas pe un rand de 0/1. Intoarce un rand nou, nu schimba grila veche."""

    if boundary not in {"fixed", "toroidal"}:
        raise ValueError(f"unknown boundary: {boundary}")

    # accept si grila cu o singura linie (1 x W)
    if grid.ndim == 2:
        if grid.shape[0] != 1:
            raise ValueError("table rules work only on one row")
        new_row = apply_table(grid[0], rule, boundary)
        return new_row[np.newaxis, :]

    table = make_table(rule)

    # vecinii fiecarei celule, ca 2 siruri de aceeasi lungime cu grila
    if boundary == "toroidal":
        # vecinul din stanga al lui i este grid[i-1], cel din dreapta grid[i+1]
        left = np.roll(grid, 1)
        right = np.roll(grid, -1)
    else:
        # in afara grilei e 0
        left = np.concatenate(([0], grid[:-1]))
        right = np.concatenate((grid[1:], [0]))

    # pt fiecare tipar din tabel, gasim celulele care il au si le dam iesirea
    new_grid = np.zeros_like(grid)
    for pattern, output in table.items():
        want_left = int(pattern[0])
        want_center = int(pattern[1])
        want_right = int(pattern[2])

        has_pattern = (left == want_left) & (grid == want_center) & (right == want_right)
        new_grid[has_pattern] = output
    return new_grid
