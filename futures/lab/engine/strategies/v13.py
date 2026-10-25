"""Estrategias v13 (tanda 14), congeladas en futures/strategies/v15.json.
  ABI v2 : ABSORCIÓN EN LOS NIVELES DEL PROPIO DÍA, SOLO EN LA TARDE DE NUEVA YORK (11:30–15:30 ET).
           Es exactamente el detector de ABI v1 (v8.py::absorption_intraday); lo único que cambia es la ventana de entradas.
           Los niveles (máximo/mínimo de la sesión, VWAP, POC/VAH/VAL en desarrollo) se siguen calculando desde las 09:30,
           con lo ocurrido hasta cada momento. Las operaciones de la mañana (09:30–11:30) ya las midió ABI v1 (P021) y no se repiten.
           Investigación y justificación: docs/investigacion/ventana_tarde.md.
"""
import numpy as np
from ..sim import Signal
from ..data import NY_OPEN
from . import v1 as V1
from . import v8 as V8

PARAMS = {
    "ABI2": {"near_ticks": 4, "max_advance": 2, "confirm_s": 60, "away_ticks": 4, "stop_beyond": 4, "stop_min": 12, "stop_max": 32,
             "max_min": 15, "min_elapsed_s": 600, "cooldown_s": 600,
             "rel_pct": 95, "rel_lookback_s": 3600, "floor_frac": 0.5,
             "first_sec": 41400.0, "last_sec": 55800.0, "data_end_sec": 56700.0},   # 11:30, 15:30 y 15:45 ET
}
BIN = V1.BIN


def absorption_intraday_pm(s, ref, thr, p=None):
    """Igual que ABI v1 (mismo detector, mismos niveles, misma confirmación y salida por tiempo), con la ventana de entradas
    desplazada a la tarde: la señal se emite solo si su momento de entrada cae entre `first_sec` y `last_sec`.
    ÚNICO CAMBIO DEL DETECTOR: el umbral de "volumen agresivo grande en 60 s". En la tarde el p95 de las 20 sesiones anteriores (todo el día)
    casi nunca se alcanza (2 señales en 57 sesiones), así que el umbral es relativo a la hora: el percentil `rel_pct` de los volúmenes
    agresivos de 60 s (compra y venta juntas, paso de 10 s) que TERMINARON en los `rel_lookback_s` anteriores al inicio de la ventana
    (solo la cinta del propio día, nada futuro), con un piso de `floor_frac` × el p95 de las 20 sesiones anteriores para no disparar en horas muertas.
    Los datos se leen de 09:30 a `data_end_sec` (los niveles necesitan toda la sesión), pero cada decisión usa solo lo anterior a ella."""
    p = p or PARAMS["ABI2"]
    if not thr:
        return []
    i, j = s.idx_sec(NY_OPEN), s.idx_sec(p["data_end_sec"])
    buy, sell, hi, lo, first, last = V1._bins(s, i, j)
    nb = len(buy); W = 60 // BIN
    if nb < 2 * W:
        return []
    k = np.ones(W)
    bw = np.convolve(buy, k, "valid"); sw = np.convolve(sell, k, "valid")
    px = s.px[i:j].astype(float); vol = s.vol[i:j].astype(float); sec = s.sec[i:j]
    b = ((sec - NY_OPEN) // BIN).astype(int)
    pv = np.bincount(b, weights=px * vol, minlength=nb)[:nb].cumsum()
    vv = np.bincount(b, weights=vol, minlength=nb)[:nb].cumsum()
    run_hi = np.maximum.accumulate(hi); run_lo = np.minimum.accumulate(lo)
    d_poc, d_vah, d_val = V8._developing_profile(px, vol, b, nb)
    last_used = {}; out = []
    for e in range(W - 1, nb - W):
        w0 = e - W + 1
        if w0 * BIN < p["min_elapsed_s"]:
            continue
        if NY_OPEN + (e + 1) * BIN < p["first_sec"]:
            continue                      # la mañana ya la midió ABI v1
        if NY_OPEN + (e + 1) * BIN > p["last_sec"]:
            break
        for side, volw, thr_key in ((1, bw[w0], "buy60_p95"), (-1, sw[w0], "sell60_p95")):
            if volw < p["floor_frac"] * thr[thr_key]:
                continue
            a0 = max(0, w0 - W - p["rel_lookback_s"] // BIN + 1); a1 = w0 - W + 1   # ventanas de 60 s terminadas antes de w0
            if a1 - a0 < 60:
                continue
            if volw < np.percentile(np.concatenate([bw[a0:a1], sw[a0:a1]]), p["rel_pct"]):
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
            cands = []
            if side > 0:
                cands += [("day_high", int(run_hi[w0 - 1])), ("dev_vah", int(d_vah[w0 - 1]))]
            else:
                cands += [("day_low", int(run_lo[w0 - 1])), ("dev_val", int(d_val[w0 - 1]))]
            if vv[w0 - 1] > 0:
                cands += [("vwap", int(round(pv[w0 - 1] / vv[w0 - 1]))), ("dev_poc", int(d_poc[w0 - 1]))]
            name = None; best = None
            for nm, lvl in cands:
                d = abs(ext - lvl)
                if d <= p["near_ticks"] and (best is None or d < best):
                    best, name = d, nm
            if not name:
                continue
            t_sig = NY_OPEN + (e + 1) * BIN
            if name in last_used and t_sig - last_used[name] < p["cooldown_s"]:
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
            last_used[name] = t_conf
            entry_est = int(last[conf])
            dist = abs(ext + side * p["stop_beyond"] - entry_est)
            stop = int(min(max(dist, p["stop_min"]), p["stop_max"]))
            out.append(Signal(sec=t_conf, side=-side, stop_ticks=stop, target_ticks=None, max_sec=p["max_min"] * 60,
                              kind="ABI2", level=name, meta={"absorbed_vol": float(volw), "extreme": ext / 4, "side_absorbed": side}))
    out.sort(key=lambda x: x.sec)
    return out


REGISTRY = {"ABI2": absorption_intraday_pm}
