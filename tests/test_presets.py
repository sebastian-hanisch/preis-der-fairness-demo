"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen, und was jedes Preset zeigen soll."""

import fpr_constants as C
import fpr_evaluation as ev
import fpr_presets as P

HAND, NO_CONFLICT, TIE_COSTS, EXPENSIVE, LEXIMAX, SQ_WORSE, BIG = list(C.PRESETS)


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_slider_bounds():
    for preset in C.PRESETS.values():
        assert C.N_MIN <= preset["n"] <= C.N_MAX and 0 <= preset["family"] < len(C.FAMILIES)
        assert 0 <= preset["seed"] <= C.SEED_MAX and 0 <= preset["tie_seed"] <= C.TIE_SEED_MAX


def test_default_preset_equals_the_default_settings():
    assert ev.Settings(**C.PRESETS[HAND]) == ev.Settings()


def test_setting_specs_cover_every_preset_key():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)


def _analysis(name):
    return ev.analyse(ev.Settings(**C.PRESETS[name]))


def test_handbeispiel_preset_shows_a_price_and_a_gain_for_each_fair_plan():
    a = _analysis(HAND)
    assert a.enumerated and a.plans_total == 24 and a.tie_size == 1
    assert 0.0 < a.price("sumsq") < a.price("max") and 0.0 < a.gain("sumsq") < a.gain("max")


def test_no_conflict_preset_has_no_price_for_the_rule_but_a_large_one_for_the_random_tie_break():
    a = _analysis(NO_CONFLICT)
    assert not a.enumerated and a.price("max") == 0.0 and a.gain("max") == 0.0 and a.price("maxrand") > 0.2


def test_tie_costs_preset_shows_a_huge_difference_with_a_real_gain():
    a = _analysis(TIE_COSTS)
    assert a.price("maxrand") - a.price("max") > 1.0 and a.price("max") < 0.02 and a.gain("max") > 0.2


def test_expensive_gain_preset_pays_almost_a_third_for_a_visible_gain():
    a = _analysis(EXPENSIVE)
    assert a.enumerated and 0.25 < a.price("max") < 0.35 and a.gain("max") > 0.1


def test_leximax_preset_pays_clearly_more_than_maximum_then_sum_for_the_same_gain():
    a = _analysis(LEXIMAX)
    assert a.enumerated and a.price("leximax") > a.price("max") + 0.05 and abs(a.gain("leximax") - a.gain("max")) < 1e-12 and a.tie_size > 1000


def test_square_worse_preset_has_a_negative_gain_under_the_squares():
    a = _analysis(SQ_WORSE)
    assert a.gain("sumsq") < -0.04 and a.gain("max") == 0.0 and a.price("max") == 0.0


def test_big_preset_is_not_enumerated_and_the_gain_is_large_while_the_price_is_small():
    a = _analysis(BIG)
    assert not a.enumerated and a.gain("max") > 0.15 and a.price("max") < 0.02 and a.price("maxrand") > 0.1
