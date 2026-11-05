"""Kern der Demo (numpy, scipy): faire Pläne der Zuordnung gegen das Summen-Optimum. Aus Stück 1 der Reihe (zielvergleich-demo)
übernommen und erweitert um Leximax, den Engpassplan mit zufälligem Gleichstand und die untere Schranke des Maximums.

Die optimale Zuordnung für Summe, Quadratsumme, Maximum und allgemein Summe b^p:

Jede Regel ist eine eigene Funktion mit expliziten Ein- und Ausgaben (DEMO-PLAYBOOK §1b):
`enumerate_optimum` zählt alle n! Pläne auf (n <= ENUM_MAX), `solve_lap` löst Summe b^p exakt über die Ungarische Methode
(scipy), `solve_bottleneck_lex` löst das Maximum exakt über Schwellwertsuche mit Bipartit-Matching und wählt unter allen
Engpass-Optima die kleinste Summe, `check_feasible` ist der unabhängige Zulässigkeitsprüfer.

Gleichstandsregeln (sichtbar, siehe README):
  * Summe und Quadratsumme (Aufzählung): kleinster Plan in der Reihenfolge `itertools.permutations`; (Löser): ein beliebiger gleichwertiger Plan.
  * Maximum: erst kleinstes Maximum, unter allen Plänen mit diesem Maximum die kleinste Summe, dann kleinster Plan (lexikographisch).
  * Maximum mit zufälligem Gleichstand: unter allen Plänen mit dem kleinsten Maximum gewinnt der mit der kleinsten Summe reeller
    Zufallszusatzkosten (fester Seed, deshalb reproduzierbar und unabhängig von der Bibliothek).
  * Leximax: der absteigend sortierte Belastungsvektor wird lexikographisch minimiert; Pläne mit demselben sortierten Vektor haben
    dieselbe Summe, der erste in der Reihenfolge von `itertools.permutations` gilt.

Preis und Gewinn eines fairen Plans gegen das Summen-Optimum stehen in `price` und `gain`.
"""

import itertools
import math
from dataclasses import dataclass
from functools import lru_cache

import numpy as np
from scipy.optimize import linear_sum_assignment
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import maximum_bipartite_matching

import fpr_constants as C
from fpr_scenario import Instance


@dataclass(frozen=True)
class Result:
    plan: tuple[int, ...]          # plan[i] = Aufgabe von Person i
    burdens: tuple[float, ...]     # b_i = c[i][plan[i]]
    total: float                   # Summe der Belastungen
    squares: float                 # Quadratsumme
    peak: float                    # Maximum


def check_feasible(plan, n: int) -> bool:
    """Unabhängiger Prüfer: der Plan ist eine Zuordnung, jede Aufgabe genau einmal."""
    plan = tuple(plan)
    return len(plan) == n and sorted(plan) == list(range(n))


def make_result(c: np.ndarray, plan) -> Result:
    plan = tuple(int(j) for j in plan)
    if not check_feasible(plan, c.shape[0]):
        raise ValueError(f"kein zulässiger Plan: {plan}")
    b = tuple(float(c[i, j]) for i, j in enumerate(plan))
    return Result(plan, b, sum(b), sum(x * x for x in b), max(b))


@lru_cache(maxsize=None)
def all_plans(n: int) -> np.ndarray:
    """Alle n! Pläne als Zeilen (Reihenfolge von itertools.permutations); nur bis n = 9."""
    if not 1 <= n <= 9:
        raise ValueError(f"n = {n}: Aufzählung nur für 1 bis 9 Personen")
    return np.array(list(itertools.permutations(range(n))), dtype=np.int16)


def plan_burdens(c: np.ndarray, plans: np.ndarray) -> np.ndarray:
    """Belastungsvektoren aller Pläne, Form (Zahl der Pläne, n)."""
    n = c.shape[0]
    return c[np.arange(n)[None, :], plans]


