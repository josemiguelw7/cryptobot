"""Estrategias v2 (tanda 2), congeladas en futures/strategies/v2.json. Reglas con números MEDIDOS en el mapa de señales
y en el estudio de salidas, no inventados. Incluye:
  FADE v1  : desvanecer órdenes grandes (hipótesis inversa de BIG; mapa: −6 a −7 ticks a 5/15/30 min, z ≈ −28)
  HVN  v1  : rechazo de nodos de alto volumen del día anterior (mapa: +9 ticks a 15 min, +17 a 30 min, z ≈ 19)
  ABS  v2  : ABS v1 con salida por tiempo (TP 40 puntos que casi no se toca; estudio de salidas: meseta TP 30–50 × stop v1)
"""
import numpy as np
from ..sim import Signal
from ..data import NY_OPEN
from . import v1 as V1

PARAMS = {
    "FADE": {"min_levels": 2, "stop": 16, "target": None, "max_min": 15, "cooldown_s": 120},
    "HVN": {"far_ticks": 20, "within_s": 3600, "stop": 12, "target": 16, "max_min": 30, "hvn_pct": 90},
    "ABS": {**V1.PARAMS["ABS"], "target_fixed": 160},
}
BIN = V1.BIN


def fade(s, ref, thr, p=None):
    """Entra EN CONTRA de una orden agresiva ≥ p99 (10+) que barre ≥ 2 niveles, a mercado al terminar la orden.
    Sin filtro de nivel (el mapa midió el efecto sin condicionar). Sin TP: sale por tiempo (15 min) o stop 16 ticks."""
    p = p or PARAMS["FADE"]
    if not thr:
        return []
    i, j = s.idx_sec(NY_OPEN), s.idx_sec(NY_OPEN + 2 * 3600 + 15 * 60)
    tid = s.tid[i:j]; px = s.px[i:j]; vol = s.vol[i:j]; sd = s.side[i:j]; sec = s.sec[i:j]
    if len(tid) == 0:
        return []
    starts = np.r_[0, np.flatnonzero(np.diff(tid)) + 1]; ends = np.r_[starts[1:], len(tid)] - 1
    size = np.add.reduceat(vol, starts); hi = np.maximum.reduceat(px, starts); lo = np.minimum.reduceat(px, starts)
    cand = np.flatnonzero((size >= thr["order_p99"]) & (hi - lo + 1 >= p["min_levels"]))
    out, last = [], -1e9
    for c in cand:
        t0, side = float(sec[ends[c]]), int(sd[starts[c]])
        if side == 0 or t0 - last < p["cooldown_s"]:
            continue
        last = t0
        out.append(Signal(sec=t0, side=-side, stop_ticks=p["stop"], target_ticks=p["target"], max_sec=p["max_min"] * 60,
                          kind="FADE", level="orden", meta={"order_size": int(size[c]), "levels": int(hi[c] - lo[c] + 1), "order_px": int(px[starts[c]]) / 4}))
    return out


def hvn(s, ref, thr, p=None, prof=None):
    """Cuando el precio toca un nodo de alto volumen (≥ p90 del perfil NY de ayer) tras haber estado ≥ 20 ticks
    lejos en la última hora, entra a mercado de vuelta hacia donde venía. Stop 12 ticks del otro lado del nodo,
    objetivo 16 ticks, 30 min. Cada nodo una vez por día."""
    p = p or PARAMS["HVN"]
    if prof is None or not len(prof):
        return []
    i, j = s.idx_sec(NY_OPEN), s.idx_sec(NY_OPEN + 2 * 3600 + 15 * 60)
    buy, sell, bh, bl, first, last = V1._bins(s, i, j); nb = len(buy)
    if nb < 60:
        return []
    pxs, vs = prof[:, 0], prof[:, 1]; levels = pxs[vs >= np.percentile(vs, p["hvn_pct"])]
    W = p["within_s"] // BIN; out, used = [], set()
    for lvl in levels:
        lvl = int(lvl)
        touch = np.flatnonzero((bl <= lvl) & (bh >= lvl))
        if not len(touch):
            continue
        t = int(touch[0]); w0 = max(0, t - W)
        above = np.flatnonzero(bl[w0:t] >= lvl + p["far_ticks"]); below = np.flatnonzero(bh[w0:t] <= lvl - p["far_ticks"])
        if len(above) and (not len(below) or above[-1] > below[-1]):
            side = 1          # venía de arriba, tocó el nodo: rebote hacia arriba
        elif len(below):
            side = -1
        else:
            continue
        key = (lvl, side)
        if key in used:
            continue
        used.add(key)
        out.append(Signal(sec=NY_OPEN + (t + 1) * BIN, side=side, stop_ticks=p["stop"], target_ticks=p["target"], max_sec=p["max_min"] * 60,
                          kind="HVN", level=f"hvn_{lvl / 4}", meta={"hvn_px": lvl / 4}))
    return out


def absorption_v2(s, ref, thr, p=None):
    """ABS v1 con objetivo de 40 puntos (160 ticks): en la práctica, salida por tiempo a los 15 min."""
    p = p or PARAMS["ABS"]
    sigs = V1.absorption(s, ref, thr, {k: v for k, v in p.items() if k != "target_fixed"})
    for x in sigs:
        x.target_ticks = p["target_fixed"]; x.kind = "ABS"
    return sigs


REGISTRY = {"FADE": fade, "HVN": hvn, "ABS": absorption_v2}
NEEDS_PROFILE = {"HVN"}
