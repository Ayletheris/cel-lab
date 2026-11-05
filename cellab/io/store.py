from dataclasses import replace
from pathlib import Path

import numpy as np

from cellab.core.model import Automaton, Experiment, State
from cellab.io.restore import load_state
from cellab.io.save import save_state


class GenerationStore:
    def __init__(self, experiment: Experiment, automaton: Automaton | None = None,
                 mode: str = "checkpoint", rng: np.random.Generator | None = None):
        if not isinstance(experiment, Experiment):
            raise ValueError("Se asteapta un obiect Experiment.")
        if mode not in ("memory", "checkpoint", "disk"):
            raise ValueError("Mod necunoscut; foloseste memory, checkpoint sau disk.")
        if mode == "disk" and not isinstance(automaton, Automaton):
            raise ValueError("Modul disk necesita un obiect Automaton.")
        if rng is not None and not isinstance(rng, np.random.Generator):
            raise ValueError("rng trebuie sa fie un generator NumPy.")
        self.experiment = experiment
        self.automaton = replace(automaton, experiment=experiment) if isinstance(automaton, Automaton) else automaton
        self.mode = mode
        self.rng = rng
        self._entries = {}
        self._first = None
        self._last = None

    def add(self, state: State) -> None:
        if not isinstance(state, State) or type(state.generation) is not int or state.generation < 0:
            raise ValueError("Se asteapta un State cu generatia intreaga nenegativa.")
        generation = state.generation
        if self._last is not None and generation <= self._last:
            raise ValueError("Generatiile trebuie adaugate in ordine strict crescatoare.")
        grid = state.grid
        if (not isinstance(grid, np.ndarray) or grid.ndim not in (1, 2) or not grid.size
                or grid.dtype.kind not in "iuf" or not np.isfinite(grid).all()):
            raise ValueError("Grila trebuie sa fie un tablou NumPy numeric finit, 1D sau 2D.")
        if self.mode == "disk":
            path = self.experiment.output_dir / f"generation-{generation:010d}.npz"
            entry = save_state(state, self.automaton, path, rng=self.rng)
        else:
            entry = State(grid.copy(), generation)
        previous = self._last
        permanent = (self.experiment.save_intermediate and
                     (self.mode == "memory" or previous is not None and
                      previous % self.experiment.checkpoint_interval == 0))
        if previous is not None and previous != self._first and not permanent:
            old = self._entries[previous]
            if isinstance(old, Path):
                try:
                    old.unlink()
                except OSError:
                    try:
                        entry.unlink()
                    finally:
                        raise ValueError(f"Generatia {previous} nu poate fi eliminata de pe disc.") from None
            del self._entries[previous]
        self._entries[generation] = entry
        if self._first is None:
            self._first = generation
        self._last = generation

    def get(self, t: int) -> State:
        if type(t) is not int or t < 0:
            raise ValueError("Generatia ceruta trebuie sa fie un intreg nenegativ.")
        if t not in self._entries:
            raise KeyError(f"Generatia {t} nu este pastrata.")
        entry = self._entries[t]
        if isinstance(entry, Path):
            return load_state(entry, self.automaton)
        return State(entry.grid.copy(), entry.generation)

    def count(self) -> int:
        return len(self._entries)

    def last(self) -> State | None:
        return None if self._last is None else self.get(self._last)
