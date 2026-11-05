# Formatul JSON al unui automat — versiunea 1

Acesta este contractul pentru fișierele de automate și pentru ieșirea parserului
de limbaj natural (Livrabil 4). Schema este în
[`schemas/automaton.schema.json`](../../schemas/automaton.schema.json), în dialectul
JSON Schema 2020-12. Câmpurile de mai jos, exceptând `experiment`, sunt obligatorii în forma
completă validată de schemă. Încărcătorul completează câmpurile absente conform
secțiunii de mai jos. Nu se acceptă câmpuri suplimentare sau aliasuri.

| Câmp | Semnificație |
|---|---|
| `version` | Întregul `1`. O schimbare incompatibilă cere o versiune nouă. |
| `grid` | `width`, `height`: întregi pozitivi; `boundary`: `fixed` sau `wrap`. |
| `states` | Lista valorilor întregi distincte pentru un automat discret; exact `["number"]` pentru un domeniu numeric continuu. |
| `neighborhood` | `type`: `moore` sau `von_neumann`; `radius`: întreg pozitiv. |
| `rules` | Listă nevidă de reguli de același tip: `count`, `table` sau `numeric`. |
| `init` | Matrice completă sau obiect de generare: `random`, `center`, `pattern`, `empty`. |
| `experiment` | Opțional: `N`, `seed`, `save_intermediate`, `checkpoint_interval`, `output_dir`. |

## Grila și vecinătatea

`init[y][x]` este celula din coloana `x`, rândul `y`. Originea este în stânga
sus; `x` crește spre dreapta, `y` în jos. Generația inițială este 0.
Toate celulele se actualizează simultan folosind exclusiv generația precedentă.

`fixed` înseamnă că orice poziție din afara grilei are valoarea 0; celulele de
pe contur se actualizează normal. `wrap` înseamnă revenire pe partea opusă,
separat pe fiecare axă.

Moore include offseturile cu `max(abs(dx), abs(dy)) <= radius`, iar von Neumann
pe cele cu `abs(dx) + abs(dy) <= radius`. Centrul este exclus. La o grilă cu un
singur rând, vecinătatea este 1D: doar offseturile orizontale sunt folosite.
La `wrap`, fiecare offset se numără separat, chiar dacă mai multe offseturi
ajung în aceeași celulă. Pentru raza 1 sunt 8 vecini Moore, 4 von Neumann,
respectiv 2 vecini într-o grilă 1D.

## Reguli pe numărători

`from` este starea celulei, `count` este starea vecinilor numărați, iar `in`
este lista numerelor de vecini acceptate. Rezultatul este `to` când numărul
aparține listei, respectiv `otherwise` în caz contrar. Cele trei câmpuri
`count`, `in`, `otherwise` apar împreună sau lipsesc toate; când lipsesc,
tranziția `from` → `to` este necondiționată.

Regulile se parcurg în ordinea listei. Prima cu `from` egal cu starea curentă
decide rezultatul, inclusiv ramura `otherwise`; nu se continuă cu următoarea.
Dacă nu există o astfel de regulă, starea rămâne aceeași.

### Game of Life

0 = mort, 1 = viu. O celulă vie supraviețuiește cu 2 sau 3 vecini vii;
o celulă moartă se naște cu exact 3. Configurația este un oscilator de perioadă 2.

```json
{
  "version": 1,
  "grid": {"width": 5, "height": 5, "boundary": "fixed"},
  "states": [0, 1],
  "neighborhood": {"type": "moore", "radius": 1},
  "rules": [
    {"type": "count", "from": 1, "count": 1, "in": [2, 3], "to": 1, "otherwise": 0},
    {"type": "count", "from": 0, "count": 1, "in": [3], "to": 1, "otherwise": 0}
  ],
  "init": [
    [0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0],
    [0, 1, 1, 1, 0],
    [0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0]
  ]
}
```

### Brian's Brain

0 = inactiv, 1 = activ, 2 = refractar. Numai vecinii activi se numără.
Un inactiv devine activ cu exact 2 vecini activi; un activ devine refractar,
iar un refractar devine inactiv.

```json
{
  "version": 1,
  "grid": {"width": 3, "height": 3, "boundary": "fixed"},
  "states": [0, 1, 2],
  "neighborhood": {"type": "moore", "radius": 1},
  "rules": [
    {"type": "count", "from": 0, "count": 1, "in": [2], "to": 1, "otherwise": 0},
    {"type": "count", "from": 1, "to": 2},
    {"type": "count", "from": 2, "to": 0}
  ],
  "init": [[0, 0, 0], [1, 1, 0], [0, 0, 0]]
}
```

## Reguli pe tabel — Rule 30

