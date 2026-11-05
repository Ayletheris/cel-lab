# Salvarea unei stări

```python
from cellab.io import load_automaton, load_initial_state, save_state

automaton = load_automaton("automata/examples/life.json")
state = load_initial_state(automaton)
path = save_state(state, automaton, "saves/life/generation-0.npz")
```

`save_state(state, automaton, cale, overwrite=False)` întoarce un `Path`.
Creează folderele părinte lipsă. Calea este folosită exact cum a fost dată;
se recomandă extensia `.npz`, fără adăugarea automată a acesteia.

Dacă fișierul există, funcția ridică `FileExistsError`, cu mesajul că trebuie
folosit `overwrite=True`. Nu cere input interactiv. Apelantul poate cere
confirmare utilizatorului și apoi apela explicit:

```python
save_state(state, automaton, path, overwrite=True)
```

Deschiderea exclusivă în modul implicit previne suprascrierea inclusiv dacă
un alt proces creează fișierul înainte de deschidere.

## Conținutul fișierului

Arhiva este produsă cu `np.savez_compressed` și conține exact două câmpuri:

| Câmp | Conținut |
|---|---|
| `grid` | Matricea numerică, cu forma și tipul NumPy originale |
| `metadata` | Șir JSON scalar, fără obiecte Python sau pickle |

Metadatele au structura:

```json
{
  "format_version": 1,
  "generation": 0,
  "automaton_name": "Game of Life",
  "seed": 0,
  "saved_at": "2026-11-05T12:00:00+00:00"
}
```

`generation` vine din `State.generation`, `automaton_name` din `Automaton.name`,
iar `seed` din `Automaton.experiment.seed`. `saved_at` este momentul salvării
în UTC, în format ISO 8601 cu fus orar. `format_version` descrie formatul
arhivei de stare, separat de versiunea descrierii JSON a automatului.

Descrierea automatului poate include câmpul opțional `name`, de exemplu
`"name": "Game of Life"`. În lipsa lui se folosește `"automaton"`.
Seedul păstrat este cel al experimentului, nu seedul separat din `init`.

## Citirea cu NumPy

```python
import json
import numpy as np

with np.load(path, allow_pickle=False) as archive:
    grid = archive["grid"]
    metadata = json.loads(archive["metadata"].item())
```

Grila și metadatele sunt într-un singur fișier, care poate fi copiat sau mutat.
Fișierul nu conține o a doua copie a descrierii complete a automatului.

## Verificări

Generația trebuie să fie un întreg nenegativ, iar `overwrite` un boolean.
Grila trebuie să fie un tablou NumPy de numere reale finite, cu dimensiunile
automatului și valori din stările declarate. Domeniul `["number"]` acceptă
orice număr finit. Pentru un automat cu `grid_size: [1, width]`, se acceptă
și un vector 1D, păstrându-i forma. Numele trebuie să fie nevid, iar
`automaton.experiment` să fie un `Experiment` valid.

Intrările invalide produc `ValueError` înainte de scriere. Erorile de acces
la disc produc un mesaj scurt în română; fișierul existent fără permisiune
de suprascriere produce `FileExistsError`. Salvarea nu modifică starea sau
parametrii automatului.
