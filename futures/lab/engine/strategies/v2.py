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
    "FADE2": {"min_levels": 2, "stop": 12, "target": 8, "max_min": 10, "cooldown_s": 120},
    "FADEL": {"min_levels": 2, "stop": 12, "target": 8, "max_min": 10, "cooldown_s": 120, "wait_s": 30},
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
        # la señal se fecha DESPUÉS de la orden (todos sus llenados comparten el timestamp)
        out.append(Signal(sec=t0 + 1e-6, side=-side, stop_ticks=p["stop"], target_ticks=p["target"], max_sec=p["max_min"] * 60,
                          kind="FADE", level="orden", meta={"order_size": int(size[c]), "levels": int(hi[c] - lo[c] + 1), "order_px": int(px[starts[c]]) / 4}))
    return out


def fade_v2(s, ref, thr, p=None):
    """FADE con objetivo corto: el efecto medido es de 6–7 ticks, así que objetivo 8, stop 12, 10 minutos."""
    p = p or PARAMS["FADE2"]
    sigs = fade(s, ref, thr, {"min_levels": p["min_levels"], "stop": p["stop"], "target": p["target"], "max_min": p["max_min"], "cooldown_s": p["cooldown_s"]})
    for x in sigs:
        x.kind = "FADE"
    return sigs


def fade_limit(s, ref, thr, p=None):
    """FADE pasivo: en vez de cruzar el spread, pone una orden límite EN el precio extremo que barrió la orden grande
    (donde la orden grande dejó de empujar), detrás de la cola visible; si no se llena en 30 s se cancela.
    Captura el rebote del spread en vez de pagarlo. Objetivo 8, stop 12, 10 min."""
    p = p or PARAMS["FADEL"]
    sigs = fade(s, ref, thr, {"min_levels": p["min_levels"], "stop": p["stop"], "target": p["target"], "max_min": p["max_min"], "cooldown_s": p["cooldown_s"]})
    out = []
    for x in sigs:
        i = s.idx_sec(x.sec); k = i - 1 if i > 0 else 0
        ext = int(s.px[k])                       # último precio operado por la orden grande (su extremo)
        x.order = "limit"; x.limit_px = ext; x.wait_sec = p["wait_s"]; x.kind = "FADEL"
        out.append(x)
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


REGISTRY = {"FADE": fade, "HVN": hvn, "ABS": absorption_v2, "FADE2": fade_v2, "FADEL": fade_limit}
NEEDS_PROFILE = {"HVN"}
