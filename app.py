"""Preis der Fairness - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Stück 2 der Reihe „Zielfunktionsdesign“: dieselbe Zuordnung wie in Stück 1 (n Personen, n Aufgaben, Belastung je Paar). Ein fairer Plan kostet Summe
und bringt am Maximum; die Demo misst beides in Prozent gegen das Summen-Optimum, für vier faire Pläne, und zeigt, woran der Preis hängt.

Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import fpr_constants as C
from fpr_evaluation import (
    Settings,
    analyse,
    band_rows,
    de,
    dominance_rows,
    p_label,
    p_rows,
    pct,
    reach_rows,
    verdict_band,
    verdict_dominance,
    verdict_p,
    verdict_prices,
    verdict_reach,
    verdict_tie,
)
from fpr_layout import dunkles_design, kopf_css
from fpr_pdf_export import build_pdf
from fpr_presets import (
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    randomize_tie_seed,
    sidebar_presets,
    sync_query_params,
)
from fpr_visualization import build_bands, build_matrix, build_p_curves, build_price_gain_map, build_reach, build_tie_bars

st.set_page_config(page_title="Preis der Fairness – Sebastian Hanisch", layout="wide")

BAND_CHOICES = {"Quadratsumme": "sumsq", "Maximum, dann Summe": "max", "Maximum, zufälliger Gleichstand": "maxrand", "Leximax (n = 6 bis 8, aufgezählt)": "leximax"}


@st.cache_data(show_spinner=False)
def _analysis(settings):
    return analyse(settings)


@st.cache_data(show_spinner=False)
def _p_rows(settings):
    return p_rows(settings)


@st.cache_data(show_spinner=False)
def _bands(family, fair):
    return band_rows(family, fair)


@st.cache_data(show_spinner=False)
def _dominance(family):
    return dominance_rows(family)


@st.cache_data(show_spinner=False)
def _reach(family):
    return reach_rows(family)


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in fpr_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("⚖️ Preis der Fairness")
st.markdown(
    """
**Was kostet ein fairerer Plan?** Dieselbe Aufgabe wie in Stück 1: **n Personen** übernehmen **n Aufgaben**, jede Paarung hat eine Belastung.
Der **effiziente** Plan hat die kleinste **Summe**. Ein **fairer** Plan senkt die Belastung der am stärksten Belasteten, das **Maximum**, und zahlt dafür mit Summe.
Die Demo misst beides in Prozent: den **Preis** (Mehrkosten der Summe) und den **Gewinn** (Rückgang des Maximums), für vier faire Pläne, und zeigt, woran der Preis hängt.

Wer das Thema zuerst ohne Fachbegriffe verstehen will, öffnet „💬 In einfachen Worten“.

Weiter unten: **🔬 Preis und Gewinn der Pläne**, **🔬 Was die Gleichstandsregel kostet**, **🔬 Der p-Regler**, **🔬 Wie groß ist der Preis?**, **🔬 Wie weit reicht der Gewinn?**,
**🚧 Wo die Annahmen enden** und der Expander **📐 Mathematische Formulierung**.
"""
)

# erklaerseite:einfach:start (erzeugt von tools/set_demo_explainer.py (Website-Repo) aus tools/content/explainers/preis-der-fairness-erklaert.json, nicht von Hand ändern)
with st.expander("💬 In einfachen Worten"):
    st.markdown(
        """
Stellen Sie sich vor, ein Team verteilt Aufgaben auf Personen. Der sparsamste Plan hält die Belastung aller zusammen so klein wie möglich, kann aber eine Person stark belasten. Ein fairerer Plan senkt die Belastung der am stärksten Belasteten und nimmt dafür in Kauf, dass die Belastung aller zusammen wächst. Die Demo misst beides in Prozent: die Mehrbelastung als Preis und die Entlastung der am stärksten Belasteten als Gewinn.

Es kann mehrere Pläne geben, die für die am stärksten belastete Person gleich gut sind. Welchen davon man nimmt, bestimmt den Preis: Entscheidet der Zufall, kann er hoch ausfallen. Wählt man unter den gleich guten Plänen den mit der kleinsten Gesamtbelastung, bleibt er in den Messungen der Demo klein. Alle Belastungen sind erfunden.

