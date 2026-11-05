"""Szenario: n Personen, n Aufgaben, Belastung c[i][j] (Mehraufwand von Person i bei Aufgabe j). Alles simuliert.

Die ersten drei Familien und ihre Erzeugung sind aus Stück 1 der Reihe (zielvergleich-demo) übernommen; neu ist „Schwerer Schwanz“."""

from dataclasses import dataclass

import numpy as np

import fpr_constants as C


@dataclass(frozen=True)
class Instance:
    c: tuple[tuple[float, ...], ...]

    @property
    def n(self) -> int:
        return len(self.c)

    def array(self) -> np.ndarray:
        return np.array(self.c, dtype=float)


def make_instance(n: int, family: int, seed: int) -> Instance:
    """Deterministisch aus (n, Familie, Seed): gleiche Eingabe, gleiche Instanz.

    Familie 0: ganze Zahlen 1 bis 9 (viele Gleichstände); 1: gleichverteilt 0 bis 100; 2: Personeneffekt (manche Personen sind
    systematisch teurer, manche Aufgaben ebenso) plus Rauschen; 3: schwerer Schwanz (log-normal, wenige sehr große Belastungen)."""
    rng = np.random.default_rng(seed)
    key = C.FAMILY_KEYS[family]
    if key == "int":
        m = rng.integers(1, 10, size=(n, n)).astype(float)
    elif key == "real":
        m = rng.uniform(0.0, 100.0, size=(n, n))
    elif key == "person":
        person = rng.uniform(0.0, 40.0, size=(n, 1))
        job = rng.uniform(0.0, 20.0, size=(1, n))
        m = person + job + rng.uniform(0.0, 40.0, size=(n, n))
    else:
        m = rng.lognormal(mean=C.LOGNORMAL_MEAN, sigma=C.LOGNORMAL_SIGMA, size=(n, n))
    return Instance(tuple(tuple(float(x) for x in row) for row in m))
