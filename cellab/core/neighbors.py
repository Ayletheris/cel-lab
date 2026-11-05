"""Numărarea simultană a vecinilor dintr-o anumită stare."""

from typing import Any

import numpy as np
from scipy.signal import convolve2d


def count_neighbors(
    grid: np.ndarray, target_state: Any, kernel: np.ndarray, boundary: str = "fixed"
) -> np.ndarray:
    """Numără pentru fiecare celulă vecinii în starea cerută."""

    if boundary not in {"fixed", "toroidal"}:
        raise ValueError(f"unknown boundary: {boundary}")

    one_dimensional = grid.ndim == kernel.ndim == 1
    if one_dimensional:
        grid = grid[np.newaxis, :]
        kernel = kernel[np.newaxis, :]

    counts = convolve2d(
        grid == target_state,
        np.flip(kernel),
        mode="same",
        boundary="fill" if boundary == "fixed" else "wrap",
        fillvalue=int(target_state == 0),
    )
    return counts[0] if one_dimensional else counts
