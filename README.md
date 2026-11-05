# CelLab

Simulator de automate celulare. Automatul se descrie intr-un fisier JSON, iar motorul il ruleaza.
Proiect la Inteligenta Artificiala, anul 3, semestrul 1.

Echipa: Ayletheris, Dragos56, denys123456

## Foldere

| Folder | Ce contine |
|---|---|
| `cellab/core/` | motorul: grila, vecinatate, reguli, pasul de simulare |
| `cellab/io/` | citirea descrierii JSON, salvarea si restaurarea starii |
| `cellab/questions/` | raspunsurile la cele 5 intrebari (stare dupa N, stabil, configuratie, numar celule, ciclu) |
| `cellab/nl/` | parserul de limbaj natural (Livrabil 4) |
| `cellab/ml/` | dataset si experimentul NN/RL (Livrabil 3) |
| `cellab/gui/` | interfata grafica |
| `cellab/cli/` | rulare din linia de comanda |
| `automata/examples/` | descrieri de automate (Life, Brian's Brain, Rule 30...) |
| `schemas/` | schema JSON a unui automat |
| `data/datasets/` | seturi de date generate (nu se pun in git) |
| `tests/` | teste, aceeasi structura ca `cellab/` |
| `docs/design/` | decizii si note de proiectare |
| `docs/ai-logs/` | conversatiile cu AI-ul (se cer la predare) |
| `scripts/` | scripturi ajutatoare |

## Instalare

```
python -m venv .venv
.venv\Scripts\activate
pip install -e .
pip install pytest
```

## Folosire

Încărcare din fișier sau text JSON:

```python
from cellab.core.step import step
from cellab.io import load_automaton, load_initial_state

automaton = load_automaton("automata/examples/life.json")
state = step(automaton, load_initial_state(automaton))
```

`load_automaton_from_text(text)` întoarce același tip de obiect. Ambele funcții
ridică `ValueError` cu un mesaj scurt pentru intrări invalide. Formatul și
valorile implicite sunt în [docs/design/format.md](docs/design/format.md).

`from cellab.io import validate` permite verificarea unui `Automaton` sau a
unui dicționar JSON. `validate(automaton)` întoarce toate problemele într-o
listă de mesaje `Eroare:` / `Avertisment:`; pentru o descriere completă și
corectă întoarce `[]`. Valorile implicite sunt 50×50, margine wrap și Moore
cu raza 1; folosirea lor este raportată prin avertismente.

`load_initial_state(automaton, source)` acceptă o matrice, text cu `.` / `#`
sau un `Path`. Fără `source`, folosește `automaton.init`. Pentru o cale ca
text există `load_initial_state_from_file(automaton, cale)`. Rezultatul este
un `State` la generația 0, cu dimensiunile și stările verificate.
Exemplele sunt în [docs/design/initial-state.md](docs/design/initial-state.md).

`init` poate descrie și o stare generată: random cu procente și seed, o celulă
centrală, un tipar plasat la coordonate sau o grilă goală. Se folosește același
`load_initial_state(automaton)`; pentru apel direct există
`generate_initial_state(automaton, spec)`. Vezi
[docs/design/generated-state.md](docs/design/generated-state.md) și exemplele
`life_random.json`, `rule30_center.json`, `life_glider.json`, `life_empty.json`.

`automaton.experiment` este un `Experiment`, cu valori implicite `N=100`,
`seed=0`, `save_intermediate=True`, `checkpoint_interval=10`, `output_dir="saves"`.
Configurația poate veni din câmpul JSON `experiment`, din cod sau din CLI;
valorile explicite suprascriu fișierul. Exemplu:

```powershell
python -m cellab.cli automata/examples/life_random.json --generations 200 --seed 7 --no-save-intermediate
```

Comanda afișează configurația rezolvată. API-ul pentru Rulare și exemplele
sunt în [docs/design/experiment.md](docs/design/experiment.md).

`save_state(state, automaton, cale, overwrite=False)`, din `cellab.io`,
salvează grila comprimată și metadatele JSON într-un singur fișier `.npz`.
Creează folderele lipsă și refuză suprascrierea implicit. Formatul și exemplul
de citire cu NumPy sunt în [docs/design/saved-state.md](docs/design/saved-state.md).

`apply_rules(grid, rules, kernel, boundary="fixed")` aplică regulile în ordine,
pe grila veche. O regulă fără `condition` și fără `counts` este ramura „altfel”;
fără nicio potrivire, celula își păstrează starea. Formatul vechi cu `neighbor_state` și
`counts` rămâne disponibil.

Exemplu de regulă Voter: `{"condition": {"more_than": [1, 0]}, "next_state": 1}`.
În `condition` se pot folosi `all` / `any` cu liste de condiții, ori o
numărătoare ca `{"neighbor_state": 1, "at_least": 2}`. Sunt acceptate și
`at_most`, `exact` și `between: [min, max]` (capete incluse).

Pentru Cyclic cu trei stări:

```json
{"condition": {"neighbor_state": {"next_mod": 3}, "at_least": 2}, "next_state": {"next_mod": 3}}
```

Expresia `next_mod` înseamnă
`(starea_curentă + 1) % k` și poate apărea atât la starea vecinilor, cât și la
starea următoare. Stările Cyclic sunt întregi de la `0` la `k - 1`.
