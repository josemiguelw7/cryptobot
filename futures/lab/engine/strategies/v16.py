"""Estrategias v16 (tanda 17), congeladas en futures/strategies/v18.json.
  IMB v1 : DESEQUILIBRIOS DIAGONALES APILADOS (footprint) Y REPRUEBA DE LA ZONA.
           En los últimos 60 s se arma, por precio p, el volumen agresivo comprador A[p] y vendedor B[p].
           Desequilibrio comprador en p: A[p] >= ratio * B[p-1] y A[p] >= min_vol (comparación diagonal).
           Desequilibrio vendedor en p: B[p] >= ratio * A[p+1] y B[p] >= min_vol.
           Pila: >= 3 precios consecutivos con el mismo desequilibrio (se toma la pila más larga; empate, la más alta/baja según el lado).
           Zona = de la parte baja a la alta de la pila. Si el precio ya se alejó >= away_ticks de la zona en la dirección de la iniciativa,
           se deja una orden límite en el borde cercano (comprador: borde alto de la zona; vendedor: borde bajo) durante wait_s.
           Stop 4 ticks más allá del borde lejano de la zona (12–32 desde la entrada), objetivo 2R, salida a 15 min.
           Entradas 10:00–15:30 ET. Investigación: docs/investigacion/desequilibrios_apilados.md.
"""
import numpy as np
from ..sim import Signal
from ..data import NY_OPEN

PARAMS = {
    "IMB": {"ratio": 3.0, "min_vol": 10, "min_stack": 3, "window_s": 60, "step_s": 5, "away_ticks": 4, "wait_s": 300,
            "stop_beyond": 4, "stop_min": 12, "stop_max": 32, "rr": 2.0, "max_min": 15, "cooldown_s": 300,
            "first_sec": 36000.0, "last_sec": 55800.0, "data_end_sec": 56700.0},
}


def _longest_run(mask):
    """(inicio, fin) inclusivos de la racha más larga de True; empate: la última. None si no hay."""
    best = None; start = None
    for k, v in enumerate(list(mask) + [False]):
        if v and start is None:
            start = k
        elif not v and start is not None:
            if best is None or (k - start) >= (best[1] - best[0] + 1):
                best = (start, k - 1)
            start = None
    return best


def stacked_imbalance(s, ref, thr, p=None):
    p = p or PARAMS["IMB"]
    i, j = s.idx_sec(NY_OPEN), s.idx_sec(p["data_end_sec"])
    if j - i < 500:
        return []
    sec = s.sec[i:j]; px = s.px[i:j].astype(np.int64); vol = s.vol[i:j].astype(float); sd = s.side[i:j]
    out = []; last_sig = {1: -1e9, -1: -1e9}
    t = max(p["first_sec"], NY_OPEN + p["window_s"])
    while t <= p["last_sec"]:
        a = int(np.searchsorted(sec, t - p["window_s"], side="left")); b = int(np.searchsorted(sec, t, side="left"))
        if b - a >= 20:
            wp = px[a:b]; lo_p, hi_p = int(wp.min()), int(wp.max())
            n = hi_p - lo_p + 1
            if n >= p["min_stack"] + 1:
                idx = wp - lo_p
                A = np.bincount(idx, weights=np.where(sd[a:b] > 0, vol[a:b], 0.0), minlength=n)
                B = np.bincount(idx, weights=np.where(sd[a:b] < 0, vol[a:b], 0.0), minlength=n)
                last_px = int(wp[-1])
                for side in (1, -1):
                    if t - last_sig[side] < p["cooldown_s"]:
                        continue
                    m = np.zeros(n, bool)
                    if side > 0:
                        m[1:] = (A[1:] >= p["ratio"] * B[:-1]) & (A[1:] >= p["min_vol"])
                    else:
                        m[:-1] = (B[:-1] >= p["ratio"] * A[1:]) & (B[:-1] >= p["min_vol"])
                    run = _longest_run(m)
                    if run is None or run[1] - run[0] + 1 < p["min_stack"]:
                        continue
                    z_lo, z_hi = lo_p + run[0], lo_p + run[1]
                    if side > 0:
                        if last_px < z_hi + p["away_ticks"]:
                            continue
                        limit = z_hi; stop = int(min(max(z_hi - (z_lo - p["stop_beyond"]), p["stop_min"]), p["stop_max"]))
                    else:
                        if last_px > z_lo - p["away_ticks"]:
                            continue
                        limit = z_lo; stop = int(min(max((z_hi + p["stop_beyond"]) - z_lo, p["stop_min"]), p["stop_max"]))
                    last_sig[side] = t
                    out.append(Signal(sec=float(t), side=side, stop_ticks=stop, target_ticks=int(round(stop * p["rr"])),
                                      max_sec=p["max_min"] * 60, kind="IMB", level="pila", order="limit", limit_px=int(limit),
                                      wait_sec=float(p["wait_s"]),
                                      meta={"zona": [z_lo / 4, z_hi / 4], "pila": run[1] - run[0] + 1}))
        t += p["step_s"]
    out.sort(key=lambda x: x.sec)
    return out


REGISTRY = {"IMB": stacked_imbalance}
