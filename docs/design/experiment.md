# Parametrii experimentului

`Experiment` este disponibil din `cellab.core.experiment` și
`cellab.core.model`. Fiecare `Automaton` are un `experiment` de acest tip,
inclusiv dacă fișierul nu declară parametrii. Clasa este o dataclass
imuabilă; valori greșite produc `ValueError` cu mesaje scurte în română.

| Parametru | Semnificație | Implicit |
|---|---|---|
| `N` | Numărul de generații, întreg pozitiv | `100` |
| `seed` | Seedul experimentului, întreg nenegativ | `0` |
| `save_intermediate` | Salvează generațiile intermediare, boolean | `true` |
| `checkpoint_interval` | Intervalul între checkpointuri, întreg ≥ 1 | `10` |
| `output_dir` | Folderul de ieșire, cale nevidă | `"saves"` |

`output_dir` este normalizat la `pathlib.Path` în obiect. O cale relativă
se raportează la directorul curent. Crearea configurației nu creează foldere.
`save_intermediate` și `checkpoint_interval` sunt parametri distincți:
primul controlează generațiile intermediare, al doilea frecvența checkpointurilor.
Rulare poate folosi intervalul pentru generațiile `k`, `2k`, `3k`, unde
`k = checkpoint_interval`.

## Din cod

```python
from cellab.core.experiment import Experiment

experiment = Experiment(N=200, seed=7, checkpoint_interval=20, output_dir="results")
```

Valorile nespecificate se completează cu cele implicite. `N`, `seed` și
intervalul nu acceptă booleeni sau șiruri numerice; `save_intermediate`
acceptă exclusiv `True` / `False`.

## Din JSON

Câmpul opțional `experiment` este la același nivel cu `grid`, `rules` și `init`:

```json
{
  "N": 100,
  "seed": 42,
  "save_intermediate": true,
  "checkpoint_interval": 10,
  "output_dir": "saves/life-random"
}
```

Fragmentul de mai sus este valoarea câmpului `experiment`. Exemplul complet
este [life_random.json](../../automata/examples/life_random.json).
Se pot omite câmpuri sau tot obiectul. `null`, câmpurile necunoscute și
valorile invalide sunt respinse. `validate(automaton)` adună și problemele
experimentului, fără să se oprească la prima.

```python
from cellab.io import load_automaton

automaton = load_automaton("automata/examples/life_random.json")
experiment = automaton.experiment
```

## Prioritatea surselor

Valorile explicite date din cod sau CLI au prioritate față de fișier, iar
fișierul are prioritate față de valorile implicite. Combinarea se face înainte
de validarea valorilor rezultate. Inclusiv `False` și seedul `0` suprascriu
fișierul; un parametru explicit `None` este invalid.

```python
automaton = load_automaton(
    "automata/examples/life_random.json",
    experiment_overrides={"N": 25, "seed": 0, "save_intermediate": False},
)
```

Același argument este disponibil la `load_automaton_from_text`.
Pentru configurare independentă:

```python
experiment = Experiment.from_sources({"N": 200, "seed": 42}, N=25)
experiment = Experiment.from_sources(experiment, save_intermediate=False)
```

`from_sources` acceptă un dicționar, un `Experiment` sau `None` și nu modifică
sursa. Pentru a schimba ulterior parametrii, se construiește un obiect nou.

## Din linia de comandă

```powershell
python -m cellab.cli automata/examples/life_random.json --generations 200 --seed 7 --no-save-intermediate --checkpoint-interval 20 --output-dir results
```

Comanda încarcă automatul și afișează configurația finală ca JSON.
`--save-intermediate` activează salvarea, `--no-save-intermediate` o dezactivează.
Argumentele omise păstrează valorile din fișier. Valorile greșite sunt
afișate fără traceback, cu cod de ieșire 2.

## Folosire directă de Rulare și automate

```python
import numpy as np
from cellab.cli import load_run_configuration

automaton = load_run_configuration()
experiment = automaton.experiment
rng = np.random.default_rng(experiment.seed)
for generation in range(1, experiment.N + 1):
    checkpoint = generation % experiment.checkpoint_interval == 0
```

`load_run_configuration(argv=None)` combină calea JSON cu opțiunile CLI și
întoarce `Automaton`. `parse_experiment_args(argv=None, config=None)` întoarce
direct un `Experiment`. Un parser existent poate reutiliza
`add_experiment_arguments(parser)` și apoi `Experiment.from_sources`.

`experiment.seed` configurează generatorul pentru rulare. `init.seed` rămâne
seedul separat al generării stării inițiale, conform cardului anterior;
opțiunea CLI `--seed` suprascrie `experiment.seed` din fișier.
