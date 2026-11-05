"""Orakel-Test preis-der-fairness-demo: der Kern gegen einen ANDEREN Rechenweg (ORACLE-PLAYBOOK §2, DEMO-PLAYBOOK §12).

Reines Python (itertools, Listen, Gleitkomma, keine numpy-Zeile im Referenzweg) gegen die Aufzählung und die Löser der Demo:
  * Summe, Quadratsumme, „Maximum, dann Summe“ und Leximax je Plan aus der Definition,
  * Preis und Gewinn aus den Referenzplänen,
  * der zufällige Gleichstand: der gewählte Plan liegt in der Optimalmenge (kleinstes Maximum), nie darüber,
  * die Löser (Ungarische Methode, Schwellwertsuche) gegen die Aufzählung bis n = 8, scipy als dritter Weg.
Mini-Instanzen n = 3 bis 6, feste Seeds (range statt Zufall), alle vier Familien; die Handwerte stehen in test_algorithm.py.
"""

import itertools
import math

import pytest

import fpr_algorithm as A
import fpr_evaluation as ev
from fpr_scenario import make_instance

scipy_opt = pytest.importorskip("scipy.optimize")


def _plans(c):
    n = len(c)
    for plan in itertools.permutations(range(n)):
        yield plan, [c[i][j] for i, j in enumerate(plan)]


def _ref(c):
    """Referenzwerte aus der Definition: effizientes Optimum, Maximum-dann-Summe, Leximax (alle als Kennzahlen, nicht als Pläne)."""
    best_sum = min(sum(b) for _, b in _plans(c))
    best_then_sum = min((max(b), sum(b)) for _, b in _plans(c))
    best_lex = min(tuple(sorted(b, reverse=True)) for _, b in _plans(c))
    return best_sum, best_then_sum, best_lex


def _cases(sizes=(3, 4, 5, 6), seeds=range(8)):
    for n in sizes:
        for family in range(4):
            for seed in seeds:
                yield n, family, seed


def test_efficient_plan_maximum_then_sum_and_leximax_match_the_definition():
    for n, family, seed in _cases():
        inst = make_instance(n, family, seed)
        best_sum, best_then_sum, best_lex = _ref(inst.c)
        a = ev.analyse(ev.Settings(n, family, seed))
        assert a.plans["sum"].total == pytest.approx(best_sum, rel=1e-12), (n, family, seed)
        assert (a.plans["max"].peak, a.plans["max"].total) == pytest.approx(best_then_sum), (n, family, seed)
        assert tuple(sorted(a.plans["leximax"].burdens, reverse=True)) == pytest.approx(best_lex), (n, family, seed)


def test_price_and_gain_follow_from_the_reference_plans():
    for n, family, seed in _cases(sizes=(4, 5), seeds=range(6)):
        inst = make_instance(n, family, seed)
        best_sum, (peak_fair, sum_fair), _ = _ref(inst.c)
        peaks_of_efficient = [max(b) for _, b in _plans(inst.c) if abs(sum(b) - best_sum) < 1e-9]
        a = ev.analyse(ev.Settings(n, family, seed))
        assert a.price("max") == pytest.approx(sum_fair / best_sum - 1.0, rel=1e-9, abs=1e-12)
        # Der Gewinn bezieht sich auf das Maximum des von der Aufzählung gewählten Summen-Optimums (bei Gleichständen der erste Plan);
        # es gehört zu den Plänen mit der kleinsten Summe, und der Gewinn folgt daraus.
        assert a.plans["sum"].peak in peaks_of_efficient
        assert a.gain("max") == pytest.approx(1.0 - peak_fair / a.plans["sum"].peak, rel=1e-9, abs=1e-12)


def test_random_tie_break_lands_in_the_optimal_set_of_the_maximum():
    for n, family, seed in _cases(sizes=(3, 4, 5, 6), seeds=range(5)):
        inst = make_instance(n, family, seed)
        smallest_max = min(max(b) for _, b in _plans(inst.c))
        for tie_seed in (0, 1, 999):
            r = A.solve_bottleneck_random(inst.array(), tie_seed)
            assert r.peak == pytest.approx(smallest_max) and A.check_feasible(r.plan, n)
            assert r.total >= A.solve_bottleneck_lex(inst.array()).total - 1e-9      # die Regel „dann Summe“ ist die billigste unter den Engpassplänen


def test_solvers_match_enumeration_up_to_the_enumeration_limit():
    for n in (5, 6, 7, 8):
        for family in range(4):
            for seed in range(3):
                c = make_instance(n, family, seed).array()
                for p in (1.0, 2.0, 3.0):
                    assert sum(b ** p for b in A.solve_lap(c, p).burdens) == pytest.approx(sum(b ** p for b in A.enumerate_optimum(c, p).burdens), rel=1e-9)
                lex, enum = A.solve_bottleneck_lex(c), A.enumerate_optimum(c, math.inf)
                assert (lex.peak, lex.total) == pytest.approx((enum.peak, enum.total))


def test_enumeration_matches_scipy_assignment_for_sum_and_squares():
    for n in (3, 4, 5, 6, 7):
        for family in range(4):
            for seed in range(5):
                c = make_instance(n, family, seed).array()
                for p in (1.0, 2.0):
                    rows, cols = scipy_opt.linear_sum_assignment(c ** p)
                    assert (c ** p)[rows, cols].sum() == pytest.approx(sum(b ** p for b in A.enumerate_optimum(c, p).burdens), rel=1e-9)


def test_lower_bound_is_below_every_plans_maximum_and_often_attained():
    attained = 0
    for n, family, seed in _cases(sizes=(3, 4, 5, 6), seeds=range(6)):
        inst = make_instance(n, family, seed)
        lower = max(min(row) for row in inst.c)                     # reine Python-Fassung der Schranke
        assert A.lower_bound(inst.array()) == lower
        smallest_max = min(max(b) for _, b in _plans(inst.c))
        assert lower <= smallest_max + 1e-12
        attained += smallest_max <= lower + 1e-12
    assert attained > 0                                             # die Schranke ist nicht immer, aber oft erreicht
