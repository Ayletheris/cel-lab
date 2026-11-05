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
