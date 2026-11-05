"""Randfälle, an denen Kernroutinen erfahrungsgemäß brechen (DEMO-PLAYBOOK §12)."""

import math

import numpy as np
import pytest

import fpr_algorithm as A
import fpr_constants as C
import fpr_evaluation as ev
from fpr_scenario import Instance, make_instance


def test_a_single_person_has_the_only_plan_and_everything_is_zero():
    c = np.array([[6.0]])
    base = A.enumerate_optimum(c, 1.0)
    for r in (A.enumerate_optimum(c, 2.0), A.enumerate_optimum(c, math.inf), A.solve_leximax(c), A.solve_bottleneck_random(c, 3)):
        assert r.plan == (0,) and A.price(r, base) == 0.0 and A.gain(r, base) == 0.0
    assert A.lower_bound(c) == 6.0


def test_exactly_two_persons():
    a = ev.analyse(ev.Settings(2, 1, 5))
    assert a.plans_total == 2 and a.tie_size >= 1 and "leximax" in a.plans
    assert ev.Settings(C.N_MIN).n == 3 and C.N_MIN <= 3


def test_all_entries_equal_make_every_plan_optimal_and_price_and_gain_vanish():
    c = np.full((4, 4), 5.0)
    base = A.enumerate_optimum(c, 1.0)
    assert len(A.optimal_set(c, math.inf)) == 24 and A.lower_bound(c) == 5.0
    for r in (A.enumerate_optimum(c, 2.0), A.enumerate_optimum(c, math.inf), A.solve_leximax(c), A.solve_bottleneck_random(c, 9)):
        assert A.price(r, base) == 0.0 and A.gain(r, base) == 0.0


def test_integers_with_many_ties_give_feasible_plans_for_every_fair_plan():
    for seed in range(30):
        a = ev.analyse(ev.Settings(6, 0, seed))
        assert all(A.check_feasible(r.plan, 6) for r in a.plans.values())
        assert a.tie_size >= 1 and a.lower == A.lower_bound(a.inst.array())


def test_seed_zero_and_the_largest_seeds_work():
    for seed in (0, C.SEED_MAX):
        assert ev.analyse(ev.Settings(5, 1, seed, 0)).enumerated
    assert ev.analyse(ev.Settings(5, 1, 3, C.TIE_SEED_MAX)).plans["maxrand"].peak > 0


def test_bounds_are_inclusive_leximax_exists_exactly_up_to_the_enumeration_limit():
    for n in (C.N_MIN, C.ENUM_MAX, C.ENUM_MAX + 1):
        a = ev.analyse(ev.Settings(n, 1, 7))
        assert a.enumerated == (n <= C.ENUM_MAX) and ("leximax" in a.plans) == (n <= C.ENUM_MAX)
        assert (a.plans_total is None) == (n > C.ENUM_MAX) and (a.tie_size is None) == (n > C.ENUM_MAX)


def test_one_very_expensive_task_fixes_the_maximum_for_every_plan():
    """Aufgabe 2 kostet 50 bei jeder Person außer Person 2: die Untergrenze ist die zäheste Person (Person 2: 5)."""
    c = np.array([[1.0, 2.0, 50.0], [2.0, 1.0, 50.0], [9.0, 9.0, 5.0]])
    assert A.lower_bound(c) == 5.0 and A.enumerate_optimum(c, math.inf).peak == 5.0


def test_a_large_instance_is_solved_exactly_for_every_plan_but_leximax():
    a = ev.analyse(ev.Settings(C.N_MAX, 3, 3))
    assert not a.enumerated and "leximax" not in a.plans and a.inst.n == C.N_MAX
    assert a.plans["sum"].total <= a.plans["sumsq"].total + 1e-9 and a.plans["max"].peak <= a.plans["sum"].peak + 1e-9
    assert a.price("max") >= -1e-12 and a.gain("max") >= -1e-12


def test_integers_with_many_persons_have_no_conflict():
    """Ganze Zahlen 1 bis 9 bei n = 50: das Summen-Optimum besteht aus Einsen, jedes Ziel wählt gleichwertig (Preset „Kein Konflikt“)."""
    a = ev.analyse(ev.Settings(50, 0, 0))
    assert a.price("max") == 0.0 and a.gain("max") == 0.0 and a.price("sumsq") == 0.0 and a.lower == 1.0


def test_p_rows_end_at_the_rule_maximum_then_sum_and_start_at_zero():
    rows = ev.p_rows(ev.Settings(6, 2, 4))
    assert [r["p"] for r in rows] == list(C.P_VALUES) and rows[0]["price"] == 0.0 and rows[0]["gain"] == 0.0
    a = ev.analyse(ev.Settings(6, 2, 4))
    assert rows[-1]["price"] == pytest.approx(a.price("max")) and rows[-1]["gain"] == pytest.approx(a.gain("max"))


def test_band_rows_cover_the_documented_sizes_and_fair_plans():
    seeds = range(100000, 100003)
    assert [r["n"] for r in ev.band_rows(2, "max", seeds=seeds)] == list(C.BAND_SIZES)
    assert [r["n"] for r in ev.band_rows(2, "leximax", seeds=seeds)] == list(C.LEX_SIZES)
    for fair in ("sumsq", "max", "maxrand", "leximax"):
        for r in ev.band_rows(1, fair, seeds=seeds):
            lo, med, hi = r["price"]
            assert lo - 1e-12 <= med <= hi + 1e-12 and lo >= -1e-12 and r["seeds"] == 3 and 0 <= r["over"] <= 3 and 0 <= r["gain_zero"] <= 3
    with pytest.raises(ValueError):
        ev.band_rows(1, "unbekannt", seeds=seeds)


def test_instance_rows_are_always_finite():
    for family in range(4):
        c = make_instance(60, family, 1).array()
        assert np.isfinite(c).all() and Instance(tuple(tuple(r) for r in c.tolist())).n == 60
