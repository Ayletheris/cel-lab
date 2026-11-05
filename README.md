# CelLab

Simulator de automate celulare. Descrii automatul intr-un fisier JSON si programul il ruleaza.
Proiect la Inteligenta Artificiala, anul 3, semestrul 1.

Echipa: Ayletheris, Dragos56, denys123456

## Foldere

| Folder | Ce e in el |
|---|---|
| `cellab/core/` | motorul: grila, vecini, reguli, un pas de simulare |
| `cellab/io/` | citirea fisierului JSON, salvarea si restaurarea starii |
| `cellab/questions/` | raspunsurile la intrebari (stare dupa N, stabil, numar celule, ciclu) |
| `cellab/cli/` | comenzile din terminal |
| `cellab/nl/` | parserul de limbaj natural (Livrabil 4) |
| `cellab/ml/` | dataset si retea neuronala (Livrabil 3) |
| `cellab/gui/` | interfata grafica |
| `automata/examples/` | automate gata facute (Life, Brian's Brain, Rule 30, Forest Fire...) |
| `schemas/` | schema fisierului JSON |
| `data/datasets/` | date generate (nu intra in git) |
| `tests/` | teste |
| `docs/design/` | explicatii despre cum e facut proiectul |
| `docs/ai-logs/` | conversatiile cu AI-ul (se cer la predare) |
| `scripts/` | scripturi ajutatoare |

## Instalare

Prima data (Windows, PowerShell):

```
git clone https://github.com/Ayletheris/cel-lab.git
cd cel-lab
python -m venv .venv
.venv\Scripts\python -m pip install -e . pytest
.venv\Scripts\python -m pytest -q
```

Pe Mac / Linux e la fel, doar ca scrii `.venv/bin/python` in loc de `.venv\Scripts\python`.

Daca vrei sa rulezi doar testele pt citire, stare si salvare:

```
.venv\Scripts\python -m pytest tests/io/ -q
```

## Demo pentru laborator (Livrabil 2)

```
.venv\Scripts\python scripts/demo_l6.py
```

Pentru Game of Life, Brian's Brain si Forest Fire arata:
descrierea din JSON, generatia curenta, generatia noua dupa reguli,
salvarea, restaurarea si continuarea simularii.

## Rulare din terminal

```
.venv\Scripts\python -m cellab.cli run automata/examples/game_of_life.json --generations 20 --seed 1 --show
```

- `--generations N` = cate generatii
- `--seed S` = seed pt partile aleatoare (acelasi seed = acelasi rezultat)
- `--show` = arata generatiile in text (la Rule 30 cate un rand pe generatie)
- `--checkpoint-interval K` = pastreaza si salveaza din K in K generatii (`1` = toate)
- `--no-save-intermediate` = salveaza doar starea finala
- `--output-dir folder` = unde se salveaza (implicit `saves/`)

La final starea se salveaza in `saves/<nume-automat>-gen<N>.npz`. Ca sa continui de acolo:

```
.venv\Scripts\python -m cellab.cli run automata/examples/game_of_life.json --generations 20 --resume saves/game-of-life-gen20.npz
```

Starea finala se salveaza cu tot cu generatorul aleator, deci continuarea iese la fel ca o
rulare fara pauza, chiar si la automatele cu probabilitati. Generatiile intermediare nu au
generatorul, deci la automatele cu probabilitati continuarea de la ele iese diferit.

Daca dai doar fisierul, fara comanda, se afiseaza parametrii experimentului:

```
.venv\Scripts\python -m cellab.cli automata/examples/life_random.json --generations 200 --seed 7 --no-save-intermediate
```

## Alte comenzi

Toate primesc fisierul JSON si optiunile de mai sus.

| Comanda | Ce face |
|---|---|
| `validate fisier.json` | verifica fisierul si arata problemele |
| `state-after fisier.json --generations N` | Q1: starea dupa N generatii |
| `count fisier.json --generations N` | Q4: cate celule din fiecare stare sunt dupa N generatii |
| `stable fisier.json [--max-steps K]` | Q2: de la ce generatie grila nu se mai schimba |
| `cycle fisier.json [--max-steps K]` | Q5: daca intra intr-un ciclu, de unde si cat de lung e |

Exemplu:

```
.venv\Scripts\python -m cellab.cli cycle automata/examples/life.json
```

Q2 si Q5 nu merg la automatele cu probabilitati: acolo daca o grila se repeta nu inseamna
ca de acum se repeta totul.

## Cum adaugi un automat nou

1. Copiezi un fisier din `automata/examples/` (de ex. `game_of_life.json`).
2. Schimbi grila, starile, regulile si `init`. Formatul e explicat in [docs/design/format.md](docs/design/format.md).
3. Verifici: `.venv\Scripts\python -m cellab.cli validate fisierul_tau.json`
4. Rulezi: `.venv\Scripts\python -m cellab.cli run fisierul_tau.json --generations 10 --show`

## Din cod (Python)

Citesti un automat si faci un pas:

```python
from cellab.core.step import step
from cellab.io import load_automaton, load_initial_state

automaton = load_automaton("automata/examples/life.json")
state = step(automaton, load_initial_state(automaton))
```

Pe scurt, ce mai e disponibil:

- `load_automaton_from_text(text)`: la fel ca `load_automaton`, dar din text JSON.
  Daca ceva e gresit, da `ValueError` cu un mesaj scurt.
- `validate(automaton)`: lista cu probleme (`Eroare:` / `Avertisment:`). Lista goala = totul e ok.
  Daca lipsesc valori, se folosesc cele implicite (50x50, margine wrap, Moore cu raza 1)
  si primesti un avertisment.
- `load_initial_state(automaton, source)`: starea de start, dintr-o matrice, din text cu `.` si `#`
  sau dintr-un fisier. Fara `source` foloseste `init` din JSON.
- `init` din JSON poate fi si generat: random cu procente si seed, o celula in centru,
  un tipar pus la o pozitie sau grila goala. Exemple: `life_random.json`, `rule30_center.json`,
  `life_glider.json`, `life_empty.json`.
- `automaton.experiment`: parametrii rularii. Implicit `N=100`, `seed=0`, `save_intermediate=True`,
  `checkpoint_interval=10`, `output_dir="saves"`. Pot veni din JSON, din cod sau din terminal;
  ce dai in terminal bate ce e in fisier.
- `save_state(state, automaton, cale)`: salveaza starea intr-un fisier `.npz`.
  Nu suprascrie un fisier existent decat cu `overwrite=True`.
- `load_state(cale, automaton)`: incarca starea inapoi si verifica sa se potriveasca cu automatul.
- Pt automate cu probabilitati: dai acelasi generator la `step`, la `save_state(..., rng=rng)`
  si la `load_state(..., rng=rng)`, ca sa continue exact la fel.
- `GenerationStore`: tine generatiile (`add`, `get`, `count`, `last`), toate sau din K in K.
- `run(automaton, state, experiment)`: ruleaza N generatii si le pune in `GenerationStore`.

Reguli scrise direct in cod (formatul intern al motorului):

- Voter: `{"condition": {"more_than": [1, 0]}, "next_state": 1}`
- in `condition` merg `all` / `any` cu liste de conditii, sau `{"neighbor_state": 1, "at_least": 2}`;
  mai sunt `at_most`, `exact` si `between: [min, max]` (cu capete incluse)
- Cyclic cu 3 stari:

```json
{"condition": {"neighbor_state": {"next_mod": 3}, "at_least": 2}, "next_state": {"next_mod": 3}}
```

`next_mod` inseamna `(starea_curenta + 1) % k`. Starile la Cyclic sunt de la `0` la `k - 1`.

## Mai multe detalii

In `docs/design/`: `format.md` (fisierul JSON), `initial-state.md`, `generated-state.md`,
`experiment.md`, `saved-state.md`, `generation-store.md`, `run.md`, `viteza.md`.
