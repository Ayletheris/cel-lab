# Rularea unui experiment

```python
from cellab.core.experiment import Experiment
from cellab.core.run import run
from cellab.io import load_automaton, load_initial_state

automaton = load_automaton("automata/examples/life_glider.json")
experiment = Experiment(N=20, checkpoint_interval=1)
result = run(automaton, load_initial_state(automaton), experiment)

assert result.final_state.generation == 20
assert result.generations.count() == 21  # inclusiv generatia initiala
```

`run` apeleaza `step` de `N` ori si adauga fiecare stare in `GenerationStore`.
Rezultatul contine `final_state`, `generations`, `steps` si `duration` in secunde.
Store-ul pastreaza generatiile conform parametrilor `Experiment`; de exemplu,
cu `checkpoint_interval=5` se pot citi generatiile 0, 5, 10, 15 si 20.

Daca starea primita este restaurata la generatia 7, `N=5` produce generatia 12.
Pentru reguli probabilistice, `run` creeaza un generator din `experiment.seed`.
La reluarea unei rulari probabilistice, generatorul restaurat prin
`load_state(path, automaton, rng=rng)` se transmite si la `run(..., rng=rng)`.
