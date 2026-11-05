"""Gemeinsame Fixtures: das Handbeispiel und die Leximax-Matrix, an denen jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b)."""

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fpr_scenario import Instance  # noqa: E402

HAND = ((7.0, 6.0, 7.0, 5.0), (6.0, 4.0, 3.0, 6.0), (8.0, 4.0, 7.0, 2.0), (4.0, 2.0, 2.0, 6.0))
# n = 3, nur zwei Pläne haben das kleinste Maximum 5: A = (0, 1, 2) mit Belastungen 5, 5, 1 (Summe 11) und B = (1, 2, 0) mit 5, 4, 4 (Summe 13).
LEX3 = ((5.0, 5.0, 9.0), (9.0, 5.0, 4.0), (4.0, 9.0, 1.0))


@pytest.fixture
def hand():
    """Handbeispiel n = 4 (Zeile Person, Spalte Aufgabe). Von Hand: Summe 14 mit Plan (0, 2, 3, 1), Quadratsumme 65 mit Plan (1, 2, 3, 0),
    Maximum 5 mit Plan (3, 2, 1, 0); Preis und Gewinn: Quadrat 1/14 und 1/7, Maximum 2/14 und 2/7; untere Schranke des Maximums 5."""
    return Instance(HAND)


@pytest.fixture
def hand_array(hand) -> np.ndarray:
    return hand.array()


@pytest.fixture
def lex3_array() -> np.ndarray:
    """Von Hand: das Summen-Optimum und „Maximum, dann Summe“ wählen A = (0, 1, 2) (Summe 11, Maximum 5); Leximax wählt B = (1, 2, 0)
    mit dem sortierten Vektor (5, 4, 4) statt (5, 5, 1): Preis 2/11, Gewinn 0."""
    return np.array(LEX3, dtype=float)
