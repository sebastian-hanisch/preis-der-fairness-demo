"""Kennzahlen, Verdikt-Logik und Sweeps. Verdikte sind reine Funktionen (Art, Text); jede Zahl im Text kommt aus der Rechnung.

Preis = Mehrkosten der Summe des fairen Plans in Prozent der Summe des Summen-Optimums; Gewinn = Rückgang des Maximums in Prozent des
Maximums des Summen-Optimums (negativ: das Maximum wächst). Beide sind Anteile (0,05 = 5 %) und werden erst in der Anzeige zu Prozent."""

import math
from dataclasses import dataclass

import numpy as np

import fpr_algorithm as A
import fpr_constants as C
from fpr_scenario import Instance, make_instance


def de(x: float, digits: int = 1) -> str:
    """Zahl mit Dezimalkomma."""
    text = f"{x:.{digits}f}"
    if float(text) == 0.0:
        text = f"{0.0:.{digits}f}"                 # kein „-0,0“
    return text.replace(".", ",")


def pct(x: float, digits: int = 1) -> str:
    """Anteil als Prozent mit Dezimalkomma: 0,05 -> „5,0 %“."""
    return de(x * 100.0, digits) + " %"


def p_label(p: float) -> str:
    """Beschriftung des Exponenten: ganze Zahl ohne Komma, ∞ für unendlich."""
    return "∞" if math.isinf(p) else (str(int(p)) if float(p).is_integer() else str(p).replace(".", ","))


@dataclass(frozen=True)
class Settings:
    n: int = C.DEFAULT_N
    family: int = C.DEFAULT_FAMILY
    seed: int = C.DEFAULT_SEED
    tie_seed: int = C.DEFAULT_TIE_SEED


@dataclass(frozen=True)
class Analysis:
    inst: Instance
    plans: dict              # Plan-Schlüssel (C.PLAN_KEYS) -> A.Result; "leximax" nur bei Aufzählung
    lower: float             # untere Schranke des Maximums (zäheste Person)
    plans_total: int | None  # n!, nur bei Aufzählung
    tie_size: int | None     # Optimalmenge des Maximums (vor der zweiten Regel), nur bei Aufzählung
    enumerated: bool

    def price(self, key: str) -> float:
        return A.price(self.plans[key], self.plans["sum"])

    def gain(self, key: str) -> float:
        return A.gain(self.plans[key], self.plans["sum"])


def analyse(settings: Settings) -> Analysis:
    inst = make_instance(settings.n, settings.family, settings.seed)
    c = inst.array()
    plans = {
        "sum": A.solve(inst, 1.0),
        "sumsq": A.solve(inst, 2.0),
        "max": A.solve(inst, math.inf),
        "maxrand": A.solve_bottleneck_random(c, settings.tie_seed),
    }
    enumerated = inst.n <= C.ENUM_MAX
    if enumerated:
        plans["leximax"] = A.solve_leximax(c)
    for r in plans.values():
        assert A.check_feasible(r.plan, inst.n)
    tie = int(len(A.optimal_set(c, math.inf))) if enumerated else None
    total = math.factorial(inst.n) if enumerated else None
    return Analysis(inst, plans, A.lower_bound(c), total, tie, enumerated)


def p_rows(settings: Settings) -> list[dict]:
    """Optimum für Summe b^p, p = 1 bis unendlich: Plan, Summe, Maximum, Preis und Gewinn gegen p = 1."""
    inst = make_instance(settings.n, settings.family, settings.seed)
    base = A.solve(inst, 1.0)
    rows = []
    for p in C.P_VALUES:
        r = A.solve(inst, p)
        rows.append({"p": p, "plan": r.plan, "total": r.total, "peak": r.peak, "price": A.price(r, base), "gain": A.gain(r, base)})
    return rows


def _fair_result(inst: Instance, fair: str, tie_seed: int | None = None) -> A.Result:
    c = inst.array()
    if fair == "sumsq":
        return A.solve(inst, 2.0)
    if fair == "max":
        return A.solve(inst, math.inf)
    if fair == "maxrand":
        return A.solve_bottleneck_random(c, tie_seed if tie_seed is not None else C.TIE_SWEEP_SEEDS[0])
    if fair == "leximax":
        return A.solve_leximax(c)
    raise ValueError(f"unbekannter fairer Plan: {fair}")


def band_sizes(fair: str) -> tuple[int, ...]:
    return C.LEX_SIZES if fair == "leximax" else C.BAND_SIZES


def _spread(values) -> tuple[float, float, float]:
    a = np.asarray(values, dtype=float)
    return float(a.min()), float(np.median(a)), float(a.max())


