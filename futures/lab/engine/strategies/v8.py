"""Estrategias v8 (tanda 9), congeladas en futures/strategies/v10.json.
  ABI v1 : ABSORCIÓN en los niveles del PROPIO día (máximo y mínimo de la sesión en curso, VWAP y POC/VAH/VAL del perfil en desarrollo), no del día anterior.
           Mismo detector de flujo que ABS v1 (v1.py::absorption); cambia el universo de niveles.
           Investigación y justificación: docs/investigacion/absorcion_intradia.md.
"""
import numpy as np
from ..sim import Signal
from ..data import NY_OPEN
from . import v1 as V1

PARAMS = {
    "ABI": {"near_ticks": 4, "max_advance": 2, "confirm_s": 60, "away_ticks": 4, "stop_beyond": 4, "stop_min": 12, "stop_max": 32,
            "max_min": 15, "min_elapsed_s": 600, "cooldown_s": 600},
}
BIN = V1.BIN


def _developing_profile(px, vol, b, nb):
    """POC, VAH y VAL (70% del volumen) del perfil de la sesión en curso al final de cada celda de 10 s, usando solo lo ocurrido hasta ahí.
    Devuelve tres arreglos de longitud nb (en ticks; 0 mientras no hay volumen).

    Corrección 2026-10-29 (motor 1.2.0): la rejilla de precios del histograma crece con los precios VISTOS hasta la celda k.
    Antes se dimensionaba con el mínimo y el máximo de toda la rebanada (incluido el futuro): el paso de expansión del área de
    valor (1 o 2 ticks) dependía del borde de esa rejilla, así que un precio extremo posterior podía mover el VAH/VAL de una
    celda anterior. Ahora nada posterior a la celda k entra en el cálculo de la celda k."""
    poc = np.zeros(nb, dtype=int); vah = np.zeros(nb, dtype=int); val = np.zeros(nb, dtype=int)
    order = np.argsort(b, kind="stable"); bs = b[order]
    edges = np.searchsorted(bs, np.arange(nb + 1))
    hist = None; lo = 0                      # hist[i] = volumen en el precio lo + i; cubre SOLO precios ya vistos
    for k in range(nb):
        idx = order[edges[k]:edges[k + 1]]
        if len(idx):
            pk = px[idx].astype(int); pmin = int(pk.min()); pmax = int(pk.max())
            if hist is None:
                lo = pmin; hist = np.zeros(pmax - pmin + 1)
            else:
                if pmin < lo:
                    hist = np.concatenate([np.zeros(lo - pmin), hist]); lo = pmin
                top = lo + len(hist) - 1
                if pmax > top:
                    hist = np.concatenate([hist, np.zeros(pmax - top)])
            np.add.at(hist, pk - lo, vol[idx])
        if hist is None:
            continue
        tot = hist.sum()
        if tot <= 0:
            continue
        n = len(hist)
        c = int(np.argmax(hist)); a = z = c; acc = hist[c]
        while acc < 0.7 * tot and (a > 0 or z < n - 1):
            up = hist[z + 1] + (hist[z + 2] if z + 2 < n else 0) if z < n - 1 else -1
            dn = hist[a - 1] + (hist[a - 2] if a - 2 >= 0 else 0) if a > 0 else -1
            if up >= dn:
                step = 2 if z + 2 < n else 1; z += step; acc += up
            else:
                step = 2 if a - 2 >= 0 else 1; a -= step; acc += dn
        poc[k] = c + lo; vah[k] = z + lo; val[k] = a + lo
    return poc, vah, val


def absorption_intraday(s, ref, thr, p=None):
    """Detector de ABS v1 (≥ p95 de volumen agresivo de un lado en 60 s sin que el precio avance más de `max_advance` ticks;
    extremo a ≤ `near_ticks` de un nivel; confirmación en los `confirm_s` siguientes: el delta de la ventana cambia de signo y el
    precio se aleja `away_ticks` del extremo; entrada a mercado EN CONTRA del lado absorbido; stop `stop_beyond` ticks más allá del
    extremo, entre `stop_min` y `stop_max`; sin objetivo; salida por tiempo `max_min`), con niveles del propio día calculados
    SOLO con operaciones anteriores al inicio de la ventana:
      · máximo de la sesión (desde las 09:30) — solo absorción de COMPRA agresiva (el comprador no pasa) -> entra en corto
      · mínimo de la sesión — solo absorción de VENTA agresiva -> entra en largo
      · VAH del perfil en desarrollo (70% del volumen de la sesión hasta ese momento) — solo compra agresiva absorbida
      · VAL del perfil en desarrollo — solo venta agresiva absorbida
      · VWAP y POC del perfil en desarrollo — cualquiera de los dos lados
    Nada antes de `min_elapsed_s` (10 min) desde la apertura: un máximo de 2 minutos no es un nivel.
    Un disparo por nivel cada `cooldown_s` (10 min): el máximo y el mínimo se mueven durante el día."""
    p = p or PARAMS["ABI"]
    if not thr:
        return []
    i, j = s.idx_sec(NY_OPEN), s.idx_sec(NY_OPEN + 2 * 3600 + 15 * 60)
    buy, sell, hi, lo, first, last = V1._bins(s, i, j)
    nb = len(buy); W = 60 // BIN
    if nb < 2 * W:
        return []
    k = np.ones(W)
    bw = np.convolve(buy, k, "valid"); sw = np.convolve(sell, k, "valid")
    # VWAP acumulado por celda de 10 s (ponderado por contratos), solo con lo ocurrido hasta el final de cada celda
    px = s.px[i:j].astype(float); vol = s.vol[i:j].astype(float); sec = s.sec[i:j]
    b = ((sec - NY_OPEN) // BIN).astype(int)
    pv = np.bincount(b, weights=px * vol, minlength=nb)[:nb].cumsum()
    vv = np.bincount(b, weights=vol, minlength=nb)[:nb].cumsum()
    run_hi = np.maximum.accumulate(hi); run_lo = np.minimum.accumulate(lo)
    d_poc, d_vah, d_val = _developing_profile(px, vol, b, nb)
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
                              kind="ABI", level=name, meta={"absorbed_vol": float(volw), "extreme": ext / 4, "side_absorbed": side}))
    out.sort(key=lambda x: x.sec)
    return out


REGISTRY = {"ABI": absorption_intraday}
