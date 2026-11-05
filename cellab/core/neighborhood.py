"""Kernel-uri pentru vecinătățile automatelor celulare."""

from collections.abc import Sequence

import numpy as np


def make_kernel(neighborhood: str | Sequence[int], radius: int = 1) -> np.ndarray:
    """Construiește kernel-ul 2D sau, pentru o listă de offset-uri, cel 1D."""

    if radius < 1:
        raise ValueError("radius must be at least 1")

    if not isinstance(neighborhood, str):
        if len(neighborhood) == 0:
            raise ValueError("1D offsets list is empty")
        if not all(isinstance(offset, int) for offset in neighborhood):
            raise ValueError("1D offsets must be integers")
        radius = max(radius, *(abs(offset) for offset in neighborhood))
        width = 2 * radius + 1
        kernel = np.zeros(width, dtype=int)
        for offset in neighborhood:
            if offset != 0:
                kernel[radius + offset] = 1
        return kernel

    width = 2 * radius + 1
    kind = neighborhood.lower().replace(" ", "_").replace("-", "_")
    if kind not in {"moore", "von_neumann"}:
        raise ValueError(f"unknown neighborhood: {neighborhood}")

    kernel = np.ones((width, width), dtype=int) if kind == "moore" else np.zeros((width, width), dtype=int)
    if kind == "von_neumann":
        for row in range(width):
            for column in range(width):
                if abs(row - radius) + abs(column - radius) <= radius:
                    kernel[row, column] = 1
    kernel[radius, radius] = 0
    return kernel