Există exact o regulă `table`, cu toate cele 8 tipare binare. Cheia conține
stânga, centrul, dreapta, în această ordine; valoarea este noul centru.
Grila are obligatoriu `height: 1`, stările `[0, 1]`, vecinătatea Moore de rază 1.
Rândurile succesive dintr-o vizualizare sunt generații, nu rânduri ale grilei.

```json
{
  "version": 1,
  "grid": {"width": 7, "height": 1, "boundary": "fixed"},
  "states": [0, 1],
  "neighborhood": {"type": "moore", "radius": 1},
  "rules": [{
    "type": "table",
    "table": {"111": 0, "110": 0, "101": 0, "100": 1, "011": 1, "010": 1, "001": 1, "000": 0}
  }],
  "init": [[0, 0, 0, 1, 0, 0, 0]]
}
```

## Reguli numerice — difuzie

Există exact o regulă `numeric`, iar `states` este `["number"]`: fiecare celulă
poate conține orice număr finit. Raza este 1. Expresia folosește `celula` și
direcțiile `nord`, `sud`, `est`, `vest`, `nord_est`, `nord_vest`, `sud_est`,
`sud_vest`, numai dacă direcția aparține vecinătății declarate. Pe o grilă 1D
sunt disponibile doar `est` și `vest`.

Gramatica permisă: literali numerici zecimali (inclusiv notație exponențială),
paranteze, minus unar, operațiile `+`, `-`, `*`, `/`, comparațiile
`<`, `<=`, `>`, `>=`, `==`, `!=` și apeluri `suma`, `media`, `min`, `max`
cu cel puțin un argument pozițional. Comparațiile produc 0 sau 1; comparațiile
înlănțuite sunt interzise. Precedența este cea obișnuită: apeluri, minus unar,
înmulțire/împărțire, adunare/scădere, comparații. Nu se execută cod arbitrar.
Împărțirea la zero și rezultatele nefinite opresc pasul cu eroare.

În exemplu, fiecare valoare nouă este media dintre celulă și cei patru vecini.
După un pas, centrul și cei patru vecini ai săi au valoarea 0.2, colțurile 0.

```json
{
  "version": 1,
  "grid": {"width": 3, "height": 3, "boundary": "fixed"},
  "states": ["number"],
  "neighborhood": {"type": "von_neumann", "radius": 1},
  "rules": [{"type": "numeric", "expression": "media(celula, nord, sud, est, vest)"}],
  "init": [[0, 0, 0], [0, 1, 0], [0, 0, 0]]
}
```

## Validare și integrare

Schema verifică structura, tipurile și combinațiile celor trei familii.
Încărcătorul trebuie să verifice suplimentar, înainte de simulare:

- Dimensiunile exacte ale matricei `init` și absența valorilor nefinite.
- Apartenența valorilor inițiale și a câmpurilor `from`, `count`, `to`,
  `otherwise` la `states`, pentru automate discrete. La `fixed`, 0 trebuie
  să aparțină listei de stări.
- Fiecare valoare din `in` este cel mult numărul de offseturi ale vecinătății.
- Gramatica expresiei numerice și disponibilitatea direcțiilor folosite.
- Respingerea cheilor JSON duplicate, fără conversii automate între tipuri.

JSON Schema standard nu poate compara dimensiuni sau referințe de stări
între câmpuri; trecerea validării structurale nu înlocuiește aceste verificări.
Erorile trebuie să indice câmpul și cauza, fără corectare tacită.

Motorul existent are un API intern diferit. Încărcătorul va converti `wrap`
în `toroidal`, `grid` în `grid_size: [height, width]` și va construi kernelul
din `neighborhood`. O regulă condiționată se traduce într-o regulă internă cu
`state`, `neighbor_state`, `counts`, `next_state`, urmată de o ramură
necondiționată pentru același `state`, cu rezultatul `otherwise`. Perechile
rămân în ordinea din JSON. Pentru tabel se transmite `table` către
`apply_table`, pentru numeric se transmite `expression` către `apply_numeric`.
Regulile interne nu sunt formatul de ieșire al parserului de limbaj natural.
Pentru a respecta prioritatea primei reguli `from`, încărcătorul ignoră la
conversie regulile ulterioare cu același `from`, după validarea lor.
Kernelul este construit de motor la simulare; pe o singură linie folosește
numai offseturile orizontale.

## Încărcarea din fișier sau text

```python
from cellab.io import load_automaton, load_automaton_from_text

automaton = load_automaton("automata/examples/life.json")
automaton = load_automaton_from_text('{"rules": [{"type": "count", "from": 0, "to": 1}]}')
```

