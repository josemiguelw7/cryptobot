"""
PRE-CHECK DE ADMISION (plan_v3 C0.4 + F1).

Ninguna semilla entra al examen sin pasar por aqui. Mide, SIN escribir
en el ledger y SIN gastar un nombre:

  1. turnover realizado contra hold declarado (regla F1: realizado >=
     declarado/1.5, si no vuelve a diseño)
  2. breakeven de costo: a que comision dejaria de perder

Correr: .venv/bin/python analysis/admission.py [roster]
"""
import os, sys, statistics as st
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "backtest"))
sys.path.insert(0, os.path.join(ROOT, "bot"))
os.environ.setdefault("EXAM_ROSTER", "seeds_crypto_v3")
import exam_1h as X

LEVELS = [0.0042, 0.0032, 0.0020, 0.0010, 0.0005, 0.0001, 0.0]


def main():
    R = X.SEEDS
    data = {p: X.load_hourly(p) for p in X.PAIRS}
    cutoff = X.holdout_cutoff({k: v[1] for k, v in data.items()})
    cut = {p: sum(1 for t in data[p][1] if t < cutoff) for p in X.PAIRS}

    print(f"{'semilla':14s} {'decl':>6s} {'real':>7s} {'turnov':>7s} "
          f"{'cobert':>7s} {'med/oper':>9s} {'ganaB&H':>8s} {'breakeven':>10s}")
    print("-" * 78)
    for name, cfg in R.SEEDS.items():
        strat = R.get(name)
        rows = []
        for p in X.PAIRS:
            cl, ts = data[p]
            if not cl or cut[p] <= 0:
                continue
            r, _ = X.windows_for(p, strat, cl, ts, 0, cut[p],
                                 X.FEE, X.SLIP)
            rows += r
        if not rows:
            print(f"{name:14s}  (sin ventanas validas)")
            continue
        tr = sum(r["trades"] for r in rows)
        bars = len(rows) * X.WIN
        realized = (2.0 * bars / tr) if tr else float("inf")
        decl = cfg["hold_h"]
        ok = "OK" if realized >= decl / 1.5 else "CHURN"
        med = X.median_window_traded(rows)     # C0.1b: solo cuando opera
        cov = X.pct_windows_traded(rows)
        beat = X.beat_bh_pct(rows)

        be = None
        for lvl in LEVELS:
            rr = []
            for p in X.PAIRS:
                cl, ts = data[p]
                if not cl or cut[p] <= 0:
                    continue
                r, _ = X.windows_for(p, strat, cl, ts, 0, cut[p], 0.0, lvl)
                rr += r
            if rr and X.median_window(rr) >= 0:
                be = lvl
                break
        bes = "nunca" if be is None else f"{be*100:.3f}%"
        cflag = "" if cov >= 0.50 else " AUSENTE"
        print(f"{name:14s} {decl:>5d}h {realized:>6.0f}h {ok:>7s} "
              f"{cov:>6.0%}{cflag:<8s} {med:>+9.2%} {beat:>7.0%} {bes:>10s}")
    print()
    print("Regla F1: realizado >= declarado/1.5 o vuelve a diseño.")
    print("Regla C0.4: breakeven 'nunca' a <=0.32%/lado -> no gasta nombre.")
    print("Regla C0.1b: cobertura < 50% -> AUSENTE, la mediana global miente.")


if __name__ == "__main__":
    main()
