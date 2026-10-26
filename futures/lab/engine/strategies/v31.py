"""Estrategias v31 (tanda 32), congeladas en futures/strategies/v33.json.
  OPD v1 : APERTURA IMPULSIVA (OPEN DRIVE) MEDIDA POR FLUJO. Dalton: en un "open drive" el precio sale de la apertura en una dirección
           y no mira atrás: es iniciativa de los participantes de corto plazo y suele marcar el día. Aquí se mide con flujo agresivo:
           en los primeros `win_s` segundos desde las 09:30, (1) el delta agresivo es >= delta_min del volumen en una dirección,
           (2) el precio avanza >= move_min ticks en esa dirección, y (3) el mayor retroceso desde el extremo del avance es <= retrace
           del avance. Si se cumple, entrada a mercado a favor al cerrar la ventana. Stop = contra-extremo de la ventana (12-32 ticks),
           objetivo 1.5R, salida a 15 min. Una vez por día. 2 contratos.
           Investigación: docs/investigacion/apertura_impulsiva.md.
"""
import numpy as np
from ..sim import Signal
from ..data import NY_OPEN
from . import v1 as V1

PARAMS = {
    "OPD": {"win_s": 300, "delta_min": 0.03, "move_min": 40, "retrace": 1.0, "stop_min": 12, "stop_max": 32, "rr": 1.5, "max_min": 15,
            "data_end_sec": 36000.0},
}
BIN = V1.BIN
CONTRACTS = 2
MAX_CONSEC_LOSSES = 2


def open_drive(s, ref, thr, p=None):
    p = p or PARAMS["OPD"]
    if not ref:
        return []
    i, j = s.idx_sec(NY_OPEN), s.idx_sec(p["data_end_sec"])
    if j - i < 50:
        return []
    buy, sell, hi, lo, first, last = V1._bins(s, i, j)
    nb = int(p["win_s"] // BIN)
    if len(buy) < nb:
        return []
    b, sl = float(buy[:nb].sum()), float(sell[:nb].sum())
    tot = b + sl
    if tot <= 0:
        return []
    delta = (b - sl) / tot
    side = 1 if delta > 0 else -1
    if abs(delta) < p["delta_min"]:
        return []
    h, l = int(hi[:nb].max()), int(lo[:nb].min())
    p0, p1 = int(first[0]), int(last[nb - 1])
    move = (p1 - p0) * side
    if move < p["move_min"]:
        return []
    # mayor retroceso desde el extremo corrido del avance
    ext = np.maximum.accumulate(hi[:nb]) if side > 0 else np.minimum.accumulate(lo[:nb])
    adverse = (ext - lo[:nb]) if side > 0 else (hi[:nb] - ext)
    if adverse.max() > p["retrace"] * max(move, 1):
        return []
    dist = (p1 - l) if side > 0 else (h - p1)
    stop = int(min(max(dist, p["stop_min"]), p["stop_max"]))
    t_sig = NY_OPEN + nb * BIN
    return [Signal(sec=t_sig, side=side, stop_ticks=stop, target_ticks=int(round(p["rr"] * stop)), max_sec=p["max_min"] * 60,
                   kind="OPD", level="open",
                   meta={"delta_share": float(delta), "move": move / 4, "retrace_max": float(adverse.max()) / 4})]


REGISTRY = {"OPD": open_drive}
