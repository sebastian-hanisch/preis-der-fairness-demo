"""Konstanten: Regler-Grenzen, feste Annahmen, Farben und Presets."""

import math

N_MIN, N_MAX, DEFAULT_N = 3, 200, 4
ENUM_MAX = 8                                  # bis hierher werden alle n! Pläne aufgezählt; nur dort gibt es Leximax
SEED_MAX, DEFAULT_SEED = 999999, 358          # Seed 358 mit ganzen Zahlen und n = 4: das Handbeispiel
TIE_SEED_MAX, DEFAULT_TIE_SEED = 999999, 1000
FAMILIES = ("Ganze Zahlen 1 bis 9", "Gleichverteilt 0 bis 100", "Mit Personeneffekt", "Schwerer Schwanz (log-normal)")
FAMILY_KEYS = ("int", "real", "person", "heavy")
DEFAULT_FAMILY = 0
LOGNORMAL_MEAN, LOGNORMAL_SIGMA = 3.0, 1.0    # Familie „Schwerer Schwanz“

SWEEP_SEEDS = tuple(range(100000, 100020))    # feste Instanzen für alle Sweeps: nie ein einzelner Seed als Befund
TIE_SWEEP_SEEDS = tuple(range(1000, 1005))    # Gleichstands-Seeds je Instanz im Sweep (Median je Instanz)
BAND_SIZES = (10, 20, 50, 100, 200)           # Instanzgrößen der Bänder (Löser)
LEX_SIZES = (6, 7, 8)                         # Instanzgrößen der Bänder für Leximax (aufgezählt)
DOM_SIZES = (10, 50, 200)                     # Instanzgrößen der Dominanz- und Reichweitenzählung
PRICE_LIMIT = 0.05                            # „teuer“: mehr als 5 % Mehrkosten

P_VALUES = (1.0, 1.5, 2.0, 3.0, 5.0, 10.0, 20.0, math.inf)
PLAN_KEYS = ("sum", "sumsq", "max", "maxrand", "leximax")
FAIR_KEYS = ("sumsq", "max", "maxrand", "leximax")
PLAN_NAMES = {
    "sum": "Summe (effizient)",
    "sumsq": "Quadratsumme",
    "max": "Maximum, dann Summe",
    "maxrand": "Maximum, zufälliger Gleichstand",
    "leximax": "Leximax",
}
TOL = 1e-9                                    # Gleichstände: absolut
REL_TOL = 1e-12                               # Gleichstände bei Potenzsummen: relativ

COLOR_SUM = "#2F6B65"
COLOR_SUMSQ = "#4c78a8"
COLOR_MAX = "#c0504d"
COLOR_RAND = "#d8a13a"
COLOR_LEX = "#7b5ea7"
COLOR_OTHER = "rgba(150,150,150,0.35)"
PLAN_COLORS = {"sum": COLOR_SUM, "sumsq": COLOR_SUMSQ, "max": COLOR_MAX, "maxrand": COLOR_RAND, "leximax": COLOR_LEX}
PLAN_SYMBOLS = {"sum": "circle", "sumsq": "square", "max": "diamond", "maxrand": "x", "leximax": "star"}

PRESETS = {
    "Handbeispiel (n = 4, ganze Zahlen)": {"n": 4, "family": 0, "seed": 358, "tie_seed": 1000},
    "Kein Konflikt (n = 50, ganze Zahlen)": {"n": 50, "family": 0, "seed": 0, "tie_seed": 1000},
    "Gleichstand kostet viel (n = 50)": {"n": 50, "family": 1, "seed": 26, "tie_seed": 1000},
    "Teurer Gewinn (schwerer Schwanz, n = 8)": {"n": 8, "family": 3, "seed": 110, "tie_seed": 1000},
    "Leximax zahlt mehr (n = 8, Personeneffekt)": {"n": 8, "family": 2, "seed": 44, "tie_seed": 1000},
    "Quadrat vergrößert das Maximum (n = 20)": {"n": 20, "family": 1, "seed": 100001, "tie_seed": 1000},
    "Viele Personen (n = 100, Personeneffekt)": {"n": 100, "family": 2, "seed": 3, "tie_seed": 1000},
}
PRESET_HELP = {
    "Handbeispiel (n = 4, ganze Zahlen)": "Vier Personen, vier Aufgaben: der faire Plan kostet Summe und bringt am Maximum.",
    "Kein Konflikt (n = 50, ganze Zahlen)": "Hier wählt „Maximum, dann Summe“ denselben Plan wie die Summe: Fairness kostet nichts und bringt nichts. Nur der zufällige Gleichstand zahlt.",
    "Gleichstand kostet viel (n = 50)": "Derselbe Engpass, einmal mit zufälligem Gleichstand und einmal mit „dann kleinste Summe“: der Preis unterscheidet sich deutlich (Median gleichverteilt, n = 10: 0,4 gegen 12,5 %).",
    "Teurer Gewinn (schwerer Schwanz, n = 8)": "Ein Fall, in dem der faire Plan rund 29 % mehr Summe kostet.",
    "Leximax zahlt mehr (n = 8, Personeneffekt)": "Leximax (volle Max-Min-Fairness) weicht vom Plan „Maximum, dann Summe“ ab und kostet mehr Summe.",
    "Quadrat vergrößert das Maximum (n = 20)": "Das Quadrat-Optimum hat ein größeres Maximum als das Summen-Optimum.",
    "Viele Personen (n = 100, Personeneffekt)": "Zu groß zum Aufzählen: exakte Löser; der Gewinn am Maximum ist groß, der Preis klein.",
}
