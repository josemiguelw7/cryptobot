"""Estrategias v3 (tanda 4), congeladas en futures/strategies/v5.json.
  ABS v3 : absorción con ENTRADA TEMPRANA (sin la confirmación de 60 s) y salida por tiempo a 15 min como ABS v2.
           Tercera y última versión de ABS (máximo 3).
"""
import numpy as np
from ..sim import Signal
from ..data import NY_OPEN
from . import v1 as V1

PARAMS = {
    "ABS3": {"near_ticks": 4, "max_advance": 2, "stop_beyond": 4, "stop_min": 12, "stop_max": 32, "max_min": 15, "target_fixed": 160},
}
BIN = V1.BIN


def absorption_early(s, ref, thr, p=None):
    """Mismo detector que ABS v1 (≥ p95 de volumen agresivo en 60 s, el precio no avanza más de 2 ticks, extremo a ≤ 4 ticks
    de un nivel del día anterior/noche), pero entra a mercado EN CONTRA del lado absorbido al cerrar la ventana de 60 s
    (sin esperar confirmación). Stop 4 ticks más allá del extremo (12–32 ticks). Sale por tiempo a los 15 min."""
    p = p or PARAMS["ABS3"]
    if not ref or not thr:
        return []
    i, j = s.idx_sec(NY_OPEN), s.idx_sec(NY_OPEN + 2 * 3600 + 15 * 60)
    buy, sell, hi, lo, first, last = V1._bins(s, i, j)
    nb = len(buy); W = 60 // BIN
    if nb < 2 * W:
        return []
    k = np.ones(W)
    bw = np.convolve(buy, k, "valid"); sw = np.convolve(sell, k, "valid")
    lv = V1._ref_levels(ref); used = set(); out = []
    for e in range(W - 1, nb - W):
        w0 = e - W + 1
        for side, volw, thr_key in ((1, bw[w0], "buy60_p95"), (-1, sw[w0], "sell60_p95")):
            if volw < thr[thr_key]:
                continue
            start = int(first[w0])
            if side > 0:
                ext = int(hi[w0:e + 1].max())
                if ext > start + p["max_advance"]:
                    continue
            else:
                ext = int(lo[w0:e + 1].min())
                if ext < start - p["max_advance"]:
                    continue
            name = V1._near(ext, lv, p["near_ticks"])
            if not name or name in used:
                continue
            used.add(name)
            entry_est = int(last[e])
            dist = abs(ext + side * p["stop_beyond"] - entry_est)
            stop = int(min(max(dist, p["stop_min"]), p["stop_max"]))
            out.append(Signal(sec=NY_OPEN + (e + 1) * BIN, side=-side, stop_ticks=stop, target_ticks=p["target_fixed"],
                              max_sec=p["max_min"] * 60, kind="ABS", level=name,
                              meta={"absorbed_vol": float(volw), "extreme": ext / 4, "side_absorbed": side}))
    return out


REGISTRY = {"ABS3": absorption_early}
