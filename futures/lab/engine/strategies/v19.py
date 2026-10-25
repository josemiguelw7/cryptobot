"""Estrategias v19 (tanda 20), congeladas en futures/strategies/v21.json.
  ABT v1 : ABSORCIÓN A FAVOR DE LA TENDENCIA — días que abren FUERA del valor de ayer (los que ABU/ABD dejan fuera).
           Si abre por encima del VAH de ayer, solo se compra la venta agresiva absorbida (retroceso aceptado hacia un nivel);
           si abre por debajo del VAL de ayer, solo se vende la compra agresiva absorbida. El sesgo se fija con el primer precio de las 09:30.
           Detector, niveles (ayer, noche, POC/VAH/VAL en desarrollo), umbral relativo, confirmación a 60 s, stop 12–32, objetivo 2R,
           salida a 15 min y ventana 09:30–15:30: idénticos a ABU v1 (v17.py). 1 contrato.
           Cambios (solo dos): el filtro de día se invierte y la dirección queda atada al lado de la apertura respecto al valor.
           Investigación y justificación: docs/investigacion/absorcion_tendencia.md.
"""
import numpy as np
from ..sim import Signal
from ..data import NY_OPEN
from . import v1 as V1
from .v8 import _developing_profile

PARAMS = {
    "ABT": {"near_ticks": 4, "max_advance": 2, "confirm_s": 60, "away_ticks": 4, "stop_beyond": 4, "stop_min": 12, "stop_max": 32, "rr": 2.0,
            "max_min": 15, "min_elapsed_s": 0, "dev_min_elapsed_s": 600, "dev_cooldown_s": 600, "rel_pct": 90, "rel_lookback_s": 3600,
            "floor_frac": 0.5, "last_sec": 55800.0, "data_end_sec": 56700.0},
}
BIN = V1.BIN


def absorption_trend(s, ref, thr, p=None):
    p = p or PARAMS["ABT"]
    if not ref or not thr or ref.get("prev_vah") is None or ref.get("prev_val") is None:
        return []
    i, j = s.idx_sec(NY_OPEN), s.idx_sec(p["data_end_sec"])
    if j - i < 50:
        return []
    if s.px[i] > ref["prev_vah"]:
        bias = 1                       # abre por encima del valor de ayer (dato de las 09:30): solo largos
    elif s.px[i] < ref["prev_val"]:
        bias = -1                      # abre por debajo: solo cortos
    else:
        return []                      # abre dentro del valor: es territorio de ABU
    buy, sell, hi, lo, first, last = V1._bins(s, i, j)
    nb = len(buy); W = 60 // BIN
    if nb < 2 * W:
        return []
    k = np.ones(W)
    bw = np.convolve(buy, k, "valid"); sw = np.convolve(sell, k, "valid")
    px = s.px[i:j].astype(float); vol = s.vol[i:j].astype(float); sec = s.sec[i:j]
    b = ((sec - NY_OPEN) // BIN).astype(int)
    d_poc, d_vah, d_val = _developing_profile(px, vol, b, nb)
    lv = V1._ref_levels(ref); used = set(); last_dev = {}; out = []
    for e in range(W - 1, nb - W):
        w0 = e - W + 1
        if w0 * BIN < p["min_elapsed_s"]:
            continue
        if NY_OPEN + (e + 1) * BIN > p["last_sec"]:
            break
        for side, volw, thr_key in ((1, bw[w0], "buy60_p95"), (-1, sw[w0], "sell60_p95")):
            if side == bias:
                continue                          # la absorción debe ser del flujo CONTRA el sesgo (entrada a favor de él)
            if volw < p["floor_frac"] * thr[thr_key]:
                continue
            a0 = max(0, w0 - W - p["rel_lookback_s"] // BIN + 1); a1 = w0 - W + 1
            lim = thr[thr_key]
            if a1 - a0 >= 60:
                lim = min(lim, np.percentile(np.concatenate([bw[a0:a1], sw[a0:a1]]), p["rel_pct"]))
            if volw < lim:
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
            cands = list(lv.items())
            if w0 * BIN >= p["dev_min_elapsed_s"] and w0 >= 1:
                cands.append(("dev_vah" if side > 0 else "dev_val", int(d_vah[w0 - 1] if side > 0 else d_val[w0 - 1])))
                cands.append(("dev_poc", int(d_poc[w0 - 1])))
            name = None; best = None
            for nm, lvl in cands:
                if lvl <= 0:
                    continue                      # perfil en desarrollo aún sin volumen
                d = abs(ext - lvl)
                if d <= p["near_ticks"] and (best is None or d < best):
                    best, name = d, nm
            if not name:
                continue
            dev = name.startswith("dev_")
            t_sig = NY_OPEN + (e + 1) * BIN
            if dev:
                if name in last_dev and t_sig - last_dev[name] < p["dev_cooldown_s"]:
                    continue
            elif name in used:
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
            t_conf = NY_OPEN + (conf + 1) * BIN
            if dev:
                last_dev[name] = t_conf
            else:
                used.add(name)
            entry_est = int(last[conf])
            dist = abs(ext + side * p["stop_beyond"] - entry_est)
            stop = int(min(max(dist, p["stop_min"]), p["stop_max"]))
            out.append(Signal(sec=t_conf, side=-side, stop_ticks=stop, target_ticks=int(round(p["rr"] * stop)),
                              max_sec=p["max_min"] * 60, kind="ABT", level=name,
                              meta={"absorbed_vol": float(volw), "extreme": ext / 4, "side_absorbed": side}))
    out.sort(key=lambda x: x.sec)
    return out


REGISTRY = {"ABT": absorption_trend}
