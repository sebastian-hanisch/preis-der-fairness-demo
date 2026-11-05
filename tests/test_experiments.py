"""Experimente der App: jede Auswahl des fairen Plans, jedes Preset und jede p-Stufe laufen ohne Fehler und zeigen ein Verdikt."""

import os
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import fpr_constants as C

APP = str(Path(__file__).resolve().parent.parent / "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))
BAND_CHOICES = ["Quadratsumme", "Maximum, dann Summe", "Maximum, zufälliger Gleichstand", "Leximax (n = 6 bis 8, aufgezählt)"]


def _app() -> AppTest:
    at = AppTest.from_file(APP, default_timeout=TIMEOUT)
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _texts(at) -> str:
    return " ".join(m.value for kind in ("success", "info", "warning") for m in getattr(at, kind))


@pytest.mark.parametrize("choice", BAND_CHOICES)
def test_every_choice_of_the_fair_plan_in_the_bands_runs_and_names_the_plan(choice):
    at = _app()
    at.selectbox(key="band_fair").set_value(choice).run()
    assert not at.exception, [str(e) for e in at.exception]
    assert f"Plan „{choice.split(' (')[0]}“" in _texts(at)


def test_every_p_step_runs_and_the_verdict_mentions_the_price():
    at = _app()
    for p in ("1", "1,5", "2", "3", "5", "10", "20", "∞"):
        at.select_slider(key="p_slider").set_value(p).run()
        assert not at.exception, (p, [str(e) for e in at.exception])
    assert "Preis" in _texts(at)


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_every_preset_runs_and_shows_the_price_verdict(name):
    at = _app()
    at.sidebar.button(key=f"preset_{name}").click().run()
    assert not at.exception, (name, [str(e) for e in at.exception])
    text = _texts(at)
    assert "Plan „Maximum, dann Summe“" in text and ("Konflikt" in text or "Summe" in text)


def test_the_tie_seed_changes_only_the_random_plan():
    at = _app()
    before = at.metric[1].value
    at.sidebar.number_input(key="tie_seed_input").set_value(5).run()
    assert not at.exception and at.metric[1].value == before      # die Kennzahl gilt „Maximum, dann Summe“ und hängt nicht am Gleichstands-Seed
