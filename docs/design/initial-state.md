# Stare inițială explicită

`load_initial_state(automaton, source=None, symbols=None)` întoarce un obiect
`State` la generația 0. Acceptă matrice Python, matrice NumPy 2D, text cu
caractere sau un `pathlib.Path`. Dacă `source` lipsește, folosește
`automaton.init`. Matricea returnată este o copie independentă.

Dimensiunile trebuie să fie exact `automaton.grid_size`, în ordinea
`[height, width]`. Nu se adaugă margini și nu se decupează modelul automat.
Fiecare valoare trebuie să fie numerică, finită și declarată în `states`.
Pentru domeniul `["number"]` sunt permise toate numerele finite, inclusiv
fracții. Valorile booleene și șirurile numerice din matrice sunt respinse.
În domeniul discret, valori ca `1.0` sunt acceptate dacă starea `1` există,
iar matricea rezultat conține întregi. Numerele trebuie să poată fi
reprezentate în tipul numeric NumPy folosit de motor.

## Blinker din text

Legenda implicită este `.` = 0 și `#` = 1. Spațiile, taburile și liniile
goale sunt ignorate. Caracterele necunoscute produc o eroare cu linia și
coloana. Aceste poziții sunt numerotate de la 1.

```python
from cellab.io import load_automaton, load_initial_state

automaton = load_automaton("automata/examples/life.json")
automaton.grid_size = [3, 3]
state = load_initial_state(automaton, ". # .\n. # .\n. # .")
```

Rezultatul este matricea `[[0, 1, 0], [0, 1, 0], [0, 1, 0]]`, un blinker
vertical. Se poate da direct aceeași matrice în locul textului.
La grilă 3×3 cu margine fixă, după un pas blinkerul devine orizontal,
iar după doi pași revine la forma inițială.

## Glider și legendă proprie

```python
automaton.grid_size = [5, 5]
glider = ".#...\n..#..\n###..\n.....\n....."
state = load_initial_state(automaton, glider)
```

După patru pași Life, gliderul s-a deplasat o celulă spre dreapta și în jos.
Pentru alte stări se poate furniza o legendă cu câte un caracter pentru
fiecare simbol folosit:

```python
automaton.grid_size = [1, 3]
automaton.states = [0, 1, 2]
state = load_initial_state(automaton, ".#x", {".": 0, "#": 1, "x": 2})
```

Legenda schimbă numai interpretarea textului. Fiecare valoare folosită
trebuie să fie în continuare o stare declarată.

## Încărcare din fișier

```python
from cellab.io import load_initial_state_from_file

automaton.grid_size = [3, 3]
automaton.states = [0, 1]
state = load_initial_state_from_file(automaton, "blinker.txt")
```

Un fișier `.json` conține exclusiv matricea de numere, de exemplu
`[[0, 1, 0], [0, 1, 0], [0, 1, 0]]`. Celelalte extensii sunt citite ca text
cu caractere. Fișierele sunt UTF-8, cu sau fără BOM. Alternativ, se poate
apela `load_initial_state(automaton, Path("blinker.txt"))`.

Un șir transmis direct la `load_initial_state` este întotdeauna textul
modelului, nu o cale de fișier. Pentru cale se folosește funcția dedicată
sau `Path`, astfel încât interpretarea să nu depindă de fișierele existente.

Toate erorile de intrare sunt `ValueError` cu mesaje scurte în română:
dimensiuni nepotrivite, stare nedeclarată, caracter necunoscut, valoare
nenumerică/nefinită, fișier absent sau imposibil de citit și JSON invalid.
Încărcătorul de automate păstrează contractul JSON v1: `init` rămâne o matrice;
textul și fișierele externe se încarcă prin funcțiile de stare inițială.
