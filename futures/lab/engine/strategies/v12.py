"""Estrategias v12 (tanda 13), congeladas en futures/strategies/v14.json.
  LVN v1 : TRAVESÍA DE UN VACÍO DE VOLUMEN (LVN) DEL PERFIL DE AYER CON FLUJO INICIADOR.
           Teoría de subasta: donde ayer casi no se operó, el mercado no encontró valor; si hoy entra ahí con flujo agresivo a favor
           (iniciativa), cruza rápido hasta el otro borde. Es lo contrario de HVN/HVF (rechazo) y de ABS (absorción).
           Investigación y justificación: docs/investigacion/lvn.md.
"""
import numpy as np
from ..sim import Signal
from ..data import NY_OPEN
from . import v1 as V1

PARAMS = {
    "LVN": {"lvn_pct": 20, "delta_pct": 10, "min_width": 16, "stop_beyond": 4, "max_min": 15, "bucket": 8, "edge_skip": 16,
            "min_target": 12, "max_target": 40, "stop_min": 8, "stop_max": 24},
}
BIN = V1.BIN


def lvn_zones(prof, p):
    """Zonas de vacío del perfil NY de ayer: [(lo, hi)] en ticks. Cubos de `bucket` ticks; se ignoran `edge_skip` ticks en cada punta
    del rango (las colas siempre son finas); cubo fino = volumen ≤ percentil lvn_pct de los cubos del rango; zona = racha de cubos finos."""
    if prof is None or len(prof) < 10:
        return []
    px = prof[:, 0].astype(int); v = prof[:, 1].astype(float)
    b0 = px.min(); nbk = (px.max() - b0) // p["bucket"] + 1
    vb = np.bincount((px - b0) // p["bucket"], weights=v, minlength=nbk)
    k0 = p["edge_skip"] // p["bucket"]
    inner = np.arange(k0, nbk - k0)
    if len(inner) < 4:
        return []
    thr = np.percentile(vb[inner], p["lvn_pct"])
    thin = np.zeros(nbk, bool); thin[inner] = vb[inner] <= thr
    zones, k = [], 0
    while k < nbk:
        if thin[k]:
            m = k
            while m + 1 < nbk and thin[m + 1]:
                m += 1
            lo, hi = int(b0 + k * p["bucket"]), int(b0 + (m + 1) * p["bucket"] - 1)
            if hi - lo + 1 >= p["min_width"]:
                zones.append((lo, hi))
            k = m + 1
        else:
            k += 1
    return zones


def lvn_cross(s, ref, thr, p=None, prof=None):
    """Primer cruce de cada vacío (solo el borde de entrada, con datos hasta la celda de decisión):
      · el último precio de la celda anterior estaba fuera del vacío y la celda actual entra ≥ 2 ticks adentro;
      · iniciador: el delta agresivo de los últimos 60 s va en la dirección del cruce y vale ≥ delta_pct % del volumen de esos 60 s;
      · entrada a mercado en la dirección del cruce; objetivo = el borde lejano del vacío (entre min_target y max_target ticks);
        stop = detrás del borde de entrada `stop_beyond` ticks (entre stop_min y stop_max); 15 min.
    Cada vacío se decide una sola vez (a su primer cruce), tenga o no la señal."""
    p = p or PARAMS["LVN"]
    zones = lvn_zones(prof, p)
    if not zones:
        return []
    i, j = s.idx_sec(NY_OPEN), s.idx_sec(NY_OPEN + 2 * 3600 + 15 * 60)
    buy, sell, hi, lo, first, last = V1._bins(s, i, j)
    nb = len(buy); W = 60 // BIN
    if nb < 2 * W:
        return []
    k = np.ones(W)
    bw = np.convolve(buy, k, "valid"); sw = np.convolve(sell, k, "valid")
    out = []; done = set()
    for f in range(W, nb):
        w0 = f - W + 1
        for zi, (zlo, zhi) in enumerate(zones):
            if zi in done:
                continue
            side = 0
            if last[f - 1] < zlo and hi[f] >= zlo + 2:
                side = 1
            elif last[f - 1] > zhi and lo[f] <= zhi - 2:
                side = -1
            if not side:
                continue
            done.add(zi)
            tot = bw[w0] + sw[w0]
            if tot <= 0 or side * (bw[w0] - sw[w0]) < p["delta_pct"] / 100.0 * tot:
                continue
            entry_est = int(last[f])
            far = zhi if side > 0 else zlo
            tgt = (far - entry_est) * side
            if tgt < p["min_target"]:
                continue
            tgt = min(tgt, p["max_target"])
            near = zlo if side > 0 else zhi
            stop = int(min(max((entry_est - near) * side + p["stop_beyond"], p["stop_min"]), p["stop_max"]))
            out.append(Signal(sec=NY_OPEN + (f + 1) * BIN, side=side, stop_ticks=stop, target_ticks=int(tgt),
                              max_sec=p["max_min"] * 60, kind="LVN", level=f"lvn_{zlo / 4}-{zhi / 4}",
                              meta={"lvn_lo": zlo / 4, "lvn_hi": zhi / 4, "delta_pct": float(side * (bw[w0] - sw[w0]) / tot)}))
    out.sort(key=lambda x: x.sec)
    return out


REGISTRY = {"LVN": lvn_cross}
