"""Estrategias v14 (tanda 15), congeladas en futures/strategies/v16.json.
  ABD v1 : ABSORCIÓN EN LOS NIVELES DE AYER, SOLO EN DÍAS QUE ABREN DENTRO DEL VALOR, TODA LA SESIÓN (09:40–15:30 ET).
           Detector, niveles (ayer + noche), confirmación y salida de ABS v1 (v1.py::absorption: stop 12–32, objetivo 2R, 15 min).
           Cambios: (1) filtro de apertura dentro del valor de ayer; (2) ventana de entradas hasta las 15:30; (3) umbral de volumen
           = el menor entre el p95 de 20 sesiones (ABS v1) y el p95 de la hora anterior (como ABI v2), con piso de 0.5 × el primero:
           la mañana queda igual que ABS v1 y la tarde no queda sin señales.
           Investigación y justificación: docs/investigacion/absorcion_dias_balance.md.
"""
import numpy as np
from ..sim import Signal
from ..data import NY_OPEN
from . import v1 as V1

PARAMS = {
    "ABD": {"near_ticks": 4, "max_advance": 2, "confirm_s": 60, "away_ticks": 4, "stop_beyond": 4, "stop_min": 12, "stop_max": 32, "rr": 2.0,
            "max_min": 15, "min_elapsed_s": 0, "rel_pct": 90, "rel_lookback_s": 3600, "floor_frac": 0.5,
            "last_sec": 55800.0, "data_end_sec": 56700.0},   # entradas hasta 15:30, datos hasta 15:45 ET
}
BIN = V1.BIN


def absorption_balance_days(s, ref, thr, p=None):
    p = p or PARAMS["ABD"]
    if not ref or not thr or ref.get("prev_vah") is None or ref.get("prev_val") is None:
        return []
    i, j = s.idx_sec(NY_OPEN), s.idx_sec(p["data_end_sec"])
    if j - i < 50:
        return []
    if not (ref["prev_val"] <= s.px[i] <= ref["prev_vah"]):
        return []                      # abre fuera del valor de ayer: el filtro excluye el día (dato de las 09:30)
    buy, sell, hi, lo, first, last = V1._bins(s, i, j)
    nb = len(buy); W = 60 // BIN
    if nb < 2 * W:
        return []
    k = np.ones(W)
    bw = np.convolve(buy, k, "valid"); sw = np.convolve(sell, k, "valid")
    lv = V1._ref_levels(ref); used = set(); out = []
    for e in range(W - 1, nb - W):
        w0 = e - W + 1
        if w0 * BIN < p["min_elapsed_s"]:
            continue
        if NY_OPEN + (e + 1) * BIN > p["last_sec"]:
            break
        for side, volw, thr_key in ((1, bw[w0], "buy60_p95"), (-1, sw[w0], "sell60_p95")):
            if volw < p["floor_frac"] * thr[thr_key]:
                continue
            a0 = max(0, w0 - W - p["rel_lookback_s"] // BIN + 1); a1 = w0 - W + 1   # ventanas terminadas antes de w0
            lim = thr[thr_key]
            if a1 - a0 >= 60:                      # con menos de 10 min de cinta se usa solo el umbral de 20 sesiones
                lim = min(lim, np.percentile(np.concatenate([bw[a0:a1], sw[a0:a1]]), p["rel_pct"]))
            if volw < lim:
                continue                  # umbral = el MENOR entre p95 de 20 sesiones y p95 de la hora anterior (piso 0.5 × el de 20 sesiones)
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
            conf = None
            for f in range(e + 1, min(nb, e + 1 + p["confirm_s"] // BIN)):
                dw = bw[f - W + 1] - sw[f - W + 1] if f - W + 1 >= 0 else 0
                if side > 0 and dw < 0 and lo[f] <= ext - p["away_ticks"]:
                    conf = f; break
                if side < 0 and dw > 0 and hi[f] >= ext + p["away_ticks"]:
                    conf = f; break
            if conf is None:
                continue
            used.add(name)
            t_conf = NY_OPEN + (conf + 1) * BIN
            entry_est = int(last[conf])
            dist = abs(ext + side * p["stop_beyond"] - entry_est)
            stop = int(min(max(dist, p["stop_min"]), p["stop_max"]))
            out.append(Signal(sec=t_conf, side=-side, stop_ticks=stop, target_ticks=int(round(p["rr"] * stop)),
                              max_sec=p["max_min"] * 60, kind="ABD", level=name,
                              meta={"absorbed_vol": float(volw), "extreme": ext / 4, "side_absorbed": side}))
    out.sort(key=lambda x: x.sec)
    return out


REGISTRY = {"ABD": absorption_balance_days}
