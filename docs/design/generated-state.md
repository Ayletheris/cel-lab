# Stare inițială generată după reguli

`init` poate fi o matrice explicită sau un obiect cu un câmp `type`:
`random`, `center`, `pattern`, `empty`. Formele vechi rămân valabile.
Obiectele de generare nu acceptă câmpuri suplimentare.

```python
from cellab.io import load_automaton, load_initial_state

automaton = load_automaton("automata/examples/life_random.json")
state = load_initial_state(automaton)
```

Rezultatul este un `State` la generația 0, cu matrice NumPy independentă.
Încărcătorul păstrează obiectul `init` în `Automaton` și îl verifică fără
să genereze întreaga grilă. Generarea are loc la `load_initial_state` sau
la apelul direct `generate_initial_state(automaton, spec)`.
`validate(automaton)` raportează și erorile configurației de generare.

## Random cu procente

```json
{"type": "random", "percentages": {"1": 30}, "seed": 42}
```

Cheile din `percentages` sunt valorile stărilor declarate, scrise ca șiruri
JSON canonice: `"0"`, `"1"`, `"-2"`. Valorile sunt procente între 0 și 100,
inclusiv fracții. Cu `states: [0, 1]`, exemplul înseamnă 30% șanse pentru 1
și 70% pentru 0, independent pentru fiecare celulă. Frecvența obținută este
aproximativă; nu se impune un număr exact de celule vii.

Dacă suma este sub 100%, diferența se adaugă **primei stări din `states`**,
chiar dacă aceasta are deja un procent explicit. Stările omise au inițial
0%. De exemplu, la `states: [0, 1, 2]`, procentele `{"0": 10, "1": 20}`
devin 80%, 20%, 0%. Un obiect gol înseamnă 100% pentru prima stare.
Suma peste 100% produce eroare; se tolerează doar o abatere de rotunjire de
cel mult `1e-9` puncte procentuale. Nu se renormalizează procentele greșite.

`seed` este un întreg nenegativ, implicit `0`. Se folosește un generator
local NumPy `Generator(PCG64(seed))`, fără modificarea generatorului global.
Aceeași configurație, ordine a stărilor, dimensiune și versiune NumPy produce
aceeași matrice. Ordinea cheilor din `percentages` nu influențează rezultatul.
Random necesită stări discrete; domeniul continuu `["number"]` nu este acceptat.

Exemplu complet: [life_random.json](../../automata/examples/life_random.json),
grilă 100×100, probabilitate de 30% pentru celule vii.

## O celulă în centru

```json
{"type": "center", "state": 1}
```

Se umple grila cu `background`, implicit prima stare declarată, apoi se pune
`state` în poziția `x = width // 2`, `y = height // 2`. Pentru dimensiuni pare
se alege celula din dreapta/jos dintre pozițiile centrale. Pentru Rule 30,
grila are un singur rând, deci `y = 0`.

`state` este implicit a doua stare declarată sau prima dacă există numai una.
Pentru domeniul numeric continuu, valorile implicite sunt `background: 0`
și `state: 1`; sunt acceptate și valori finite fracționare.

Exemplu complet: [rule30_center.json](../../automata/examples/rule30_center.json).

## Tipar plasat la coordonate

```json
{
  "type": "pattern",
  "pattern": [[0, 1, 0], [0, 0, 1], [1, 1, 1]],
  "position": {"x": 2, "y": 3},
  "background": 0
}
```

`pattern` este o matrice nevidă de stări declarate sau text cu `.` = 0 și
`#` = 1, de exemplu `".#.\n..#\n###"`. Spațiile și liniile goale din text
sunt ignorate. `position` este obligatoriu: coordonatele întregi nenegative
ale colțului din stânga sus, numerotate de la 0. `x` este coloana, `y` rândul.
Toată matricea tiparului, inclusiv zerourile, înlocuiește zona aleasă.

Tiparul trebuie să încapă integral, inclusiv la margine `wrap`; nu se taie
și nu se înfășoară la plasare. Restul grilei primește `background`, implicit
prima stare declarată, respectiv 0 pentru domeniul continuu.

Exemplu complet: [life_glider.json](../../automata/examples/life_glider.json).

## Grilă goală

```json
{"type": "empty"}
```

Toate celulele primesc `background`, implicit prima stare declarată sau 0
pentru domeniul continuu. Se poate indica explicit o altă stare de fundal.

Exemplu complet: [life_empty.json](../../automata/examples/life_empty.json).

Procentele, seedul, coordonatele, dimensiunile tiparului și stările sunt
verificate cu mesaje `ValueError` scurte în română. Schema JSON verifică
structura; relațiile cu dimensiunile grilei și stările declarate, precum și
suma procentelor sunt verificate de încărcător și de `validate`.
