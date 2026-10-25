"""Estrategias v9 (tanda 10), congeladas en futures/strategies/v11.json.
  ABV v1 : ABSORCIÓN en los bordes y el centro del VALOR EN DESARROLLO del propio día (POC, VAH y VAL del perfil de las
           operaciones ocurridas hasta ese momento). Es ABI v1 (v8.py) sin máximo/mínimo de la sesión ni VWAP, con la
           tolerancia de cercanía y el enfriamiento ajustados para tener suficientes operaciones.
           Investigación y justificación: docs/investigacion/absorcion_valor_desarrollo.md.
"""
import numpy as np
from ..sim import Signal
from ..data import NY_OPEN
from . import v1 as V1
from . import v8 as V8

PARAMS = {
    "ABV": {"near_ticks": 8, "max_advance": 2, "confirm_s": 60, "away_ticks": 4, "stop_beyond": 4, "stop_min": 12, "stop_max": 32,
            "max_min": 15, "min_elapsed_s": 600, "cooldown_s": 300},
}
BIN = V1.BIN


def absorption_value(s, ref, thr, p=None):
    """Detector de ABS v1 (≥ p95 de volumen agresivo de un lado en 60 s sin que el precio avance más de `max_advance` ticks;
    confirmación en los `confirm_s` siguientes: el delta de la ventana cambia de signo y el precio se aleja `away_ticks` del
    extremo; entrada a mercado EN CONTRA del lado absorbido; stop `stop_beyond` ticks más allá del extremo, entre `stop_min` y
    `stop_max`; sin objetivo; salida por tiempo `max_min`), con tres niveles del perfil de la sesión en curso, calculados SOLO
    con operaciones anteriores al inicio de la ventana (70% del volumen acumulado):
      · VAH en desarrollo — solo compra agresiva absorbida (el comprador no pasa del borde alto) -> entra en corto
      · VAL en desarrollo — solo venta agresiva absorbida -> entra en largo
      · POC en desarrollo — cualquiera de los dos lados
    El extremo debe estar a ≤ `near_ticks` (2 puntos) del nivel. Nada antes de `min_elapsed_s` (10 min): con menos tiempo el
    perfil es una sola barra (20 min daba solo 86 señales, 10 min da 132). Un disparo por nivel cada `cooldown_s` (5 min)."""
    p = p or PARAMS["ABV"]
    if not thr:
        return []
    i, j = s.idx_sec(NY_OPEN), s.idx_sec(NY_OPEN + 2 * 3600 + 15 * 60)
    buy, sell, hi, lo, first, last = V1._bins(s, i, j)
    nb = len(buy); W = 60 // BIN
    if nb < 2 * W:
        return []
    k = np.ones(W)
    bw = np.convolve(buy, k, "valid"); sw = np.convolve(sell, k, "valid")
    px = s.px[i:j].astype(float); vol = s.vol[i:j].astype(float); sec = s.sec[i:j]
    b = ((sec - NY_OPEN) // BIN).astype(int)
    d_poc, d_vah, d_val = V8._developing_profile(px, vol, b, nb)
    last_used = {}; out = []
    for e in range(W - 1, nb - W):
        w0 = e - W + 1
        if w0 * BIN < p["min_elapsed_s"]:
            continue
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
            cands = [("dev_vah", int(d_vah[w0 - 1]))] if side > 0 else [("dev_val", int(d_val[w0 - 1]))]
            cands.append(("dev_poc", int(d_poc[w0 - 1])))
            name = None; best = None
            for nm, lvl in cands:
                d = abs(ext - lvl)
                if lvl > 0 and d <= p["near_ticks"] and (best is None or d < best):
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
                              kind="ABV", level=name, meta={"absorbed_vol": float(volw), "extreme": ext / 4, "side_absorbed": side}))
    out.sort(key=lambda x: x.sec)
    return out


REGISTRY = {"ABV": absorption_value}
