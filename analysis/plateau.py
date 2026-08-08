"""
MESETA DE PARAMETROS + CONSISTENCIA ENTRE ACTIVOS (Tanda A).

MESETA: si trend_168 funciona pero trend_144 y trend_192 fallan, es
sobreajuste (un pico). Si toda la vecindad se comporta parecido, es
estructura. Es la prueba mas dura contra curve-fitting que existe.

CONSISTENCIA: una semilla que solo funciona en un par es ruido.

No crea candidatos ni escribe en el ledger: son variaciones de
semillas YA examinadas, evaluadas fuera del examen. K no sube.
"""
import os, sys, statistics as st
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "backtest"))
sys.path.insert(0, os.path.join(ROOT, "bot"))
import exam_1h as X
import strategies as S

FEE, SLIP = 0.0, 0.0042

FAMILIES = {
    "trend":  (lambda n: S.Trend(n),           [96, 120, 144, 168, 192, 216, 240]),
    "tsmom":  (lambda n: S.TSMom(n),           [36, 48, 60, 72, 96, 120, 144]),
    "nearhi": (lambda n: S.NearHigh(n, 0.02),  [96, 120, 144, 168, 192, 216, 240]),
}


def score(strat, data, cut):
    rows = []
    for p in X.PAIRS:
        cl, ts = data[p]
        if not cl or cut[p] <= 0:
            continue
        r, _ = X.windows_for(p, strat, cl, ts, 0, cut[p], FEE, SLIP)
        rows += r
    if not rows:
        return None, None
    med = st.median(w["ret"] for w in rows)
    beat = sum(1 for w in rows if w["ret"] > w["bh"]) / len(rows)
    return med, beat


def main():
    data = {p: X.load_hourly(p) for p in X.PAIRS}
    cutoff = X.holdout_cutoff({k: v[1] for k, v in data.items()})
    cut = {p: sum(1 for t in data[p][1] if t < cutoff) for p in X.PAIRS}

    print("=== MESETA DE PARAMETROS (mediana por ventana / %% gana a B&H) ===")
    for fam, (mk, vals) in FAMILIES.items():
        print(f"\n  {fam}:")
        meds = []
        for v in vals:
            m, b = score(mk(v), data, cut)
            if m is None:
                continue
            meds.append(m)
            mark = "  <-- adoptado" if v in (168, 72) else ""
            print(f"    n={v:4d}   mediana {m:+7.2%}   gana B&H {b:5.0%}{mark}")
        if len(meds) > 2:
            spread = max(meds) - min(meds)
            print(f"    -> dispersion de la vecindad: {spread:.2%} "
                  + ("(MESETA: estructura)" if spread < 0.02
                     else "(PICO: sospecha de sobreajuste)"))

    print("\n=== CONSISTENCIA ENTRE PARES ===")
    for n in ["h_trend_168", "h_tsmom_72", "h_calm_24_168", "h_boll_48"]:
        strat = X.SEEDS.get(n)
        if getattr(strat, "wants_bars", False):
            continue
        per = []
        for p in X.PAIRS:
            cl, ts = data[p]
            if not cl or cut[p] <= 0:
                continue
            r, _ = X.windows_for(p, strat, cl, ts, 0, cut[p], FEE, SLIP)
            if r:
                per.append((p, st.median(w["ret"] for w in r)))
        if not per:
            continue
        pos = sum(1 for _, m in per if m > 0)
        print(f"  {n:16s} positiva en {pos}/{len(per)} pares   "
              + "  ".join(f"{p.split('-')[0]}:{m:+.1%}" for p, m in per))


if __name__ == "__main__":
    main()
