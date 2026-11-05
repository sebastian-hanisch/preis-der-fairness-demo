# Preis der Fairness – Streamlit-Demo

<!-- TODO nach dem Deploy: direkt hierher den Live-Link setzen (Leerzeile davor und danach):
**[→ Demo live ausprobieren](https://sebastianhanisch-preis-der-fairness-demo.streamlit.app/)** -->

Stück 2 der Linie **Zielfunktionsdesign** („Das Ziel ist das Modell“) in der „Konzepte“-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“ (Arbeitsname; Name, Bereich und Themenfeld werden erst bei der Einbindung in die Website festgelegt). Es baut auf Stück 1 auf (`zielvergleich-demo`): dieselbe Zuordnung, dieselbe Belastungsmatrix, dieselben drei ersten Instanzfamilien. Das Beispiel: **n Personen übernehmen n Aufgaben**, jede Paarung hat eine Belastung. Der **effiziente** Plan hat die kleinste Summe; ein **fairer** Plan senkt das Maximum und zahlt dafür mit Summe. Die Demo misst beides in Prozent. Alles ist **simuliert**; keine Aussage über echte Personen, Betriebe oder Lasten.

## Warum dieses Problem

„Fair“ klingt nach einer Eigenschaft, ist aber ein Ziel, und ein Ziel hat einen Preis. Die Demo fragt: **Was kostet ein fairerer Plan an Summe, und was bringt er am Maximum?** Sie beantwortet es für vier faire Pläne und zeigt, dass der Preis weniger an der Fairness hängt als an einer Kleinigkeit: der **Regel für Gleichstände** beim Maximum.

## Modell

Gegeben Belastungen `c[i][j]` (Zeile Person, Spalte Aufgabe). Ein Plan ist eine Permutation `π`; Person `i` trägt `b_i = c[i][π(i)]`. `S = Σ b_i` ist die Summe, `M = max b_i` das Maximum. Der effiziente Plan minimiert `S`. Für einen Plan `π`:

- **Preis** = `S(π) / S(effizient) − 1` (Mehrkosten der Summe in Prozent),
- **Gewinn** = `1 − M(π) / M(effizient)` (Rückgang des Maximums in Prozent; negativ, wenn das Maximum wächst).

Faire Pläne: **Quadratsumme** (`Σ b_i²`), **Maximum, dann Summe** (kleinstes Maximum, unter allen Plänen damit die kleinste Summe), **Maximum mit zufälligem Gleichstand** (derselbe Engpass, aber unter den gleich guten Plänen gewinnt der mit der kleinsten Summe reeller Zufallszusatzkosten; fester Seed, damit reproduzierbar) und **Leximax** (den absteigend sortierten Belastungsvektor lexikographisch minimieren; aufgezählt nur bis n = 8). Dazu die **p-Familie** `Σ b_i^p` für p = 1 bis ∞. Die **untere Schranke** des Maximums ist `max_i min_j c[i][j]`: die zäheste Person trägt mindestens ihre billigste Aufgabe. Formeln stehen im 📐-Expander der App.

**Preis ist hier nicht der Preis der Fairness von Bertsimas, Farias und Trichakis (2011).** Deren Maß gilt für Nutzen (Maximierung), liegt zwischen 0 und 1 und hat Schranken, die nur von der Spielerzahl abhängen, für **konvexe** Nutzenmengen. Die Zuordnung ist diskret, die Schranken gelten hier nicht; die Demo misst Mehrkosten und nennt sie „Preis“ nur in Anlehnung an die Arbeit.

## Methodik

Vier Instanzfamilien: **ganze Zahlen 1 bis 9** (viele Gleichstände), **gleichverteilt 0 bis 100**, **mit Personeneffekt** (manche Personen sind systematisch stärker belastet) und **schwerer Schwanz** (log-normal, wenige sehr große Belastungen). Bis n = 8 werden alle Pläne aufgezählt (und Leximax gerechnet), darüber rechnen die Ungarische Methode (Summe, Quadratsumme, p) und ein Engpassverfahren (Maximum) das Optimum **exakt**. Die App zeigt: Belastungsmatrix mit Plänen, Tabelle der Pläne mit Preis und Gewinn, die Preis-Gewinn-Karte, die Gleichstandsregel (zwei Gleichstandsregeln gegeneinander), den p-Regler, Bänder über 20 feste Instanzen je Instanzgröße und die untere Schranke. Verdikte entstehen live aus der Rechnung, jede Zahl im Text kommt aus dem Ergebnis.

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen stammen aus den Auswertungsfunktionen der App und sind in `tests/test_claims.py` nachgerechnet. „Je 20 feste Instanzen“ heißt `SWEEP_SEEDS` (Seeds 100000 bis 100019), nie ein einzelner Seed; die Zahlen sind **Mediane und Spannen über Instanzen**, kein Satz und keine Aussage über andere Instanzen. Größen n = 10 / 20 / 50 / 100 / 200, soweit nicht anders angegeben.

| Frage | Befund |
|---|---|
| Handbeispiel (n = 4, ganze Zahlen, Seed 358; 24 Pläne) | Quadratsumme: Preis **7,1 %**, Gewinn **14,3 %**; Maximum, dann Summe: Preis **14,3 %**, Gewinn **28,6 %** (Summe 16 statt 14, Maximum 5 statt 7); das Maximum 5 ist die untere Schranke, Leximax ist derselbe Plan |
| Preis von „Maximum, dann Summe“ (Median) | gleichverteilt **0,4 / 2,3 / 3,0 / 1,9 / 0,6 %**, Personeneffekt **4,2 / 2,3 / 1,4 / 0,9 / 0,6 %**, schwerer Schwanz **0,8 / 1,9 / 0,9 / 1,1 / 0,9 %**, ganze Zahlen **0,0 / 0,0 / 0,0 / 0,0 / 0,0 %**: meist klein, **fällt aber nicht in jeder Familie mit n** |
| Größter Preis unter den 20 Instanzen („Maximum, dann Summe“) | gleichverteilt **17,0 / 25,6 / 14,2 / 8,6 / 5,0 %**, schwerer Schwanz **37,1 / 6,9 / 4,2 / 3,1 / 2,9 %**: Spitzen sind groß |
| Preis desselben Engpasses mit zufälligem Gleichstand (Median) | gleichverteilt **12,5 / 39,6 / 54,1 / 60,2 / 90,9 %**, Personeneffekt **16,1 / 21,0 / 23,9 / 22,9 / 22,2 %**, schwerer Schwanz **14,1 / 21,1 / 31,4 / 31,7 / 32,6 %**; größter Einzelwert 218,7 % (gleichverteilt, n = 50) |
| Instanzen mit Preis über 5 % (gleichverteilt) | mit zufälligem Gleichstand **15 / 19 / 20 / 20 / 20** von 20, mit der Regel „dann Summe“ **8 / 7 / 4 / 3 / 1** von 20 |
| Gewinn am Maximum (Median, „Maximum, dann Summe“) | gleichverteilt **2,5 / 12,4 / 16,3 / 21,0 / 9,1 %**, Personeneffekt **12,9 / 11,2 / 19,1 / 20,9 / 24,3 %**, schwerer Schwanz **0,5 / 8,5 / 9,3 / 16,6 / 15,0 %**; ganze Zahlen: Gewinn null in **13 / 16 / 20 / 20 / 20** von 20 (kein Konflikt) |
| Obergrenze des Gewinns: untere Schranke (zäheste Person) | der Engpassplan erreicht sie in (n = 10 / 50 / 200) gleichverteilt **8 / 6 / 9**, Personeneffekt **17 / 16 / 15**, schwerer Schwanz **9 / 12 / 7**, ganze Zahlen **14 / 20 / 20** von 20; darunter gewinnt kein Plan |
| „Maximum, dann Summe“ dominiert das Quadrat (Preis und Gewinn mindestens gleich gut, in einem besser; n = 10 / 50 / 200) | gleichverteilt **1 / 7 / 18**, Personeneffekt **4 / 12 / 20**, schwerer Schwanz **2 / 10 / 4**, ganze Zahlen **0 / 0 / 0** von 20; das **Quadrat dominiert in 0 von 240** Instanzen |
| Quadrat kann das Maximum vergrößern | gleichverteilt, n = 20: der kleinste Gewinn des Quadrats unter den 20 Instanzen ist **−4,1 %** (Preset „Quadrat vergrößert das Maximum“) |
| Leximax (aufgezählt, n = 6 / 7 / 8; Preis, Median) | gleichverteilt **0,0 / 0,0 / 6,7 %**, Personeneffekt **4,0 / 5,5 / 5,7 %**, schwerer Schwanz **1,3 / 0,6 / 1,0 %**; Preis über 5 % bei Personeneffekt in **9 / 10 / 12** von 20 |
| Preset „Gleichstand kostet viel“ (n = 50, gleichverteilt, Seed 26) | zufälliger Gleichstand **142,9 %**, „dann kleinste Summe“ **1,2 %**; Gewinn beider **23,5 %** |
| Preset „Teurer Gewinn“ (n = 8, schwerer Schwanz, Seed 110) | Preis **28,9 %**, Gewinn **14,4 %** |
| Preset „Leximax zahlt mehr“ (n = 8, Personeneffekt, Seed 44) | Leximax **15,6 %** Preis, „Maximum, dann Summe“ **5,9 %**, beide Gewinn **6,1 %**; die Optimalmenge beim Maximum hat **1356** Pläne |
| Preset „Viele Personen“ (n = 100, Personeneffekt, Seed 3), p = 1,5 / 2 / 3 / 5 / 10 / 20 / ∞ | Preis **0,8 / 1,2 / 1,9 / 2,5 / 4,3 / 5,0 / 0,8 %**: der Preis **fällt bei ∞** (das Maximum mit der Regel „dann Summe“ ist nicht der Grenzwert der p-Optima); Gewinn **8,0 / 10,1 / 10,1 / 16,5 / 17,8 / 18,6 / 18,6 %** |
| Preset „Kein Konflikt“ (n = 50, ganze Zahlen, Seed 0) | Preis und Gewinn von „Maximum, dann Summe“ null; zufälliger Gleichstand dennoch **35,3 %** |

**Korrektur der Planungshypothese:** Vor der Messung stand die Vermutung „der Preis ist klein und fällt mit n“. Die Messung stützt nur den ersten Teil; mit n fällt er bei Personeneffekt, in den anderen Familien nicht eindeutig (die Demo behauptet keinen Trend).

## Ehrliche Grenzen

- **Vier Familien, nicht die Welt:** Wie groß der Preis ist, hängt an der Familie; echte Belastungen können sich anders verhalten. „Schwerer Schwanz“ ist ein einfacher Generator (log-normal, Mittel 3, Streuung 1).
- **Gleichstandsregel gestaltet das Ergebnis:** Der „zufällige“ Gleichstand ist ein Rechenmodell der Willkür, kein gleichverteiltes Ziehen aus der Optimalmenge (Zufallszusatzkosten).
- **Leximax nur bis n = 8:** Es wird aufgezählt; für größere n bräuchte es ein sequenzielles Verfahren, das hier fehlt.
- **Fair heißt hier: das Maximum senken.** Andere Fairnessbegriffe (proportional, nach Bedarf, Neidfreiheit) wählen andere Pläne.
- **Keine Schranke aus der Literatur:** Die Sätze von Bertsimas, Farias und Trichakis gelten für konvexe Nutzenmengen und gelten für die diskrete Zuordnung nicht; die Demo übernimmt keine Zahl daraus.
- **Spannen, keine Trends:** Je 20 Instanzen; Median und Spanne zeigen, was in diesen Instanzen geschieht, nicht was in anderen geschieht.

## Verifikation

Insgesamt 306 Tests (`pytest tests/`), alle grün.

- **Kern:** Handbeispiel von Hand (Preis und Gewinn aller Pläne), eine Matrix, an der Leximax und „Maximum, dann Summe“ verschiedene Pläne wählen, n = 2 von Hand; Optima gegen reines Python (itertools, ohne numpy) und `scipy.optimize.linear_sum_assignment`; Löser (Ungarische Methode, Schwellwertsuche mit Matching) gegen die Aufzählung bis n = 8; der zufällige Gleichstand liegt in der Optimalmenge; unabhängiger Zulässigkeitsprüfer.
- **Eigenschaften:** Preis nie negativ, Gewinn der Engpasspläne nie negativ, alle Engpasspläne mit demselben Gewinn und geordneten Preisen („dann Summe“ ≤ Leximax, ≤ zufällig), Gewinn nie über der Grenze der unteren Schranke, Skalierung, Zeilen- und Spaltenpermutation, eine addierte Konstante senkt den Preis des Engpassplans nie, Determinismus.
- **Randfälle:** n = 1, n = 2, alle Einträge gleich, viele Gleichstände, Seed 0 und größter Seed, n = 200 (ohne Leximax), ganze Zahlen ohne Konflikt.
- **Verdikte:** reine Funktionen, jede Verzweigung und jede Zahl im Text an handgesetzten Werten (`tests/test_verdicts.py`), kein Trendwort in den Bänderverdikten.
- **Presets:** Vollständigkeit, Werte innerhalb der Reglergrenzen, Standard-Preset gleich Standardeinstellung, und dass jedes Preset zeigt, was sein Name sagt.
- **Oberfläche:** AppTest-Rauchtest (jeder Button, jeder Regler am Minimum und Maximum, n = 200), jede Auswahl des fairen Plans, jede p-Stufe und jedes Preset, Footer-Test, Layout (Schnellstart in der Seitenleiste, fester Kopf, aktives Preset hervorgehoben, jede Änderung eines Reglers hebt die Markierung auf).
- **Claims:** jede Zahl dieser README in `tests/test_claims.py`.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App |
| `requirements-dev.txt` | Laufzeit plus pytest |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt) |
| `fpr_algorithm.py` | Kern: Aufzählung, Ungarische Methode, Engpassverfahren, Leximax, zufälliger Gleichstand, Preis und Gewinn, Zulässigkeitsprüfer |
| `fpr_constants.py` | Regler-Grenzen, feste Annahmen, Farben, Presets |
| `fpr_evaluation.py` | Kennzahlen, Verdikte, Sweeps über feste Instanzen |
| `fpr_layout.py` | Fester Kopf (Stylesheet) |
| `fpr_pdf_export.py` | PDF-Export des Ergebnisses |
| `fpr_presets.py` | Permalink (Begrenzen), Presets (Schnellstart in der Seitenleiste), Zufalls-Seed-Buttons |
| `fpr_scenario.py` | Instanzen (vier Familien) |
| `fpr_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `tests/` | Handbeispiel, Gegenproben, Eigenschaften, Randfälle, Verdikte, Presets, Claims, Layout, AppTest-Smoke-Test, Footer, Laufzeit-Importe, Orakel |

## Bewusst nicht umgesetzt

- **Keine Pareto-Front, keine Gewichtssumme:** Zwei Kriterien und die Frage, welche Kompromisse eine Gewichtssumme erreicht, sind Stück 3.
- **Keine Lexikographik mit Gewicht, keine Toleranz:** Hier gilt die Regel „erst Maximum, dann Summe“ nur als sichtbare Gleichstandsregel; ihre Tücken sind Stück 4 und 5.
- **Keine Zufallspläne:** Eine zufällige Zuordnung (Erwartungsbelastung) wäre konvex, dort griffen die Schranken von Bertsimas, Farias und Trichakis; das wäre ein eigenes Stück.
- **Keine α-Familie der Fairness als Behauptung:** Die p-Familie dieser Demo ist eine Familie von Kostenzielen für die Zuordnung, nicht die α-Familie für Nutzen in Netzwerken.
- **Kein Leximax für große n.**

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly, NumPy und SciPy.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html).
