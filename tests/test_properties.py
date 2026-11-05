"""Eigenschaftstests (ORACLE-PLAYBOOK §5): Aussagen, die für jede Instanz gelten müssen, an festen Seeds und allen vier Familien."""

import math

import numpy as np
import pytest

import fpr_algorithm as A
import fpr_constants as C
import fpr_evaluation as ev
from fpr_scenario import Instance, make_instance

CASES = [(n, family, seed) for n in (3, 5, 7) for family in range(4) for seed in range(4)]


def _plans(c: np.ndarray, tie_seed=5) -> dict:
    inst = Instance(tuple(tuple(float(x) for x in row) for row in c))
    base = A.solve(inst, 1.0)
    out = {"sum": base, "sumsq": A.solve(inst, 2.0), "max": A.solve(inst, math.inf), "maxrand": A.solve_bottleneck_random(c, tie_seed)}
    if inst.n <= C.ENUM_MAX:
        out["leximax"] = A.solve_leximax(c)
    return out


@pytest.mark.parametrize("n,family,seed", CASES)
def test_price_is_never_negative_and_the_engpass_gain_is_never_negative(n, family, seed):
    a = ev.analyse(ev.Settings(n, family, seed))
    for key in a.plans:
        assert a.price(key) >= -1e-12, key
    for key in ("max", "maxrand", "leximax"):
        assert a.gain(key) >= -1e-12, key


@pytest.mark.parametrize("n,family,seed", CASES)
def test_the_three_engpass_plans_share_one_gain_and_their_prices_are_ordered(n, family, seed):
    """Alle Engpasspläne haben dasselbe, kleinstmögliche Maximum, also denselben Gewinn. „Dann Summe“ ist unter ihnen der billigste."""
    a = ev.analyse(ev.Settings(n, family, seed))
    assert a.gain("max") == pytest.approx(a.gain("maxrand")) == pytest.approx(a.gain("leximax"))
    assert 0.0 - 1e-12 <= a.price("max") <= a.price("leximax") + 1e-12
    assert a.price("max") <= a.price("maxrand") + 1e-12


@pytest.mark.parametrize("n,family,seed", CASES)
def test_the_gain_cannot_exceed_what_the_lower_bound_allows(n, family, seed):
    a = ev.analyse(ev.Settings(n, family, seed))
    cap = 1.0 - a.lower / a.plans["sum"].peak
    for key in a.plans:
        assert a.gain(key) <= cap + 1e-9, key


@pytest.mark.parametrize("n,family,seed", CASES)
def test_price_and_gain_are_scale_invariant(n, family, seed):
    c = make_instance(n, family, seed).array()
    for factor in (0.5, 3.0, 1000.0):
        for key, r in _plans(c).items():
            r2 = _plans(c * factor)[key]
            base, base2 = _plans(c)["sum"], _plans(c * factor)["sum"]
            assert A.price(r2, base2) == pytest.approx(A.price(r, base), abs=1e-9), (key, factor)
            assert A.gain(r2, base2) == pytest.approx(A.gain(r, base), abs=1e-9), (key, factor)


@pytest.mark.parametrize("n,family,seed", [(5, 1, 3), (6, 2, 1), (4, 0, 7), (7, 3, 2)])
def test_permuting_rows_and_columns_changes_neither_price_nor_gain(n, family, seed):
    c = make_instance(n, family, seed).array()
    rng = np.random.default_rng(seed + 100)
    perm_r, perm_c = rng.permutation(n), rng.permutation(n)
    c2 = c[perm_r][:, perm_c]
    for key in ("sumsq", "max", "leximax"):
        a1 = ev.analyse(ev.Settings(n, family, seed))
        r1, r2 = _plans(c)[key], _plans(c2)[key]
        base1, base2 = _plans(c)["sum"], _plans(c2)["sum"]
        assert A.price(r2, base2) == pytest.approx(A.price(r1, base1), abs=1e-9), key
        assert A.gain(r2, base2) == pytest.approx(A.gain(r1, base1), abs=1e-9), key
        assert A.lower_bound(c2) == A.lower_bound(c) and a1.lower == A.lower_bound(c)


@pytest.mark.parametrize("n,family,seed", [(5, 1, 3), (6, 2, 1), (7, 3, 2), (8, 1, 4)])
def test_adding_a_constant_never_raises_the_price_of_the_engpass_plan(n, family, seed):
    """Alle Summen wachsen um n*k, alle Maxima um k: die Engpasspläne bleiben dieselben, ihre Mehrkosten werden relativ kleiner."""
    c = make_instance(n, family, seed).array()
    for key in ("max", "leximax"):
        r, base = _plans(c)[key], _plans(c)["sum"]
        r2, base2 = _plans(c + 25.0)[key], _plans(c + 25.0)["sum"]
        assert r2.plan == r.plan
        assert A.price(r2, base2) <= A.price(r, base) + 1e-12


@pytest.mark.parametrize("n,family,seed", [(5, 1, 3), (8, 2, 6), (12, 3, 2), (30, 1, 5)])
def test_the_random_tie_break_never_changes_the_maximum_and_never_beats_the_rule(n, family, seed):
    c = make_instance(n, family, seed).array()
    lex = A.solve_bottleneck_lex(c)
    peaks, totals = set(), []
    for tie_seed in range(12):
        r = A.solve_bottleneck_random(c, tie_seed)
        peaks.add(round(r.peak, 9))
        totals.append(r.total)
    assert peaks == {round(lex.peak, 9)} and min(totals) >= lex.total - 1e-9


def test_everything_is_deterministic():
    s = ev.Settings(6, 3, 11, 77)
    a1, a2 = ev.analyse(s), ev.analyse(s)
    assert {k: r.plan for k, r in a1.plans.items()} == {k: r.plan for k, r in a2.plans.items()}
    assert ev.band_rows(1, "maxrand", seeds=range(100000, 100003)) == ev.band_rows(1, "maxrand", seeds=range(100000, 100003))
