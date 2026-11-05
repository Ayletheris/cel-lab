# Viteza simularii

Masurat cu `scripts/measure_speed.py`, pe PC-ul lui Robert (Windows, Python 3.11.4, numpy 2.4.6).
Toate prin `step()`, fara bucle pe celule (totul e calculat pe toata matricea deodata).

| Automat | Marime | Generatii | Timp |
|---|---|---|---|
| Game of Life | 100x100 | 100 | 0.05 s |
| Game of Life | 500x500 | 100 | 1.15 s |
| Difuzie | 500x500 | 100 | 0.71 s |
| Rule 30 | 10000 celule | 1000 | 0.21 s |

Tinta din cardul Motor 11 (500x500, 100 generatii in cateva secunde) e atinsa: 1.15 s.
Nu a fost nevoie de optimizari.

Cum rulezi singur:

```
.venv\Scripts\python scripts/measure_speed.py
```

Timpii depind de calculator. Daca iese mult mai lent, anunta echipa.
