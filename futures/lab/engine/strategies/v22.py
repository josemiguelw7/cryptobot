"""Estrategias v22 (tanda 23), congeladas en futures/strategies/v24.json.
  FAF v1 : SUBASTA FALLIDA — el precio sale del valor/extremos de ayer o de la noche con una
           ráfaga de flujo agresivo (iniciativa) y vuelve al nivel en 120 s con delta contrario: la salida falló (Dalton / Barros: failed auction).
           Niveles superiores: VAH, máximo de ayer, máximo de la noche. Inferiores: VAL, mínimo de ayer, mínimo de la noche. Un intento por nivel y día.
           Entrada a mercado en contra de la salida; stop 4 ticks más allá del extremo de la excursión (12–32); objetivo 2R; salida a 15 min.
           Investigación y definición fijada antes de correr: docs/investigacion/subasta_fallida.md.
"""
import numpy as np
from ..sim import Signal
from ..data import NY_OPEN
from . import v1 as V1

PARAMS = {
    "FAF": {"pen_ticks": 2, "fail_s": 120, "burst_frac": 0.5, "delta_s": 30, "stop_beyond": 4, "stop_min": 12, "stop_max": 32, "rr": 2.0,
            "max_min": 15, "inside_only": False, "last_sec": 55800.0, "data_end_sec": 56700.0},
}
BIN = V1.BIN
UP = ("prev_vah", "prev_high", "night_high")
DN = ("prev_val", "prev_low", "night_low")


def failed_auction(s, ref, thr, p=None):
    p = p or PARAMS["FAF"]
    if not ref or not thr or ref.get("prev_vah") is None or ref.get("prev_val") is None:
        return []
    i, j = s.idx_sec(NY_OPEN), s.idx_sec(p["data_end_sec"])
    if j - i < 50:
        return []
    if p.get("inside_only") and not (ref["prev_val"] <= s.px[i] <= ref["prev_vah"]):
        return []                      # variante: solo días que abren dentro del valor de ayer
    buy, sell, hi, lo, first, last = V1._bins(s, i, j)
    nb = len(buy); W = 60 // BIN; D = max(1, int(p["delta_s"] // BIN)); F = int(p["fail_s"] // BIN)
    if nb < 2 * W:
        return []
    k = np.ones(W)
    bw = np.convolve(buy, k, "valid"); sw = np.convolve(sell, k, "valid")      # bw[x] = compras en celdas x..x+W-1
    cb = np.concatenate([[0.0], np.cumsum(buy)]); cs = np.concatenate([[0.0], np.cumsum(sell)])
    used = set(); out = []
    for e in range(W - 1, nb - 1):
        if NY_OPEN + (e + 1) * BIN > p["last_sec"]:
            break
        for side, names, thr_key in ((1, UP, "buy60_p95"), (-1, DN, "sell60_p95")):
            volw = (bw if side > 0 else sw)[e - W + 1]
            if volw < p["burst_frac"] * thr[thr_key]:
                continue
            for nm in names:
                lvl = ref.get(nm)
                if lvl is None or nm in used:
                    continue
                crossed = hi[e] >= lvl + p["pen_ticks"] if side > 0 else lo[e] <= lvl - p["pen_ticks"]
                if not crossed or (e > 0 and ((hi[e - 1] >= lvl + p["pen_ticks"]) if side > 0 else (lo[e - 1] <= lvl - p["pen_ticks"]))):
                    continue           # solo la primera celda que cruza
                used.add(nm)
                ext = int(hi[e]) if side > 0 else int(lo[e]); conf = None
                for f in range(e + 1, min(nb, e + 1 + F)):
                    ext = max(ext, int(hi[f])) if side > 0 else min(ext, int(lo[f]))
                    back = last[f] <= lvl if side > 0 else last[f] >= lvl
                    if not back:
                        continue
                    a = max(0, f + 1 - D)
                    d = (cb[f + 1] - cb[a]) - (cs[f + 1] - cs[a])
                    if (side > 0 and d < 0) or (side < 0 and d > 0):
                        conf = f
                    break              # volvió al nivel: se evalúa una sola vez
                if conf is None:
                    continue
                entry_est = int(last[conf])
                dist = abs(ext + side * p["stop_beyond"] - entry_est)
                stop = int(min(max(dist, p["stop_min"]), p["stop_max"]))
                out.append(Signal(sec=NY_OPEN + (conf + 1) * BIN, side=-side, stop_ticks=stop, target_ticks=int(round(p["rr"] * stop)),
                                  max_sec=p["max_min"] * 60, kind="FAF", level=nm,
                                  meta={"burst_vol": float(volw), "extreme": ext / 4, "side_failed": side}))
    out.sort(key=lambda x: x.sec)
    return out


REGISTRY = {"FAF": failed_auction}