def landscape(c: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """(Summe, Maximum) aller Pläne."""
    b = plan_burdens(c, all_plans(c.shape[0]))
    return b.sum(axis=1), b.max(axis=1)


def power_values(b: np.ndarray, p: float) -> np.ndarray:
    """Zielwert je Plan: Summe b^p, für p = unendlich das Maximum."""
    if math.isinf(p):
        return b.max(axis=1)
    return (b ** p).sum(axis=1)


def optimal_set(c: np.ndarray, p: float) -> np.ndarray:
    """Indizes aller Pläne, die das Ziel zum Minimum bringen (Optimalmenge); aufgezählt.

    Für endliches p: relative Toleranz. Für p = unendlich: alle Pläne mit kleinstem Maximum (Optimalmenge VOR der zweiten Regel)."""
    b = plan_burdens(c, all_plans(c.shape[0]))
    v = power_values(b, p)
    if math.isinf(p):
        return np.flatnonzero(v <= v.min() + C.TOL)
    return np.flatnonzero(v <= v.min() * (1.0 + C.REL_TOL) + 0.0)


def enumerate_optimum(c: np.ndarray, p: float) -> Result:
    """Optimaler Plan für Summe b^p (p endlich) oder das Maximum (p = unendlich), aufgezählt, mit der Gleichstandsregel der Demo."""
    plans = all_plans(c.shape[0])
    b = plan_burdens(c, plans)
    idx = optimal_set(c, p)
    if math.isinf(p):
        sums = b[idx].sum(axis=1)
        idx = idx[sums <= sums.min() + C.TOL]
    return make_result(c, plans[int(idx[0])])


def solve_lap(c: np.ndarray, p: float) -> Result:
    """Summe b^p exakt über die lineare Zuordnung mit Kosten c^p (die Zielfunktion ist trennbar); bei Gleichstand ein beliebiger gleichwertiger Plan."""
    if math.isinf(p) or p <= 0:
        raise ValueError("solve_lap braucht ein endliches p > 0")
    rows, cols = linear_sum_assignment(c ** p)
    plan = np.empty(c.shape[0], dtype=int)
    plan[rows] = cols
    return make_result(c, plan)


def bottleneck_value(c: np.ndarray) -> float:
    """Kleinstes Maximum über alle Zuordnungen: kleinste Schwelle t, bei der die Kanten c <= t ein perfektes Matching haben."""
    vals = np.unique(c)
    lo, hi = 0, len(vals) - 1
    best = float(vals[-1])
    while lo <= hi:
        mid = (lo + hi) // 2
        graph = csr_matrix((c <= vals[mid]).astype(np.int8))
        match = maximum_bipartite_matching(graph, perm_type="column")
        if (match >= 0).all():
            best = float(vals[mid])
            hi = mid - 1
        else:
            lo = mid + 1
    return best


def solve_bottleneck_lex(c: np.ndarray) -> Result:
    """Maximum exakt; unter allen Plänen mit diesem Maximum die kleinste Summe (lexikographisch)."""
    t = bottleneck_value(c)
    big = float(c.max()) * c.shape[0] * 10.0 + 1.0
    rows, cols = linear_sum_assignment(np.where(c <= t, c, big))
    plan = np.empty(c.shape[0], dtype=int)
    plan[rows] = cols
    return make_result(c, plan)


def lower_bound(c: np.ndarray) -> float:
    """Untere Schranke des Maximums jedes Plans: die zäheste Person, `max_i min_j c_ij`; ihre Aufgabe kostet mindestens so viel."""
    return float(c.min(axis=1).max())


def solve_bottleneck_random(c: np.ndarray, tie_seed: int) -> Result:
    """Maximum exakt; unter allen Plänen mit diesem Maximum entscheiden reelle Zufallszusatzkosten (Seed `tie_seed`) statt der Summe."""
    t = bottleneck_value(c)
    extra = np.random.default_rng(tie_seed).uniform(0.0, 1.0, size=c.shape)
    rows, cols = linear_sum_assignment(np.where(c <= t, extra, 1e9))     # Summe der Zusatzkosten höchstens n: 1e9 sperrt jede Kante über der Schwelle
    plan = np.empty(c.shape[0], dtype=int)
    plan[rows] = cols
    return make_result(c, plan)


def solve_leximax(c: np.ndarray) -> Result:
    """Leximax, aufgezählt (n <= ENUM_MAX): den absteigend sortierten Belastungsvektor lexikographisch minimieren."""
    n = c.shape[0]
    if n > C.ENUM_MAX:
        raise ValueError(f"Leximax nur bis n = {C.ENUM_MAX} (aufgezählt)")
    plans = all_plans(n)
    ordered = -np.sort(-plan_burdens(c, plans), axis=1)
    order = np.lexsort(ordered.T[::-1])        # letzter Schlüssel zuerst: die größte Belastung entscheidet zuerst
    return make_result(c, plans[int(order[0])])


def price(r: Result, base: Result) -> float:
    """Mehrkosten der Summe gegen das Summen-Optimum `base`, als Anteil von dessen Summe (0,05 = 5 %)."""
    return 0.0 if base.total <= 0 else r.total / base.total - 1.0


def gain(r: Result, base: Result) -> float:
    """Rückgang des Maximums gegen das Maximum des Summen-Optimums `base`, als Anteil (negativ: das Maximum wächst)."""
    return 0.0 if base.peak <= 0 else 1.0 - r.peak / base.peak


def solve(inst: Instance, p: float) -> Result:
    """Optimaler Plan für p = 1 (Summe), 2 (Quadratsumme), beliebiges p oder unendlich (Maximum): aufgezählt bis ENUM_MAX, sonst exakt über Löser."""
    c = inst.array()
    if c.shape[0] <= C.ENUM_MAX:
        return enumerate_optimum(c, p)
    return solve_bottleneck_lex(c) if math.isinf(p) else solve_lap(c, p)


def goal_p(goal: str) -> float:
    return {"sum": 1.0, "sumsq": 2.0, "max": math.inf}[goal]
