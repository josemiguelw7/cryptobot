"""Estrategias v34 (tanda 35), congeladas en futures/strategies/v36.json.
  IBX v1 : EXTENSIÓN DEL BALANCE INICIAL CONFIRMADA POR DELTA (G4, pedido de Jose 26/10/2026). Balance inicial (IB) = máximo y mínimo de
           09:30–10:30 (Steidlmayer/Dalton). Después de las 10:30, cuando una celda de 10 s supera el borde del IB en >= brk_ticks y en
           los últimos win_s segundos el delta agresivo es >= delta_min del volumen a favor de la ruptura y el último precio sigue fuera
           del borde, es una extensión con iniciativa. Entrada a mercado a favor al cerrar la celda. Stop `stop_inside` ticks dentro del
           IB (12–32 ticks), objetivo rr x stop, salida a max_min minutos. Una vez por lado y por día (máximo 2 por día), 10:30–14:30.
           Investigación: docs/investigacion/extension_ib.md.
"""
import numpy as np
from ..sim import Signal
from ..data import NY_OPEN
from . import v1 as V1

PARAMS = {
    "IBX": {"win_s": 120, "delta_min": 0.05, "brk_ticks": 4, "stop_inside": 4, "stop_min": 12, "stop_max": 32, "rr": 1.5, "max_min": 20,
            "ib_end_sec": 37800.0, "last_sec": 52200.0, "data_end_sec": 56700.0},
}
BIN = V1.BIN
CONTRACTS = 1


def ib_extension(s, ref, thr, p=None):
    p = p or PARAMS["IBX"]
    if not ref:
        return []
    i, j = s.idx_sec(NY_OPEN), s.idx_sec(p["data_end_sec"])
    if j - i < 50:
        return []
    buy, sell, hi, lo, first, last = V1._bins(s, i, j)
    nb = len(buy); W = int(p["win_s"] // BIN); c0 = int((p["ib_end_sec"] - NY_OPEN) // BIN)
    if nb <= c0 + W:
        return []
    ibh, ibl = int(hi[:c0].max()), int(lo[:c0].min())
    cb, cs = np.cumsum(np.r_[0.0, buy]), np.cumsum(np.r_[0.0, sell])
    done = set(); out = []
    for e in range(c0, nb):
        t_sig = NY_OPEN + (e + 1) * BIN
        if t_sig > p["last_sec"]:
            break
        w0 = max(c0, e - W + 1)                       # la ventana de flujo empieza al cerrar el IB (sin mirar antes de 10:30)
        b, sl = cb[e + 1] - cb[w0], cs[e + 1] - cs[w0]
        tot = b + sl
        if tot <= 0:
            continue
        dl = (b - sl) / tot
        for side, edge, ext in ((1, ibh, hi[e]), (-1, ibl, lo[e])):
            if side in done:
                continue
            if (ext - edge) * side < p["brk_ticks"] or (last[e] - edge) * side <= 0 or dl * side < p["delta_min"]:
                continue
            done.add(side)
            entry = int(last[e]); inner = edge - side * p["stop_inside"]
            stop = int(min(max((entry - inner) * side, p["stop_min"]), p["stop_max"]))
            out.append(Signal(sec=t_sig, side=side, stop_ticks=stop, target_ticks=int(round(p["rr"] * stop)), max_sec=p["max_min"] * 60,
                              kind="IBX", level="ib_hi" if side > 0 else "ib_lo",
                              meta={"delta_share": float(dl), "ib_range": (ibh - ibl) / 4}))
    return out


REGISTRY = {"IBX": ib_extension}
