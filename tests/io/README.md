# Testele pentru descriere și stare

Din rădăcina proiectului:

```powershell
python -m pytest tests/io/ -q
```

Comanda verificată pe Windows, cu un singur fir de calcul și un director
temporar dedicat în cache-ul ignorat de Git:

```powershell
$env:OPENBLAS_NUM_THREADS = "1"
$env:OMP_NUM_THREADS = "1"
python -m pytest tests/io/ -q --basetemp .pytest_cache/io-acceptance
```

| Cerință | Teste |
|---|---|
| Salvare/restaurare cu grilă, tip numeric și generație identice | [test_restore.py](test_restore.py), [test_save.py](test_save.py) |
| Automat cu dimensiuni sau stări incompatibile | [test_restore.py](test_restore.py) |
| Fișier lipsă, corupt, versiune sau metadate invalide | [test_load.py](test_load.py), [test_restore.py](test_restore.py) |
| Stări nedeclarate, contradicții, parametri lipsă și alte erori de validare | [test_validate.py](test_validate.py) |
| Random reproductibil, procente aproximative și completarea primei stări | [test_generation.py](test_generation.py) |
| Text cu număr greșit de rânduri, coloane sau linii inegale | [test_initial_state.py](test_initial_state.py) |
| Generațiile exacte păstrate și toate generațiile omise | [test_store.py](test_store.py) |
| Forest Fire: 10 pași comparativ cu 5 + salvare/restaurare + 5 | [test_rng_state.py](test_rng_state.py) |
| Experiment din cod, JSON și CLI, cu prioritatea surselor | [test_experiment.py](test_experiment.py), [test_experiment_cli.py](test_experiment_cli.py) |

Testele folosesc seeduri fixe și foldere temporare. Frecvențele random sunt
comparate cu o toleranță de 2 puncte procentuale pe grile 100×100.
Continuarea probabilistă este verificată și prin checkpointuri produse de
`GenerationStore`, atât pentru grilă, cât și pentru următoarele valori RNG.
Sunt testate `PCG64`, `PCG64DXSM`, `MT19937`, `Philox` și `SFC64`.
