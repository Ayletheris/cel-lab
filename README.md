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

De completat.
