"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

import plotly.graph_objects as go
from plotly.subplots import make_subplots

import fpr_constants as C
from fpr_evaluation import p_label

TEXT_MAX_N = 10    # bis hierher stehen die Zahlen in den Zellen der Matrix
MATRIX_KEYS = ("sum", "sumsq", "max")


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=360):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=30, b=10), legend=dict(orientation="h", y=-0.2), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def build_matrix(inst, plans):
    """Belastungsmatrix als Heatmap (Zeile Person, Spalte Aufgabe); die Pläne Summe, Quadratsumme und „Maximum, dann Summe“ als Marken."""
    n = inst.n
    fig = go.Figure(go.Heatmap(z=[list(row) for row in inst.c], x=list(range(1, n + 1)), y=list(range(1, n + 1)), colorscale="Blues", showscale=False,
                               text=[[f"{v:.0f}" for v in row] for row in inst.c] if n <= TEXT_MAX_N else None,
                               texttemplate="%{text}" if n <= TEXT_MAX_N else None, hovertemplate="Person %{y}, Aufgabe %{x}: %{z:.1f}<extra></extra>"))
    offsets = {"sum": -0.22, "sumsq": 0.0, "max": 0.22}
    for g in MATRIX_KEYS:
        plan = plans[g].plan
        fig.add_trace(go.Scatter(x=[j + 1 + (offsets[g] if n <= TEXT_MAX_N else 0) for j in plan], y=[i + 1 for i in range(n)], mode="markers",
                                 marker=dict(symbol=C.PLAN_SYMBOLS[g], size=14 if n <= TEXT_MAX_N else 7, color=C.PLAN_COLORS[g], line=dict(width=1, color="white")),
                                 name=C.PLAN_NAMES[g], hovertemplate=C.PLAN_NAMES[g] + ": Person %{y} → Aufgabe %{x}<extra></extra>"))
    fig.update_xaxes(title_text="Aufgabe", dtick=1 if n <= 20 else None, side="top")
    fig.update_yaxes(title_text="Person", autorange="reversed", dtick=1 if n <= 20 else None)
    return _base(fig, height=420 if n <= TEXT_MAX_N else 520)


def build_price_gain_map(points):
    """Preis-Gewinn-Karte: ein Punkt je Plan (x Preis in %, y Gewinn in %); das Summen-Optimum liegt im Ursprung.

    `points`: Liste (Plan-Schlüssel, Preis als Anteil, Gewinn als Anteil)."""
    fig = go.Figure()
    for rank, (key, price, gain) in enumerate(points):
        # Zusammenfallende Pläne liegen übereinander: spätere Marken sind kleiner und sitzen in den früheren, so bleibt jede sichtbar.
        size = max(9, 20 - 3 * rank)
        fig.add_trace(go.Scatter(x=[price * 100], y=[gain * 100], mode="markers",
                                 marker=dict(symbol=C.PLAN_SYMBOLS[key], size=size, color=C.PLAN_COLORS[key], line=dict(width=1, color="white")),
                                 name=C.PLAN_NAMES[key], hovertemplate=C.PLAN_NAMES[key] + ": Preis %{x:.1f} %, Gewinn %{y:.1f} %<extra></extra>"))
    fig.add_hline(y=0, line=dict(color="rgba(120,120,120,0.5)", dash="dot", width=1))
    fig.update_xaxes(title_text="Preis: Mehrkosten der Summe in % (links besser)", rangemode="tozero")
    fig.update_yaxes(title_text="Gewinn: Rückgang des Maximums in % (oben besser)")
    return _base(fig, height=400)