def band_rows(family: int, fair: str, seeds=C.SWEEP_SEEDS) -> list[dict]:
    """Je Instanzgröße über die festen Instanzen: Spanne (Min, Median, Max) von Preis und Gewinn des fairen Plans `fair`.

    Beim zufälligen Gleichstand zählt je Instanz der Median über C.TIE_SWEEP_SEEDS (der Gewinn ist für alle Gleichstände gleich).
    over: Instanzen mit Preis über C.PRICE_LIMIT; gain_zero: Instanzen ohne Gewinn."""
    rows = []
    for n in band_sizes(fair):
        prices, gains = [], []
        for seed in seeds:
            inst = make_instance(n, family, seed)
            base = A.solve(inst, 1.0)
            if fair == "maxrand":
                rs = [_fair_result(inst, fair, t) for t in C.TIE_SWEEP_SEEDS]
                prices.append(float(np.median([A.price(r, base) for r in rs])))
                gains.append(A.gain(rs[0], base))
            else:
                r = _fair_result(inst, fair)
                prices.append(A.price(r, base))
                gains.append(A.gain(r, base))
        rows.append({"n": n, "seeds": len(seeds), "price": _spread(prices), "gain": _spread(gains),
                     "over": sum(p > C.PRICE_LIMIT for p in prices), "gain_zero": sum(g <= C.TOL for g in gains)})
    return rows


def dominance_rows(family: int, sizes=C.DOM_SIZES, seeds=C.SWEEP_SEEDS) -> list[dict]:
    """„Maximum, dann Summe“ gegen die Quadratsumme je Instanz: dominiert ein Plan den anderen in Preis UND Gewinn?

    max_dom: der Engpassplan ist in beidem mindestens so gut und in einem besser; sq_dom: umgekehrt; same: beide gleich;
    neither: keiner dominiert; sq_negative: das Quadrat-Optimum vergrößert das Maximum."""
    rows = []
    for n in sizes:
        max_dom = sq_dom = same = neither = neg = 0
        for seed in seeds:
            inst = make_instance(n, family, seed)
            base = A.solve(inst, 1.0)
            q, m = A.solve(inst, 2.0), A.solve(inst, math.inf)
            pq, gq, pm, gm = A.price(q, base), A.gain(q, base), A.price(m, base), A.gain(m, base)
            neg += gq < -C.TOL
            if abs(pq - pm) <= C.TOL and abs(gq - gm) <= C.TOL:
                same += 1
            elif pm <= pq + C.TOL and gm >= gq - C.TOL:
                max_dom += 1
            elif pq <= pm + C.TOL and gq >= gm - C.TOL:
                sq_dom += 1
            else:
                neither += 1
        rows.append({"n": n, "seeds": len(seeds), "max_dom": max_dom, "sq_dom": sq_dom, "same": same, "neither": neither, "sq_negative": int(neg)})
    return rows


def reach_rows(family: int, sizes=C.DOM_SIZES, seeds=C.SWEEP_SEEDS) -> list[dict]:
    """Wie weit reicht der Gewinn? at_bound: das Maximum des Plans „Maximum, dann Summe“ ist die untere Schranke (zäheste Person);
    gain_zero: der Engpassplan hat dasselbe Maximum wie das Summen-Optimum."""
    rows = []
    for n in sizes:
        at_bound = gain_zero = 0
        for seed in seeds:
            inst = make_instance(n, family, seed)
            base = A.solve(inst, 1.0)
            m = A.solve(inst, math.inf)
            at_bound += m.peak <= A.lower_bound(inst.array()) + C.TOL
            gain_zero += A.gain(m, base) <= C.TOL
        rows.append({"n": n, "seeds": len(seeds), "at_bound": int(at_bound), "gain_zero": int(gain_zero)})
    return rows


# --- Verdikte ------------------------------------------------------------------------------------------------------------------------------

def verdict_prices(a: Analysis) -> tuple[str, str]:
    """Kernfrage: Was kostet der faire Plan an Summe, was bringt er am Maximum?"""
    pm, gm = a.price("max"), a.gain("max")
    if pm <= C.TOL and gm <= C.TOL:
        text = (f"**Hier gibt es keinen Konflikt:** Der Plan „Maximum, dann Summe“ hat dieselbe Summe ({de(a.plans['sum'].total)}) und dasselbe Maximum "
                f"({de(a.plans['sum'].peak)}) wie das Summen-Optimum. Fairness kostet hier nichts und bringt nichts.")
        kind = "info"
    else:
        text = (f"**Der faire Plan „Maximum, dann Summe“ kostet {pct(pm)} Summe ({de(a.plans['max'].total)} gegen {de(a.plans['sum'].total)}) "
                f"und bringt {pct(gm)} am Maximum ({de(a.plans['max'].peak)} gegen {de(a.plans['sum'].peak)}).**")
        kind = "success"
    gq = a.gain("sumsq")
    if gq < -C.TOL:
        text += f" Das Quadrat-Optimum vergrößert hier das Maximum um {pct(-gq)}."
        kind = "warning"
    return kind, text


