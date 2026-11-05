"""Handwerte: jede Einheit des Kerns an einem Beispiel, das von Hand nachgerechnet ist (DEMO-PLAYBOOK §1b)."""

import math

import numpy as np
import pytest

import fpr_algorithm as A
import fpr_constants as C
import fpr_evaluation as ev
from fpr_scenario import Instance, make_instance


def test_hand_example_prices_and_gains_from_the_hand_calculation(hand):
    a = ev.analyse(ev.Settings())
    s, q, m = a.plans["sum"], a.plans["sumsq"], a.plans["max"]
    assert (s.plan, s.total, s.peak) == ((0, 2, 3, 1), 14.0, 7.0)
    assert (q.plan, q.total, q.squares, q.peak) == ((1, 2, 3, 0), 15.0, 65.0, 6.0)
    assert (m.plan, m.total, m.peak) == ((3, 2, 1, 0), 16.0, 5.0)
    assert a.price("sum") == 0.0 and a.gain("sum") == 0.0
    assert a.price("sumsq") == pytest.approx(1 / 14) and a.gain("sumsq") == pytest.approx(1 / 7)
    assert a.price("max") == pytest.approx(2 / 14) and a.gain("max") == pytest.approx(2 / 7)


def test_hand_example_lower_bound_and_the_other_two_fair_plans(hand_array):
    assert A.lower_bound(hand_array) == 5.0                       # max(5, 3, 2, 2)
    a = ev.analyse(ev.Settings())
    assert a.plans["leximax"].plan == (3, 2, 1, 0)                # das Maximum 5 ist eindeutig, also ist Leximax derselbe Plan
    assert a.plans["maxrand"].plan == (3, 2, 1, 0) and a.tie_size == 1 and a.plans_total == 24


def test_leximax_differs_from_maximum_then_sum_on_the_constructed_matrix(lex3_array):
    """Zwei Pläne haben das kleinste Maximum 5: A (5, 5, 1; Summe 11) und B (5, 4, 4; Summe 13). Die Summe wählt A, Leximax wählt B."""
    efficient = A.enumerate_optimum(lex3_array, 1.0)
    then_sum = A.enumerate_optimum(lex3_array, math.inf)
    lex = A.solve_leximax(lex3_array)
    assert efficient.plan == (0, 1, 2) and then_sum.plan == (0, 1, 2) and lex.plan == (1, 2, 0)
    assert sorted(lex.burdens, reverse=True) == [5.0, 4.0, 4.0] and sorted(then_sum.burdens, reverse=True) == [5.0, 5.0, 1.0]
    assert A.price(lex, efficient) == pytest.approx(2 / 11) and A.gain(lex, efficient) == pytest.approx(0.0)
    assert A.price(then_sum, efficient) == 0.0


def test_random_tie_break_stays_in_the_optimal_set_of_the_maximum(lex3_array):
    """Die Optimalmenge beim Maximum sind A und B; der Zufall wählt eine von beiden, nie einen anderen Plan."""
    chosen = {A.solve_bottleneck_random(lex3_array, seed).plan for seed in range(40)}
    assert chosen <= {(0, 1, 2), (1, 2, 0)} and len(chosen) == 2      # mit 40 festen Seeds treten beide Pläne auf


def test_price_and_gain_of_the_n2_example_by_hand():
    """n = 2: c = [[1, 4], [3, 2]]. Der Plan (0, 1) hat Belastungen 1, 2 (Summe 3, Maximum 2); der Plan (1, 0) hat 4, 3 (Summe 7, Maximum 4)."""
    c = np.array([[1.0, 4.0], [3.0, 2.0]])
    base = A.enumerate_optimum(c, 1.0)
    other = A.make_result(c, (1, 0))
    assert base.plan == (0, 1) and A.price(other, base) == pytest.approx(7 / 3 - 1) and A.gain(other, base) == pytest.approx(1 - 4 / 2)


def test_price_and_gain_are_zero_for_an_instance_without_conflict():
    c = Instance(tuple(tuple([5.0] * 3) for _ in range(3))).array()
    base = A.enumerate_optimum(c, 1.0)
    for r in (A.enumerate_optimum(c, 2.0), A.enumerate_optimum(c, math.inf), A.solve_leximax(c), A.solve_bottleneck_random(c, 7)):
        assert A.price(r, base) == 0.0 and A.gain(r, base) == 0.0


def test_price_and_gain_guard_against_a_zero_baseline():
    zero = A.make_result(np.zeros((2, 2)), (0, 1))
    assert A.price(zero, zero) == 0.0 and A.gain(zero, zero) == 0.0


def test_leximax_refuses_sizes_beyond_the_enumeration_limit():
    with pytest.raises(ValueError):
        A.solve_leximax(make_instance(C.ENUM_MAX + 1, 1, 1).array())


def test_all_families_produce_instances_of_the_requested_shape_and_range():
    for family in range(len(C.FAMILIES)):
        c = make_instance(7, family, 5).array()
        assert c.shape == (7, 7) and (c >= 0).all()
    assert make_instance(6, 0, 3).array().max() <= 9 and make_instance(6, 1, 3).array().max() <= 100
    assert make_instance(5, 3, 3) == make_instance(5, 3, 3) and make_instance(5, 3, 3) != make_instance(5, 3, 4)


def test_solver_and_enumeration_agree_on_the_hand_example(hand_array):
    for p in (1.0, 2.0):
        assert A.solve_lap(hand_array, p).total == A.enumerate_optimum(hand_array, p).total
    assert A.solve_bottleneck_lex(hand_array).plan == A.enumerate_optimum(hand_array, math.inf).plan
