"""Jede Zahl aus dem README wird hier nachgerechnet (DEMO-PLAYBOOK §4). Die Zahlen sind exakt: Aufzählung, Löser und Zufallszusatzkosten
mit festem Seed sind deterministisch (Zusatzkosten reell, also eindeutig, unabhängig von der Bibliothek)."""

from pathlib import Path

import pytest

import fpr_constants as C
import fpr_evaluation as ev

README = (Path(__file__).resolve().parent.parent / "README.md").read_text(encoding="utf-8")
INT, REAL, PERSON, HEAVY = range(4)
HAND, NO_CONFLICT, TIE_COSTS, EXPENSIVE, LEXIMAX, SQ_WORSE, BIG = list(C.PRESETS)


@pytest.fixture(scope="module")
def bands():
    """(Familie, fairer Plan) -> Zeilen von band_rows; je einmal gerechnet."""
    return {(f, k): ev.band_rows(f, k) for f in range(4) for k in ("max", "maxrand", "leximax")}


def _med(rows, key):
    return [r[key][1] for r in rows]


def _line(values, digits=1):
    return " / ".join(ev.de(v * 100.0, digits) for v in values)


def _claim(values, unit=" %"):
    return "**" + _line(values) + unit + "**"


def test_sweep_instances_are_the_documented_ones():
    assert C.SWEEP_SEEDS == tuple(range(100000, 100020)) and C.BAND_SIZES == (10, 20, 50, 100, 200) and C.LEX_SIZES == (6, 7, 8) and C.DOM_SIZES == (10, 50, 200)
    assert "Seeds 100000 bis 100019" in README


def test_handbook_example_claims():
    a = ev.analyse(ev.Settings())
    assert (ev.pct(a.price("sumsq")), ev.pct(a.gain("sumsq")), ev.pct(a.price("max")), ev.pct(a.gain("max"))) == ("7,1 %", "14,3 %", "14,3 %", "28,6 %")
    assert a.plans["max"].peak == a.lower == 5.0 and a.plans["leximax"].plan == a.plans["max"].plan and a.plans_total == 24
    for text in ("Preis **7,1 %**, Gewinn **14,3 %**", "Preis **14,3 %**, Gewinn **28,6 %**", "Summe 16 statt 14, Maximum 5 statt 7"):
        assert text in README


def test_price_of_maximum_then_sum_claims(bands):
    assert [_line(_med(bands[(f, "max")], "price")) for f in (REAL, PERSON, HEAVY, INT)] == [
        "0,4 / 2,3 / 3,0 / 1,9 / 0,6", "4,2 / 2,3 / 1,4 / 0,9 / 0,6", "0,8 / 1,9 / 0,9 / 1,1 / 0,9", "0,0 / 0,0 / 0,0 / 0,0 / 0,0"]
    for text in ("**0,4 / 2,3 / 3,0 / 1,9 / 0,6 %**", "**4,2 / 2,3 / 1,4 / 0,9 / 0,6 %**", "**0,8 / 1,9 / 0,9 / 1,1 / 0,9 %**", "**0,0 / 0,0 / 0,0 / 0,0 / 0,0 %**"):
        assert text in README


def test_largest_price_claims(bands):
    assert _line([r["price"][2] for r in bands[(REAL, "max")]]) == "17,0 / 25,6 / 14,2 / 8,6 / 5,0"
    assert _line([r["price"][2] for r in bands[(HEAVY, "max")]]) == "37,1 / 6,9 / 4,2 / 3,1 / 2,9"
    assert "**17,0 / 25,6 / 14,2 / 8,6 / 5,0 %**" in README and "**37,1 / 6,9 / 4,2 / 3,1 / 2,9 %**" in README


def test_random_tie_break_price_claims(bands):
    assert _line(_med(bands[(REAL, "maxrand")], "price")) == "12,5 / 39,6 / 54,1 / 60,2 / 90,9"
    assert _line(_med(bands[(PERSON, "maxrand")], "price")) == "16,1 / 21,0 / 23,9 / 22,9 / 22,2"
    assert _line(_med(bands[(HEAVY, "maxrand")], "price")) == "14,1 / 21,1 / 31,4 / 31,7 / 32,6"
    assert ev.de(max(r["price"][2] for r in bands[(REAL, "maxrand")]) * 100) == "218,7"
    for text in ("**12,5 / 39,6 / 54,1 / 60,2 / 90,9 %**", "**16,1 / 21,0 / 23,9 / 22,9 / 22,2 %**", "**14,1 / 21,1 / 31,4 / 31,7 / 32,6 %**", "218,7 %"):
        assert text in README


def test_instances_over_five_percent_claims(bands):
    assert [r["over"] for r in bands[(REAL, "maxrand")]] == [15, 19, 20, 20, 20] and [r["over"] for r in bands[(REAL, "max")]] == [8, 7, 4, 3, 1]
    assert "**15 / 19 / 20 / 20 / 20** von 20" in README and "**8 / 7 / 4 / 3 / 1** von 20" in README


