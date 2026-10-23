"""Prueba dorada del motor: ABS v1 sobre un conjunto fijo de 60 sesiones, sin RAND ni Red Team (≈ 10 s).
La huella de las operaciones debe salir IDÉNTICA después de cualquier cambio de código. Si cambia, fue a propósito:
se actualiza futures/lab/golden.json con el motivo escrito y el commit, nunca en silencio.

  python -m engine.golden            compara contra golden.json (sale con 1 si difiere)
  python -m engine.golden --update "motivo"   fija la huella nueva (solo tras un cambio intencional del motor)
El orquestador la corre antes de cada prueba y se niega a correr si difiere.
"""
import argparse, hashlib, json, os, sys, time
from . import config
from .data import load
from .levels import Levels, precompute_stats
from .sim import Rules, simulate
from .strategies import v1 as S1
from .sim import sec_to_hms

GOLDEN = os.path.join(config.LAB, "golden.json")
N_SESSIONS = 60


def run():
    dates, sess_sha = config.design_sessions()
    dates = dates[:N_SESSIONS]
    precompute_stats(dates)
    L = Levels(dates); gen, params = S1.REGISTRY["ABS"], dict(S1.PARAMS["ABS"])
    c = config.Costs(); rows = []
    for d in dates:
        ref, thr = L.reference(d), L.thresholds(d)
        if not ref or not thr:
            continue
        s = load(d, ny_only=True)
        for t in simulate(s, gen(s, ref, thr, params), Rules(), c.slip_ticks, c.commission_rt):
            rows.append(f"{t['date']},{t['side']},{sec_to_hms(t['entry_sec'])},{t['entry_px']},{sec_to_hms(t['exit_sec'])},{t['exit_px']},{t['reason']},{t['pnl_ticks']},{t['net_usd']:.2f}")
    h = hashlib.sha256("\n".join(rows).encode()).hexdigest()
    return h, len(rows), sess_sha


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--update", default=""); a = ap.parse_args()
    t0 = time.time(); h, n, sess_sha = run()
    if a.update:
        json.dump({"estrategia": "ABS v1", "sesiones": N_SESSIONS, "sesiones_sha256": sess_sha, "operaciones": n, "trades_sha256": h,
                   "commit": config.git_commit(), "fecha": time.strftime("%Y-%m-%d"), "motivo": a.update}, open(GOLDEN, "w"), indent=1)
        print(f"golden fijada: {h[:16]} ({n} operaciones) · {time.time()-t0:.0f}s"); return
    if not os.path.exists(GOLDEN):
        print("no hay golden.json; fíjala con --update"); sys.exit(2)
    g = json.load(open(GOLDEN))
    ok = g["trades_sha256"] == h and g["sesiones_sha256"] == sess_sha
    print(f"golden {'OK' if ok else 'DIFIERE'}: esperado {g['trades_sha256'][:16]} ({g['operaciones']} op.) · obtenido {h[:16]} ({n} op.) · {time.time()-t0:.0f}s")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