[Ausführlich und verständlich erklärt, mit Fachteil](https://sebastianhanisch.net/preis-der-fairness-erklaert.html)
        """
    )
# erklaerseite:einfach:end

with st.expander("So funktioniert die Preis-Gewinn-Rechnung", expanded=True):
    st.markdown(
        """
1. **Der effiziente Plan** hat die kleinste Summe der Belastungen. Er ist der Maßstab: Preis und Gewinn sind Abstände zu ihm.
2. **Der Preis** eines Plans: um wie viel Prozent ist seine Summe größer als die des effizienten Plans? **Der Gewinn:** um wie viel Prozent ist sein Maximum kleiner?
3. **Vier faire Pläne:** die **Quadratsumme** (Ausreißer zählen mehr), das **Maximum, dann Summe** (erst das kleinste Maximum, unter allen Plänen damit die kleinste Summe),
   das **Maximum mit zufälligem Gleichstand** (derselbe Engpass, aber unter den gleich guten Plänen entscheidet der Zufall) und **Leximax** (zuerst das Maximum, dann die zweitgrößte Belastung, und so weiter; nur bis n = 8).
4. **Warum der Gleichstand zählt:** Beim Maximum gibt es oft viele gleich gute Pläne. Welchen man nimmt, bestimmt den Preis, nicht die Fairness.
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Instanz**")
    n = st.slider("Personen und Aufgaben n", *bounds("n_slider"), key="n_slider", help=f"Bis n = {C.ENUM_MAX} werden alle Pläne aufgezählt (und Leximax gerechnet); darüber rechnen exakte Löser.")
    family = st.selectbox("Art der Belastungen", list(range(len(C.FAMILIES))), key="family_select", format_func=lambda i: C.FAMILIES[i],
                          help="Ganze Zahlen haben viele Gleichstände; „Mit Personeneffekt“: manche Personen sind systematisch stärker belastet; „Schwerer Schwanz“: wenige sehr große Belastungen.")
    seed = st.number_input("Zufalls-Seed der Instanz", *bounds("seed_input"), key="seed_input", step=1)
    st.button("🎲 Neue Instanz generieren", width="stretch", on_click=randomize_seed)
    st.markdown("**Gleichstand**")
    tie_seed = st.number_input("Gleichstands-Seed", *bounds("tie_seed_input"), key="tie_seed_input", step=1,
                               help="Entscheidet beim „Maximum, zufälliger Gleichstand“, welcher der gleich guten Engpasspläne gewählt wird.")
    st.button("🎲 Anderer Gleichstand", width="stretch", on_click=randomize_tie_seed)

sync_query_params({"n_slider": int(n), "family_select": int(family), "seed_input": int(seed), "tie_seed_input": int(tie_seed)})

settings = Settings(int(n), int(family), int(seed), int(tie_seed))
a = _analysis(settings)
sum_r, max_r = a.plans["sum"], a.plans["max"]

# --- Ergebnis ------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Ergebnis: der faire Plan gegen den effizienten")
m1, m2, m3 = st.columns(3)
# Delta immer als „mein Wert minus Referenz“; die Farbe regelt delta_color="inverse" (Vorzeichen-Falle, DEMO-PLAYBOOK §2).
m1.metric("Summe im effizienten Plan (kleinstmöglich)", de(sum_r.total), delta="Referenz", delta_color="off")
m2.metric("Preis von „Maximum, dann Summe“", pct(a.price("max")), delta=f"{max_r.total - sum_r.total:+.1f} Summe".replace(".", ","), delta_color="inverse")
m3.metric("Gewinn von „Maximum, dann Summe“", pct(a.gain("max")), delta=f"{max_r.peak - sum_r.peak:+.1f} Maximum".replace(".", ","), delta_color="inverse")

rows_md = ["| Plan | Summe | Maximum | Preis | Gewinn |", "|---|---|---|---|---|"]
for key in C.PLAN_KEYS:
    if key in a.plans:
        r = a.plans[key]
        rows_md.append(f"| **{C.PLAN_NAMES[key]}** | {de(r.total)} | {de(r.peak)} | {pct(a.price(key))} | {pct(a.gain(key))} |")
    else:
        rows_md.append(f"| **{C.PLAN_NAMES[key]}** | – | – | – | – |")
st.markdown("\n".join(rows_md))
st.caption("Preis: Mehrkosten der Summe gegen den effizienten Plan; Gewinn: Rückgang des Maximums (negativ: das Maximum wächst). "
           + ("" if a.enumerated else f"Leximax wird nur bis n = {C.ENUM_MAX} gerechnet (aufgezählt). ")
           + "Gleichstand beim Maximum: erst kleinstes Maximum, dann kleinste Summe; „zufällig“ entscheidet der Gleichstands-Seed. "
           + "Bei ganzen Zahlen ist die Referenz nicht eindeutig: Preis und Gewinn hängen davon ab, welcher von mehreren gleich guten Summen-Optimalplänen als Referenz dient.")

st.plotly_chart(build_matrix(a.inst, a.plans), width="stretch", key="matrix_chart")
st.caption("Belastungsmatrix (Zeile Person, Spalte Aufgabe); Marken: Kreis effizienter Plan, Quadrat Quadratsumme, Raute „Maximum, dann Summe“. Je dunkler die Zelle, desto größer die Belastung.")
st.download_button("📄 Ergebnis als PDF", data=build_pdf(settings, a), file_name="preis-der-fairness.pdf", mime="application/pdf", key="pdf_download")

# --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Was kostet der faire Plan, und was bringt er?")
kind, text = verdict_prices(a)
getattr(st, kind)(text)

st.markdown("---")

# --- Experimente ---------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Preis und Gewinn der Pläne")
points = [(key, a.price(key), a.gain(key)) for key in C.PLAN_KEYS if key in a.plans]
st.plotly_chart(build_price_gain_map(points), width="stretch", key="map_chart")
st.caption("Jeder Punkt ist ein Plan: nach links weniger Mehrkosten, nach oben mehr Rückgang des Maximums. Der effiziente Plan liegt im Ursprung. "
           "Pläne, die oben links liegen, sind besser als die rechts darunter. Pläne mit denselben Werten liegen übereinander: die Marken sind ineinander gesetzt.")

st.markdown("---")

st.subheader("🔬 Was die Gleichstandsregel kostet")
st.caption("Beide Pläne haben dasselbe, kleinstmögliche Maximum. Sie unterscheiden sich nur darin, wie sie unter den gleich guten Plänen wählen: "
           "zufällig (Gleichstands-Seed in der Seitenleiste) oder nach der kleinsten Summe.")
st.plotly_chart(build_tie_bars(a), width="stretch", key="tie_chart")
kind, text = verdict_tie(a)
getattr(st, kind)(text)

st.markdown("---")

st.subheader("🔬 Der p-Regler: vom effizienten zum fairen Plan")
st.caption("Ziel: Summe der Belastungen hoch p. p = 1 ist der effiziente Plan, p = 2 die Quadratsumme, p → ∞ strebt zum Maximum; bei „∞“ gilt „Maximum, dann Summe“. "
           "Die Optima werden für jedes p neu gerechnet.")
p_options = [p_label(p) for p in C.P_VALUES]
p_choice = st.select_slider("Exponent p", options=p_options, value="2", key="p_slider")
rows_p = _p_rows(settings)
row = rows_p[p_options.index(p_choice)]
c1, c2 = st.columns(2)
c1.metric("Preis beim gewählten p", pct(row["price"]))
c2.metric("Gewinn beim gewählten p", pct(row["gain"]))
st.plotly_chart(build_p_curves(rows_p), width="stretch", key="p_chart")
kind, text = verdict_p(rows_p)
getattr(st, kind)(text)

st.markdown("---")

st.subheader("🔬 Wie groß ist der Preis?")
fair_label = st.selectbox("Fairer Plan", list(BAND_CHOICES), index=1, key="band_fair")
fair = BAND_CHOICES[fair_label]
st.caption(f"Je {len(C.SWEEP_SEEDS)} feste Instanzen (SWEEP_SEEDS) der gewählten Art, je Instanzgröße; die Zahlen sind Spannen über Instanzen, kein Satz. "
           + ("Beim zufälligen Gleichstand zählt je Instanz der Median über fünf Gleichstands-Seeds." if fair == "maxrand" else ""))
bands = _bands(settings.family, fair)
st.plotly_chart(build_bands(bands, fair), width="stretch", key="band_chart")
kind, text = verdict_band(bands, fair)
getattr(st, kind)(text)
st.markdown("**Maximum, dann Summe gegen Quadratsumme, je Instanz**")
kind, text = verdict_dominance(_dominance(settings.family))
getattr(st, kind)(text)

st.markdown("---")

st.subheader("🔬 Wie weit reicht der Gewinn?")
st.caption("Die zäheste Person, die bei jeder Aufgabe stark belastet ist, legt eine untere Schranke für das Maximum fest: Kein Plan kann darunter liegen.")
st.plotly_chart(build_reach(a), width="stretch", key="reach_chart")
kind, text = verdict_reach(a, _reach(settings.family))
getattr(st, kind)(text)

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Die Belastungen sind bekannt und gelten je Paar unabhängig** | Wechselwirkungen oder Schätzfehler machen aus dem „Optimum“ eine Näherung; Preis und Gewinn sind dann selbst unsicher | Optimierung unter Unsicherheit |
| **„Preis“ heißt hier Mehrkosten in Prozent** | Der Preis der Fairness bei Bertsimas, Farias und Trichakis (2011) misst Nutzen, nicht Kosten, und nimmt eine konvexe Nutzenmenge an; die Zuordnung ist diskret, ihre Schranken sind hier nicht anwendbar, und Mehrkosten haben keine Obergrenze 1 | Literatur; Zufallspläne (Erwartungsbelastung) wären konvex |
| **Die Gleichstandsregel ist gesetzt** | Ohne sie liegt der Preis desselben „fairen“ Plans höher: im Median über je 20 Instanzen in drei Familien (gleichverteilt, n = 10: 0,4 % mit „dann Summe“ gegen 12,5 % mit zufälligem Gleichstand), bei ganzen Zahlen nur an einem Beispiel (Preset „Kein Konflikt“); Toleranz und Gleitkomma gehören zu Stück 4 und 5 | Stück 4 (Lexikographisch), Stück 5 (Gleichstände) |
| **Fair heißt: das Maximum der Belastung senken** | Andere Fairnessbegriffe (proportional, nach Bedarf, Neid) wählen andere Pläne; die Demo zeigt nur diese Auslegung | Wertung und Wahl (Gemeinsam entscheiden) |
| **Die Referenz ist der Summen-Optimalplan** | Bei ganzen Zahlen gibt es oft mehrere gleich gute Summen-Optimalpläne; Preis und Gewinn hängen davon ab, welcher von ihnen als Referenz dient | – |
| **Leximax nur bis n = 8** | Darüber gibt es kein Leximax, nur die p-Familie als Annäherung; die Bänder zu Leximax stehen für n = 6 bis 8 | – |
| **Vier synthetische Familien** | Wie groß der Preis ist, hängt an der Familie; echte Belastungen können sich anders verhalten | – |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    # erklaerseite:lesehilfe:start (erzeugt von tools/set_demo_explainer.py (Website-Repo) aus tools/content/explainers/preis-der-fairness-erklaert.json, nicht von Hand ändern)
    st.markdown(
        r"""
**Lesehilfe.** Gegeben sind $n$ Personen, $n$ Aufgaben und für jede Paarung eine Belastung. Gesucht sind Pläne, die jeder Person genau eine Aufgabe geben, und ihr Abstand zum sparsamsten Plan: der Preis (Mehrkosten der Summe) und der Gewinn (Rückgang der höchsten Belastung).

| Symbol | Bedeutung |
|---|---|
| $n$ | Zahl der Personen und der Aufgaben |
| $c_{ij}$ | Belastung, wenn Person $i$ die Aufgabe $j$ übernimmt |
| $\pi$ | Plan: ordnet jeder Person $i$ eine Aufgabe $\pi(i)$ zu (Permutation) |
| $b_i$ | Belastung, die Person $i$ im Plan $\pi$ trägt |
| $S(\pi)$ | Summe aller getragenen Belastungen |
| $M(\pi)$ | Maximum: die höchste Belastung einer einzelnen Person |
| $\pi^{\Sigma}$ | sparsamster (effizienter) Plan mit der kleinsten Summe |
| $\text{Preis}$, $\text{Gewinn}$ | Mehrkosten der Summe bzw. Rückgang des Maximums gegenüber $\pi^{\Sigma}$ |
| $p$ | Exponent der Zielfunktion $\sum_i b_i^p$ |
| $t$ | Schwelle: kleinster Wert, bei dem ein Plan existiert, in dem keine Belastung über $t$ liegt |

[Schritt für Schritt erklärt, mit Herleitung und Literatur](https://sebastianhanisch.net/preis-der-fairness-erklaert.html#fachleute)
        """
    )
    # erklaerseite:lesehilfe:end
    st.markdown(
        r"""
**Problem.** Gegeben $n$ Personen, $n$ Aufgaben und Belastungen $c_{ij} \ge 0$. Ein Plan ist eine Permutation $\pi$; Person $i$ trägt $b_i = c_{i,\pi(i)}$. Der **effiziente Plan** $\pi^{\Sigma}$ minimiert $S(\pi) = \sum_i b_i$; $M(\pi) = \max_i b_i$.

**Preis und Gewinn** eines Plans $\pi$ gegen $\pi^{\Sigma}$:
$$\text{Preis}(\pi) = \frac{S(\pi)}{S(\pi^{\Sigma})} - 1, \qquad \text{Gewinn}(\pi) = 1 - \frac{M(\pi)}{M(\pi^{\Sigma})}.$$
Der Preis ist nie negativ; der Gewinn ist negativ, wenn das Maximum wächst (beim Quadrat-Optimum möglich).

**Faire Pläne.** Quadratsumme: $\min \sum_i b_i^2$ (allgemein $\min \sum_i b_i^p$, exakt über die Ungarische Methode mit Kosten $c_{ij}^p$). Maximum: kleinste Schwelle $t$, bei der die Kanten mit $c_{ij} \le t$ ein perfektes Matching enthalten; unter allen Plänen mit $M(\pi) = t$ entscheidet entweder die kleinste Summe („dann Summe“) oder die kleinste Summe reeller Zufallszusatzkosten (zufälliger Gleichstand). **Leximax:** der absteigend sortierte Belastungsvektor $b_{(1)} \ge b_{(2)} \ge \dots$ wird lexikographisch minimiert (aufgezählt, $n \le 8$); Pläne mit demselben sortierten Vektor haben dieselbe Summe.

**Untere Schranke.** $M(\pi) \ge \max_i \min_j c_{ij}$ für jeden Plan $\pi$: die zäheste Person trägt mindestens ihre billigste Aufgabe.

**Literatur.** Bertsimas, Farias, Trichakis (2011), „The Price of Fairness“, Operations Research 59(1): Preis der Fairness als relative Effizienzeinbuße gegen den Plan mit der größten Nutzensumme; Schranken, die nur von der Spielerzahl abhängen, für kompakte und konvexe Nutzenmengen. Diese Demo übernimmt keine Schranke und keine Zahl daraus; alle Zahlen sind Messungen an den Instanzfamilien der Demo. Rechenverfahren: Ungarische Methode (Kuhn, 1955; hier nicht an der Quelle geprüft).
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zur Reihe: [Zielfunktionsdesign: das Ziel ist das Modell](https://sebastianhanisch.net/konzepte-zielfunktionsdesign.html)."
)
