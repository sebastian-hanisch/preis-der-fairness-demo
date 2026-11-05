"""Verdikte: reine Funktionen, jede Verzweigung und jede Zahl im Text an handgesetzten oder von Hand geprüften Werten."""

import fpr_constants as C
import fpr_evaluation as ev


def _preset(name):
    return ev.analyse(ev.Settings(**C.PRESETS[name]))


HAND, NO_CONFLICT, TIE_COSTS, EXPENSIVE, LEXIMAX, SQ_WORSE, BIG = list(C.PRESETS)


def test_number_formatting_uses_decimal_commas_and_no_negative_zero():
    assert ev.de(3.14159) == "3,1" and ev.pct(0.05) == "5,0 %" and ev.pct(-0.0000001) == "0,0 %" and ev.pct(0.2857142857) == "28,6 %"
    assert ev.p_label(1.5) == "1,5" and ev.p_label(10.0) == "10" and ev.p_label(float("inf")) == "∞"


def test_prices_verdict_for_the_hand_example_states_both_numbers():
    kind, text = ev.verdict_prices(_preset(HAND))
    assert kind == "success"
    assert "kostet 14,3 % Summe (16,0 gegen 14,0)" in text and "bringt 28,6 % am Maximum (5,0 gegen 7,0)" in text


def test_prices_verdict_without_conflict_says_so_and_names_the_shared_values():
    kind, text = ev.verdict_prices(_preset(NO_CONFLICT))
    assert kind == "info" and "keinen Konflikt" in text and "(51,0)" in text and "(2,0)" in text


def test_prices_verdict_warns_when_the_square_enlarges_the_maximum():
    kind, text = ev.verdict_prices(_preset(SQ_WORSE))
    assert kind == "warning" and "vergrößert hier das Maximum um 4,1 %" in text


def test_tie_verdict_warns_when_the_rule_makes_the_price_much_smaller():
    kind, text = ev.verdict_tie(_preset(TIE_COSTS))
    assert kind == "warning" and "142,9 %" in text and "1,2 %" in text and "Prozentpunkte" in text and "16,7" in text


def test_tie_verdict_is_calm_when_both_engpass_plans_coincide_and_names_the_optimal_set():
    kind, text = ev.verdict_tie(_preset(HAND))
    assert kind == "info" and "14,3 % ohne Regel, 14,3 % mit Regel" in text and "genau einen Plan" in text


def test_tie_verdict_names_the_size_of_the_optimal_set_when_it_is_large():
    kind, text = ev.verdict_tie(_preset(LEXIMAX))
    assert kind == "warning" and "1356 Pläne" in text


def _rows(prices, gains):
    return [{"p": p, "price": a, "gain": b} for p, a, b in zip(C.P_VALUES, prices, gains)]


def test_p_verdict_warns_about_the_fall_at_infinity_with_both_numbers():
    rows = _rows([0, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.02], [0, 0.1, 0.15, 0.2, 0.2, 0.2, 0.2, 0.2])
    kind, text = ev.verdict_p(rows)
    assert kind == "warning" and "bis p = 20 auf 6,0 %" in text and "fällt bei p = ∞ auf 2,0 %" in text and "ab p = 3 erreicht" in text and "20,0 %" in text


def test_p_verdict_is_calm_when_the_price_rises_to_infinity():
    rows = _rows([0, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07], [0, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1])
    kind, text = ev.verdict_p(rows)
    assert kind == "info" and "höchstens auf 7,0 %" in text and "bei p = ∞: 7,0 %" in text and "ab p = 1,5 erreicht" in text


def test_p_verdict_says_when_no_p_gains_anything():
    kind, text = ev.verdict_p(_rows([0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0]))
    assert kind == "info" and "Kein p bringt hier einen Gewinn" in text


def _band_rows():
    return [{"n": 10, "seeds": 20, "price": (0.0, 0.004, 0.17), "gain": (0.0, 0.025, 0.491), "over": 8, "gain_zero": 10},
            {"n": 20, "seeds": 20, "price": (0.0, 0.023, 0.256), "gain": (0.0, 0.124, 0.377), "over": 7, "gain_zero": 6}]


def test_band_verdict_lists_every_size_with_spans_and_counts_without_a_trend_word():
    kind, text = ev.verdict_band(_band_rows(), "max")
    assert kind == "info" and "Je 20 feste Instanzen" in text and "„Maximum, dann Summe“" in text
    assert "n = 10: Preis Median 0,4 % (Spanne 0,0 % bis 17,0 %), Gewinn Median 2,5 % (Spanne 0,0 % bis 49,1 %), Preis über 5 % in 8 von 20, Gewinn null in 10" in text
    assert "n = 20: Preis Median 2,3 %" in text
    for word in ("fällt", "steigt", "wächst", "sinkt", "Trend"):
        assert word not in text


def test_band_verdict_warns_for_the_random_tie_break_when_instances_are_expensive():
    assert ev.verdict_band(_band_rows(), "maxrand")[0] == "warning"
    assert ev.verdict_band([{**r, "over": 0} for r in _band_rows()], "maxrand")[0] == "info"


def test_dominance_verdict_counts_each_case_and_names_negative_square_gains():
    rows = [{"n": 10, "seeds": 20, "max_dom": 1, "sq_dom": 0, "same": 10, "neither": 9, "sq_negative": 0},
            {"n": 50, "seeds": 20, "max_dom": 7, "sq_dom": 0, "same": 3, "neither": 10, "sq_negative": 2}]
    kind, text = ev.verdict_dominance(rows)
    assert kind == "info" and "n = 10: „Maximum, dann Summe“ dominiert in 1 von 20, das Quadrat in 0, gleich in 10, keines in 9" in text
    assert "vergrößert das Maximum in 2 dieser Instanzen" in text
    assert "vergrößert" not in ev.verdict_dominance([{**rows[0]}])[1]


def test_reach_verdict_for_the_hand_example_says_the_bound_is_reached():
    rows = [{"n": 10, "seeds": 20, "at_bound": 14, "gain_zero": 13}]
    kind, text = ev.verdict_reach(_preset(HAND), rows)
    assert kind == "info" and "mindestens 5,0" in text and "ist 5,0 und erreicht sie" in text and "Schranke erreicht in 14 von 20, Gewinn null in 13" in text


def test_reach_verdict_names_the_distance_when_the_maximum_lies_above_the_bound():
    kind, text = ev.verdict_reach(_preset(EXPENSIVE), [{"n": 10, "seeds": 20, "at_bound": 9, "gain_zero": 10}])
    assert "mindestens 10,2" in text and "ist 15,3 und liegt darüber" in text