def build_tie_bars(a):
    """Derselbe Engpass, zwei Gleichstandsregeln: Preis in % (Balken) und Gewinn in % (Balken)."""
    keys = ("maxrand", "max")
    fig = make_subplots(rows=1, cols=2, subplot_titles=("Preis (Mehrkosten der Summe)", "Gewinn (Rückgang des Maximums)"))
    for key in keys:
        fig.add_trace(go.Bar(x=[C.PLAN_NAMES[key]], y=[a.price(key) * 100], marker_color=C.PLAN_COLORS[key], showlegend=False,
                             hovertemplate="%{y:.1f} %<extra></extra>"), row=1, col=1)
        fig.add_trace(go.Bar(x=[C.PLAN_NAMES[key]], y=[a.gain(key) * 100], marker_color=C.PLAN_COLORS[key], showlegend=False,
                             hovertemplate="%{y:.1f} %<extra></extra>"), row=1, col=2)
    fig.update_yaxes(title_text="Prozent", row=1, col=1)
    return _base(fig, height=320)


def build_p_curves(rows):
    """Preis und Gewinn über p (Text-Achse, damit ∞ und 1,5 gleich breit stehen); der Sprung bei ∞ ist der Befund."""
    xs = [p_label(r["p"]) for r in rows]
    fig = make_subplots(rows=1, cols=2, subplot_titles=("Preis: Mehrkosten der Summe in %", "Gewinn: Rückgang des Maximums in %"))
    fig.add_trace(go.Scatter(x=xs, y=[r["price"] * 100 for r in rows], mode="lines+markers", line=dict(color=C.COLOR_SUM, width=3), showlegend=False,
                             hovertemplate="p = %{x}: %{y:.1f} %<extra></extra>"), row=1, col=1)
    fig.add_trace(go.Scatter(x=xs, y=[r["gain"] * 100 for r in rows], mode="lines+markers", line=dict(color=C.COLOR_MAX, width=3), showlegend=False,
                             hovertemplate="p = %{x}: %{y:.1f} %<extra></extra>"), row=1, col=2)
    fig.update_xaxes(title_text="p", type="category")
    return _base(fig, height=320)


def build_bands(rows, fair):
    """Spannen über die festen Instanzen je Instanzgröße: Punkt = Median, Balken = Min bis Max (Preis links, Gewinn rechts)."""
    xs = [f"n = {r['n']}" for r in rows]
    fig = make_subplots(rows=1, cols=2, subplot_titles=("Preis in % (Median, Spanne Min bis Max)", "Gewinn in % (Median, Spanne Min bis Max)"))
    for col, key, color in ((1, "price", C.PLAN_COLORS[fair]), (2, "gain", C.COLOR_SUM)):
        med = [r[key][1] * 100 for r in rows]
        up = [(r[key][2] - r[key][1]) * 100 for r in rows]
        down = [(r[key][1] - r[key][0]) * 100 for r in rows]
        fig.add_trace(go.Scatter(x=xs, y=med, mode="markers", marker=dict(size=11, color=color), showlegend=False,
                                 error_y=dict(type="data", symmetric=False, array=up, arrayminus=down, color=color, thickness=2, width=6),
                                 hovertemplate="Median %{y:.1f} %<extra></extra>"), row=1, col=col)
    fig.add_hline(y=0, line=dict(color="rgba(120,120,120,0.5)", dash="dot", width=1))
    fig.update_xaxes(type="category")
    return _base(fig, height=340)


def build_reach(a):
    """Maximum des Summen-Optimums, des Plans „Maximum, dann Summe“ und die untere Schranke (zäheste Person)."""
    labels = ["Summen-Optimum", "Maximum, dann Summe", "untere Schranke"]
    values = [a.plans["sum"].peak, a.plans["max"].peak, a.lower]
    fig = go.Figure(go.Bar(x=labels, y=values, marker_color=[C.COLOR_SUM, C.COLOR_MAX, "rgba(120,120,120,0.8)"], showlegend=False,
                           hovertemplate="%{x}: %{y:.1f}<extra></extra>"))
    fig.update_yaxes(title_text="Maximum der Belastungen", range=[0, max(values) * 1.12])
    return _base(fig, height=300)
