"""Prueba dorada del motor: ABS v1 sobre un conjunto fijo de 60 sesiones, sin RAND ni Red Team (≈ 10 s),
más (desde el motor 1.2.0) la huella del PERFIL EN DESARROLLO (POC/VAH/VAL por celda de 10 s, strategies/v8.py::_developing_profile)
sobre las primeras 20 sesiones: ABS v1 no usa ese ayudante, así que la dorada de ABS no lo cubría.
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
N_PROFILE = 20


def run_profile():
    """Huella del perfil en desarrollo sobre las primeras N_PROFILE sesiones, ventana 09:30–15:45 ET (la de ABU)."""
    import numpy as np
    from .data import NY_OPEN
    from .strategies import v1 as V1
    from .strategies.v8 import _developing_profile
    dates, sess_sha = config.design_sessions()
    h = hashlib.sha256(); n = 0
    for d in dates[:N_PROFILE]:
        s = load(d, ny_only=True)
        i, j = s.idx_sec(NY_OPEN), s.idx_sec(56700.0)
        if j - i < 50:
            continue
        buy, sell, hi, lo, first, last = V1._bins(s, i, j); nb = len(buy)
        px = s.px[i:j].astype(float); vol = s.vol[i:j].astype(float); sec = s.sec[i:j]
        b = ((sec - NY_OPEN) // V1.BIN).astype(int)
        poc, vah, val = _developing_profile(px, vol, b, nb)
        h.update(d.encode()); h.update(np.asarray(poc, dtype=np.int64).tobytes()); h.update(np.asarray(vah, dtype=np.int64).tobytes()); h.update(np.asarray(val, dtype=np.int64).tobytes())
        n += nb
    return h.hexdigest(), n, sess_sha


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
    t0 = time.time(); h, n, sess_sha = run(); hp, np_, _ = run_profile()
    if a.update:
        old = json.load(open(GOLDEN)) if os.path.exists(GOLDEN) else {}
        abs_same = old.get("trades_sha256") == h
        json.dump({"estrategia": "ABS v1", "sesiones": N_SESSIONS, "sesiones_sha256": sess_sha, "operaciones": n, "trades_sha256": h,
                   "commit": config.git_commit(), "fecha": time.strftime("%Y-%m-%d"), "motivo": a.update,
                   "abs_v1_sin_cambio_respecto_a_la_anterior": abs_same,
                   "perfil_en_desarrollo": {"sesiones": N_PROFILE, "celdas": np_, "sha256": hp, "commit": config.git_commit(), "fecha": time.strftime("%Y-%m-%d"), "motivo": a.update}},
                  open(GOLDEN, "w"), indent=1)
        print(f"golden fijada: ABS {h[:16]} ({n} operaciones, {'igual' if abs_same else 'CAMBIÓ'} respecto a la anterior) · perfil {hp[:16]} ({np_} celdas) · {time.time()-t0:.0f}s · RECUERDA: commit + push, o el orquestador se negará a correr"); return
    if not os.path.exists(GOLDEN):
        print("no hay golden.json; fíjala con --update"); sys.exit(2)
    g = json.load(open(GOLDEN))
    ok_abs = g["trades_sha256"] == h and g["sesiones_sha256"] == sess_sha
    gp = g.get("perfil_en_desarrollo")
    ok_prof = bool(gp) and gp["sha256"] == hp
    print(f"golden ABS {'OK' if ok_abs else 'DIFIERE'}: esperado {g['trades_sha256'][:16]} ({g['operaciones']} op.) · obtenido {h[:16]} ({n} op.) · "
          f"perfil {'OK' if ok_prof else ('SIN FIJAR' if not gp else 'DIFIERE')}: {hp[:16]} ({np_} celdas) · {time.time()-t0:.0f}s")
    sys.exit(0 if (ok_abs and ok_prof) else 1)


if __name__ == "__main__":
    main()
