"""PDF-Export des aktuellen Ergebnisses (fpdf2). Kernschriften sind latin-1: Umlaute gehen, Sonderzeichen werden ersetzt."""

from __future__ import annotations

from fpdf import FPDF

import fpr_constants as C
from fpr_evaluation import Analysis, Settings, de, pct

_REPLACE = {"→": "->", "–": "-", "—": "-", "−": "-", "≤": "<=", "≥": ">=", "·": "*", "×": "x", "Δ": "Delta", "↔": "<->", "„": '"', "“": '"', "²": "2", "∞": "unendlich"}


def _s(text) -> str:
    out = str(text).replace("**", "").replace("`", "")
    for old, new in _REPLACE.items():
        out = out.replace(old, new)
    return out.encode("latin-1", "replace").decode("latin-1")


def build_pdf(s: Settings, a: Analysis) -> bytes:
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 15)
    pdf.cell(0, 9, _s("Preis der Fairness"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 5, _s(f"{s.n} Personen, {s.n} Aufgaben, Familie: {C.FAMILIES[s.family]}, Seed {s.seed}, Gleichstands-Seed {s.tie_seed}. Alles simuliert."),
                   new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    widths = (58, 30, 30, 32, 32)
    head = ("Plan", "Summe", "Maximum", "Preis", "Gewinn")
    pdf.set_font("Helvetica", "B", 9)
    for w, h in zip(widths, head):
        pdf.cell(w, 6, _s(h), border=1)
    pdf.ln()
    pdf.set_font("Helvetica", "", 9)
    for key in C.PLAN_KEYS:
        if key not in a.plans:
            continue
        r = a.plans[key]
        for w, v in zip(widths, (C.PLAN_NAMES[key], de(r.total), de(r.peak), pct(a.price(key)), pct(a.gain(key)))):
            pdf.cell(w, 5.5, _s(v), border=1)
        pdf.ln()
    pdf.ln(3)
    pdf.set_font("Helvetica", "I", 8)
    pdf.multi_cell(0, 4, _s("Preis: Mehrkosten der Summe gegen das Summen-Optimum in Prozent; Gewinn: Rückgang des Maximums in Prozent. "
                            f"Untere Schranke des Maximums (zäheste Person): {de(a.lower)}. Gleichstand beim Maximum: erst kleinstes Maximum, dann kleinste Summe, "
                            "oder zufällig (Seed). Quelle: preis-der-fairness-demo, Sebastian Hanisch."), new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())