def test_gain_claims(bands):
    assert _line(_med(bands[(REAL, "max")], "gain")) == "2,5 / 12,4 / 16,3 / 21,0 / 9,1"
    assert _line(_med(bands[(PERSON, "max")], "gain")) == "12,9 / 11,2 / 19,1 / 20,9 / 24,3"
    assert _line(_med(bands[(HEAVY, "max")], "gain")) == "0,5 / 8,5 / 9,3 / 16,6 / 15,0"
    assert [r["gain_zero"] for r in bands[(INT, "max")]] == [13, 16, 20, 20, 20]
    for text in ("**2,5 / 12,4 / 16,3 / 21,0 / 9,1 %**", "**12,9 / 11,2 / 19,1 / 20,9 / 24,3 %**", "**0,5 / 8,5 / 9,3 / 16,6 / 15,0 %**", "**13 / 16 / 20 / 20 / 20** von 20"):
        assert text in README


def test_reach_claims():
    got = {f: [r["at_bound"] for r in ev.reach_rows(f)] for f in range(4)}
    assert got == {REAL: [8, 6, 9], PERSON: [17, 16, 15], HEAVY: [9, 12, 7], INT: [14, 20, 20]}
    for text in ("**8 / 6 / 9**", "**17 / 16 / 15**", "**9 / 12 / 7**", "**14 / 20 / 20**"):
        assert text in README


def test_dominance_claims():
    got = {f: ev.dominance_rows(f) for f in range(4)}
    assert {f: [r["max_dom"] for r in rows] for f, rows in got.items()} == {REAL: [1, 7, 18], PERSON: [4, 12, 20], HEAVY: [2, 10, 4], INT: [0, 0, 0]}
    assert sum(r["sq_dom"] for rows in got.values() for r in rows) == 0 and sum(r["seeds"] for rows in got.values() for r in rows) == 240
    for text in ("**1 / 7 / 18**", "**4 / 12 / 20**", "**2 / 10 / 4**", "**0 / 0 / 0** von 20", "**Quadrat dominiert in 0 von 240**"):
        assert text in README


def test_square_can_enlarge_the_maximum_claim():
    rows = ev.band_rows(REAL, "sumsq")
    assert ev.pct(rows[1]["gain"][0]) == "-4,1 %" and rows[1]["n"] == 20
    assert "**−4,1 %**" in README
    assert ev.pct(ev.analyse(ev.Settings(**C.PRESETS[SQ_WORSE])).gain("sumsq")) == "-4,1 %"


def test_leximax_band_claims(bands):
    assert _line(_med(bands[(REAL, "leximax")], "price")) == "0,0 / 0,0 / 6,7"
    assert _line(_med(bands[(PERSON, "leximax")], "price")) == "4,0 / 5,5 / 5,7"
    assert _line(_med(bands[(HEAVY, "leximax")], "price")) == "1,3 / 0,6 / 1,0"
    assert [r["over"] for r in bands[(PERSON, "leximax")]] == [9, 10, 12]
    for text in ("**0,0 / 0,0 / 6,7 %**", "**4,0 / 5,5 / 5,7 %**", "**1,3 / 0,6 / 1,0 %**", "**9 / 10 / 12** von 20"):
        assert text in README


def test_preset_claims():
    a = ev.analyse(ev.Settings(**C.PRESETS[TIE_COSTS]))
    assert (ev.pct(a.price("maxrand")), ev.pct(a.price("max")), ev.pct(a.gain("max"))) == ("142,9 %", "1,2 %", "23,5 %")
    assert "zufälliger Gleichstand **142,9 %**" in README and "„dann kleinste Summe“ **1,2 %**" in README and "Gewinn beider **23,5 %**" in README

    a = ev.analyse(ev.Settings(**C.PRESETS[EXPENSIVE]))
    assert (ev.pct(a.price("max")), ev.pct(a.gain("max"))) == ("28,9 %", "14,4 %") and "Preis **28,9 %**, Gewinn **14,4 %**" in README

    a = ev.analyse(ev.Settings(**C.PRESETS[LEXIMAX]))
    assert (ev.pct(a.price("leximax")), ev.pct(a.price("max")), ev.pct(a.gain("max")), a.tie_size) == ("15,6 %", "5,9 %", "6,1 %", 1356)
    for text in ("Leximax **15,6 %** Preis", "„Maximum, dann Summe“ **5,9 %**", "beide Gewinn **6,1 %**", "**1356** Pläne"):
        assert text in README

    a = ev.analyse(ev.Settings(**C.PRESETS[NO_CONFLICT]))
    assert a.price("max") == 0.0 and a.gain("max") == 0.0 and ev.pct(a.price("maxrand")) == "35,3 %" and "dennoch **35,3 %**" in README


def test_big_preset_p_curve_claims():
    s = ev.Settings(**C.PRESETS[BIG])
    rows = ev.p_rows(s)
    got_price = [r["price"] for r in rows[1:]]
    got_gain = [r["gain"] for r in rows[1:]]
    assert _line(got_price) == "0,8 / 1,2 / 1,9 / 2,5 / 4,3 / 5,0 / 0,8" and _line(got_gain) == "8,0 / 10,1 / 10,1 / 16,5 / 17,8 / 18,6 / 18,6"
    assert got_price[-1] < got_price[-2]                                 # der Preis fällt bei ∞
    assert "**0,8 / 1,2 / 1,9 / 2,5 / 4,3 / 5,0 / 0,8 %**" in README and "**8,0 / 10,1 / 10,1 / 16,5 / 17,8 / 18,6 / 18,6 %**" in README
    a = ev.analyse(s)
    assert (ev.pct(a.price("max")), ev.pct(a.gain("max"))) == ("0,8 %", "18,6 %")
