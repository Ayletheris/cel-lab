# Stocarea generațiilor intermediare

`GenerationStore` este disponibil din `cellab.io`. Primește parametrii
experimentului și fiecare stare produsă de bucla de simulare.

```python
from cellab.core.experiment import Experiment
from cellab.core.step import step
from cellab.io import GenerationStore, load_automaton, load_initial_state

automaton = load_automaton("automata/examples/life_glider.json")
experiment = Experiment(N=20, checkpoint_interval=5)
store = GenerationStore(experiment)
state = load_initial_state(automaton)
store.add(state)
for _ in range(experiment.N):
    state = step(automaton, state)
    store.add(state)

assert store.count() == 5
assert store.get(10).generation == 10
assert store.last().generation == 20
```

Se păstrează generațiile `0, 5, 10, 15, 20`.

## Moduri și selecție

Constructorul este
`GenerationStore(experiment, automaton=None, mode="checkpoint", rng=None)`.

| Mod | Comportament cu `save_intermediate=True` |
|---|---|
| `memory` | Toate generațiile primite, cu copii ale grilelor în memorie |
| `checkpoint` | Prima, multiplii lui `checkpoint_interval` și cea mai recentă, în memorie |
| `disk` | Aceeași selecție ca `checkpoint`, în fișiere NPZ din `output_dir` |

Cu `checkpoint_interval=1`, modurile `checkpoint` și `disk` păstrează toate
generațiile. Dacă `save_intermediate=False`, toate modurile păstrează numai
prima și cea mai recentă generație. După 20 de pași rămân numai `0` și `20`.

Prima stare trebuie adăugată explicit înaintea buclei. Dacă rularea începe
dintr-un checkpoint, prima generație poate fi diferită de 0: după adăugarea
generațiilor 7–12, la interval 5, se păstrează `7, 10, 12`.

Cea mai recentă generație rămâne disponibilă chiar dacă simularea se oprește
între checkpointuri: după 7 pași, se pot citi `0, 5, 7`. La următoarea stare,
vechea generație recentă este eliminată dacă nu este prima sau un checkpoint.
Store-ul nu are nevoie de un apel de finalizare și nu se oprește automat la `N`.

## Metode

| Metodă | Rezultat |
|---|---|
| `add(state)` | Adaugă starea și aplică selecția; întoarce `None` |
| `get(t)` | Întoarce un `State` independent pentru generația `t` |
| `count()` | Numărul generațiilor păstrate |
| `last()` | Cea mai recentă stare păstrată sau `None` pentru store gol |

Generațiile trebuie să fie întregi nenegative și adăugate în ordine strict
crescătoare. Duplicatele și adăugările înapoi în timp produc `ValueError`.
O generație nepăstrată produce `KeyError` cu mesaj clar. Grilele primite
trebuie să fie tablouri NumPy numerice finite, 1D sau 2D.
Copiile protejează istoricul de modificarea ulterioară a stării originale
sau a rezultatelor `get` / `last`.

## Stocarea pe disc și RNG

```python
import numpy as np

rng = np.random.default_rng(experiment.seed)
store = GenerationStore(experiment, automaton, mode="disk", rng=rng)
```

Modul `disk` necesită automatul pentru metadate și validarea compatibilității.
Parametrii și seedul din fișiere provin din experimentul primit de store,
fără modificarea experimentului automatului original.
Folosește `save_state` / `load_state`; numele fișierelor sunt de forma
`generation-0000000005.npz`. Folderele se creează la prima adăugare.
Grilele nu se păstrează în memorie între apeluri, doar căile către fișiere.

Store-ul elimină numai fișierele generațiilor tranzitorii create de propria
instanță. Fișierele existente nu se suprascriu, iar alte fișiere din folder
nu sunt șterse. Pentru o rulare nouă se alege un folder separat. O instanță
nouă nu indexează automat fișierele unei rulări anterioare.

Dacă este transmis, `rng` trebuie să fie generatorul folosit în bucla
simulării și este salvat în fiecare fișier. `get` și `last` citesc grila fără
să deruleze generatorul simulării înapoi. Pentru reluarea probabilistă din
fișier, se apelează explicit `load_state(cale, automaton, rng=rng)`.
În modurile din memorie se păstrează numai obiectele `State`.
