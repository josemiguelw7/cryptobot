"""
CURVA DE SENSIBILIDAD AL COSTO (Tanda A, 2026-08-07).

Para cada semilla: a que nivel de comision dejaria de perder?

Puro analisis sobre semillas YA examinadas. No crea candidatos, no
escribe en el ledger, no sube K, no toca estado en vivo. Reusa el mismo
motor de ventanas del examen, variando solo el costo.

Lectura: si una semilla empata al 0.30%, pasar a ordenes maker la
salva. Si necesita 0.05%, esta muerta a cualquier costo retail.
"""
import os, sys, csv
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "backtest"))
sys.path.insert(0, os.path.join(ROOT, "bot"))

import exam_1h as X

# niveles de costo por LADO (fee+slip). El actual es ~0.42%/lado.
LEVELS = [0.0042, 0.0032, 0.0020, 0.0016, 0.0010, 0.0005,
          0.00025, 0.0001, 0.00005, 0.0]


def curve(name):
    strat = X.SEEDS.get(name)
    data = {p: X.load_hourly(p) for p in X.PAIRS}
    cutoff = X.holdout_cutoff({k: v[1] for k, v in data.items()})
    cut = {p: sum(1 for t in data[p][1] if t < cutoff) for p in X.PAIRS}
    out = []
    for lvl in LEVELS:
        rows = []
        for p in X.PAIRS:
            closes, ts = data[p]
            if not closes or cut[p] <= 0:
                continue
            r, _ = X.windows_for(p, strat, closes, ts, 0, cut[p], 0.0, lvl)
            rows += r
        if not rows:
            continue
        wins = sum(1 for w in rows if w["ret"] > w["bh"])
        med = sorted(w["ret"] for w in rows)[len(rows) // 2]
        out.append((lvl, med, wins / len(rows), len(rows)))
    return out


def main():
    names = sys.argv[1:] or list(X.SEEDS.SEEDS)
    print(f"{'semilla':16s} {'empata a':>10s}  {'gana a B&H a':>13s}   "
          f"veredicto")
    print("-" * 74)
    for n in names:
        try:
            c = curve(n)
        except Exception as e:
            print(f"{n:16s} ERROR {e}")
            continue
        be = next((l for l, m, w, _ in c if m >= 0), None)
        bh = next((l for l, m, w, _ in c if w >= 0.5), None)
        def f(x):
            return "nunca" if x is None else f"{x*100:.3f}%/lado"
        if be is None:
            v = "muerta a cualquier costo"
        elif be >= 0.0032:
            v = "viable con MAKER"
        elif be >= 0.0010:
            v = "necesita futuros/DMA"
        else:
            v = "solo nivel institucional"
        print(f"{n:16s} {f(be):>10s}  {f(bh):>13s}   {v}")


if __name__ == "__main__":
    main()