Ambele funcții întorc un `Automaton` compatibil cu `step`. `init` păstrează
matricea sau obiectul de generare; simularea începe cu
`load_initial_state(automaton)`, importată din `cellab.io`.
Fișierele sunt citite în UTF-8, cu sau fără BOM. Erorile de citire, sintaxă
sau descriere sunt `ValueError`, cu mesaje scurte în română. Apelantul poate
afișa `str(error)` fără traceback. Pentru JSON invalid se indică linia și coloana.

Valorile implicite se aplică numai câmpurilor absente, nu celor cu `null`:

| Câmp absent | Valoare implicită |
|---|---|
| `version` | `1` |
| `grid.width`, `grid.height` | `50`, respectiv `50` |
| `grid.boundary` | `"wrap"` |
| `states` | `[0, 1]` |
| `neighborhood.type` | `"moore"` |
| `neighborhood.radius` | `1` |
| `init` | Matrice de zerouri cu dimensiunile grilei |

`grid` și `neighborhood` pot lipsi integral sau parțial. `rules` este
obligatoriu și nevid; încărcătorul nu inventează comportamentul automatului.
Regulile numerice trebuie să declare explicit `states: ["number"]`, iar cele
de tabel trebuie să declare `grid.height: 1`.
Valorile implicite sunt centralizate în `cellab/io/defaults.py`, conform
cardului „Validarea descrierii”. Fișierele complete păstrează propriile valori.

## Validarea descrierii

```python
from cellab.io import load_automaton, validate

probleme = validate(load_automaton("automata/examples/life.json"))
```

`validate(automaton)` întoarce o listă de texte în română. Un automat complet
și corect întoarce `[]`. Mesajele încep cu `Eroare:` sau `Avertisment:`.
Funcția adună problemele și nu modifică obiectul primit. Acceptă atât
`Automaton`, cât și un dicționar în formatul JSON, înainte de încărcare.

Erorile includ stări nedeclarate în reguli și condiții, dimensiuni nepozitive,
vecinătăți necunoscute și probabilități `prob` în afara intervalului închis
`[0, 1]`. `prob` este un parametru al regulilor interne ale motorului;
validatorul nu extinde schema JSON v1 pentru a-l accepta în fișiere.

Două reguli se contrazic dacă au aceeași stare sursă și aceeași condiție, dar
rezultate diferite, inclusiv rezultate `otherwise` diferite. Ordinea cheilor,
a numărătorilor și a termenilor `all`/`any` nu contează la comparare. Nu se
încearcă demonstrarea echivalenței dintre condiții scrise în forme diferite.
Ramura necondiționată de rezervă și o regulă condiționată nu sunt un conflict.
Încărcătorul respinge contradicțiile înainte să elimine regulile umbrite.

O stare fără nicio regulă sursă produce avertismentul că va rămâne la fel.
Regulile interne fără stare sursă se aplică tuturor stărilor. Regulile
numerice și tabelul binar sunt tratate separat, fără avertismente false
pentru exemplele complete.

Parametrii absenți sunt raportați cu valoarea implicită folosită. Încărcătorul
păstrează numele câmpurilor completate în `Automaton.defaults_used`, astfel
încât avertismentele rămân disponibile după încărcare. Pentru un `Automaton`
construit manual, `None` la dimensiuni, margine sau vecinătate indică un
parametru lipsă; validatorul raportează valoarea implicită, fără să o scrie
în obiect. Încărcătorul rămâne strict și respinge `null` în fișier.

## Stabilitate și acordul echipei

Cardul „Parametrii experimentului” adaugă obiectul opțional `experiment`.
Lipsa lui păstrează compatibilitatea exemplelor existente. Contractul și
prioritatea surselor sunt în [experiment.md](experiment.md).

Cardul „Stare inițială generată după reguli” adaugă în versiunea 1 obiectele
de generare pentru `init`, fără să schimbe forma sau sensul matricelor
existente. Structura este în schema formală, iar semantica și exemplele sunt
în [generated-state.md](generated-state.md). Parserul NL produce aceeași
structură, fără aliasuri sau instrucțiuni de executat ca text.

Versiunea 1 fixează numele, tipurile și semantica de mai sus. Parserul NL
trebuie să producă exact acest contract și să semnaleze cererile care nu pot
fi reprezentate; nu adaugă câmpuri proprii. Extensiile incompatibile se fac
într-o schemă cu versiune nouă, păstrând citirea versiunii 1.

Notițele originale nu sunt prezente în repository; exemplul Life păstrează
câmpurile `from`, `count`, `in`, `to`, `otherwise` indicate în cerință.
Citirea și acordul celor doi colegi sunt încă neconfirmate. Fiecare trebuie
să confirme aici numele, data și acordul înainte ca livrabilul să fie declarat
acceptat de echipă.
