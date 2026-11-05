import json

import numpy as np

from cellab.io.load import _constant, _pairs


BIT_GENERATORS = {cls.__name__: cls for cls in (
    np.random.PCG64, np.random.PCG64DXSM, np.random.MT19937, np.random.Philox, np.random.SFC64,
)}


def _encode_rng(rng):
    if not isinstance(rng, np.random.Generator):
        raise ValueError("rng trebuie sa fie un generator NumPy.")
    if type(rng.bit_generator).__name__ not in BIT_GENERATORS:
        raise ValueError("Tipul generatorului RNG nu este suportat.")

    def encode(value):
        if isinstance(value, np.ndarray):
            return value.tolist()
        if isinstance(value, np.generic):
            return value.item()
        raise TypeError("Valoare RNG neserializabila.")

    return json.dumps(rng.bit_generator.state, default=encode, allow_nan=False)


def _restore_rng(encoded, rng):
    if encoded is None:
        if rng is not None:
            raise ValueError("Fisierul nu contine starea RNG; restaurarea exacta nu este posibila.")
        return
    if encoded.shape != () or encoded.dtype.kind != "U":
        raise ValueError("Starea RNG trebuie sa fie un sir JSON scalar.")
    try:
        snapshot = json.loads(encoded.item(), object_pairs_hook=_pairs, parse_constant=_constant)
        name = snapshot.get("bit_generator") if isinstance(snapshot, dict) else None
        if not isinstance(name, str) or name not in BIT_GENERATORS:
            raise ValueError("Tip RNG necunoscut.")
        probe = BIT_GENERATORS[name](0)
        probe.state = snapshot
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, OverflowError, RecursionError):
        raise ValueError("Starea RNG din fisier este invalida sau tipul nu este suportat.") from None
    if rng is not None:
        if type(rng.bit_generator).__name__ != name:
            raise ValueError(f"Generatorul RNG dat nu coincide cu cel salvat ({name}).")
        rng.bit_generator.state = probe.state