def verdict_tie(a: Analysis) -> tuple[str, str]:
    """Experiment Gleichstandsregel: was kostet derselbe Engpass ohne die Regel „dann kleinste Summe“?"""
    pr, pl = a.price("maxrand"), a.price("max")
    tie = ""
    if a.tie_size is not None:
        tie = " Die Optimalmenge hat genau einen Plan." if a.tie_size == 1 else f" Die Optimalmenge hat {a.tie_size} Pläne."
    if pr - pl > C.PRICE_LIMIT:
        return "warning", (f"**Ohne Gleichstandsregel kostet der Engpassplan {pct(pr)} Summe, mit der Regel „dann kleinste Summe“ {pct(pl)}:** "
                           f"die Regel macht {de((pr - pl) * 100.0)} Prozentpunkte des Preises aus; beide Pläne haben dasselbe Maximum {de(a.plans['max'].peak)}.{tie}")
    return "info", (f"Hier unterscheiden sich beide Engpasspläne kaum: Preis {pct(pr)} ohne Regel, {pct(pl)} mit Regel; "
                    f"beide haben das Maximum {de(a.plans['max'].peak)}.{tie}")


def verdict_p(rows: list[dict]) -> tuple[str, str]:
    """Experiment p-Regler: wie verläuft der Preis, wo sättigt der Gewinn?"""
    prices = [r["price"] for r in rows]
    gains = [r["gain"] for r in rows]
    i_top = int(np.argmax(prices))
    top_gain = max(gains)
    if top_gain <= C.TOL:
        sat = " Kein p bringt hier einen Gewinn am Maximum."
    else:
        i_sat = next(i for i, g in enumerate(gains) if g >= top_gain - C.TOL)
        sat = f" Der größte Gewinn ({pct(top_gain)}) ist ab p = {p_label(rows[i_sat]['p'])} erreicht."
    if i_top < len(rows) - 1 and prices[-1] < prices[i_top] - C.TOL:
        return "warning", (f"Der Preis steigt bis p = {p_label(rows[i_top]['p'])} auf {pct(prices[i_top])} und **fällt bei p = ∞ auf {pct(prices[-1])}**: "
                           f"das Maximum mit der Regel „dann Summe“ ist nicht der Grenzwert der p-Optima.{sat}")
    return "info", f"Der Preis steigt mit p höchstens auf {pct(max(prices))} (bei p = ∞: {pct(prices[-1])}).{sat}"


def verdict_band(rows: list[dict], fair: str) -> tuple[str, str]:
    """Experiment Bänder: Spannen je Instanzgröße, ohne Trendaussage."""
    parts = []
    for r in rows:
        lo, med, hi = r["price"]
        glo, gmed, ghi = r["gain"]
        parts.append(f"n = {r['n']}: Preis Median {pct(med)} (Spanne {pct(lo)} bis {pct(hi)}), Gewinn Median {pct(gmed)} (Spanne {pct(glo)} bis {pct(ghi)}), "
                     f"Preis über {pct(C.PRICE_LIMIT, 0)} in {r['over']} von {r['seeds']}, Gewinn null in {r['gain_zero']}")
    kind = "warning" if fair == "maxrand" and any(r["over"] > 0 for r in rows) else "info"
    return kind, "Je " + str(rows[0]["seeds"]) + " feste Instanzen, Plan „" + C.PLAN_NAMES[fair] + "“: " + "; ".join(parts) + "."


def verdict_dominance(rows: list[dict]) -> tuple[str, str]:
    parts = [f"n = {r['n']}: „Maximum, dann Summe“ dominiert in {r['max_dom']} von {r['seeds']}, das Quadrat in {r['sq_dom']}, gleich in {r['same']}, keines in {r['neither']}"
             for r in rows]
    neg = sum(r["sq_negative"] for r in rows)
    tail = f" Das Quadrat-Optimum vergrößert das Maximum in {neg} dieser Instanzen." if neg else ""
    return "info", "Dominanz heißt: in Preis und Gewinn mindestens so gut und in einem besser. " + "; ".join(parts) + "." + tail


def verdict_reach(a: Analysis, rows: list[dict]) -> tuple[str, str]:
    """Experiment Reichweite: wie nah liegt das Maximum an der unteren Schranke?"""
    m = a.plans["max"].peak
    at = "und erreicht sie" if m <= a.lower + C.TOL else "und liegt darüber"
    parts = "; ".join(f"n = {r['n']}: Schranke erreicht in {r['at_bound']} von {r['seeds']}, Gewinn null in {r['gain_zero']}" for r in rows)
    return "info", (f"Die zäheste Person erzwingt mindestens {de(a.lower)}; das Maximum des Plans „Maximum, dann Summe“ ist {de(m)} {at}. "
                    f"Unter der Schranke gewinnt kein Plan mehr. Je {rows[0]['seeds']} feste Instanzen: {parts}.")
