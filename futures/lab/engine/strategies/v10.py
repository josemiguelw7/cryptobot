"""Estrategias v10 (tanda 11), congeladas en futures/strategies/v12.json.
  HVF v1 : ABSORCIÓN de flujo agresivo en un HVN PODEROSO del perfil de Nueva York del día anterior (E-HVN-FUERZA, pedido de Oscar).
           HVN poderoso = nodo (grupo contiguo de precios con volumen >= percentil `hvn_pct` del perfil de ayer) que además
           (1) tiene CONFLUENCIA: su pico queda a <= `conf_ticks` (32 = 8 puntos) del POC, VAH o VAL de ayer.
           El detector de flujo es el de ABS v1/v2 (confirmación a 60 s, stop más allá del extremo, sin objetivo, salida a 15 min).
           Investigación: docs/investigacion/hvn_poderoso.md.
"""
import numpy as np
from ..sim import Signal
from ..data import NY_OPEN
from . import v1 as V1

PARAMS = {
    "HVF": {"hvn_pct": 95, "conf_ticks": 32, "near_ticks": 4, "max_advance": 2, "confirm_s": 60, "away_ticks": 4,
            "stop_beyond": 4, "stop_min": 12, "stop_max": 32, "max_min": 15, "min_elapsed_s": 0},
}
BIN = V1.BIN


def hvn_zones(prof, ref, pct, conf_ticks):
    """Zonas HVN poderosas de ayer: [(lo, hi, pico)] en ticks. Un grupo contiguo (huecos <= 2 ticks) de precios con volumen >=
    percentil `pct`; poderoso solo si su pico está a <= conf_ticks del POC/VAH/VAL de ayer."""
    if prof is None or not len(prof) or not ref:
        return []
    pxs = prof[:, 0].astype(int); vs = prof[:, 1].astype(float)
    order = np.argsort(pxs); pxs, vs = pxs[order], vs[order]
    sel = vs >= np.percentile(vs, pct)
    ps, vv = pxs[sel], vs[sel]
    if not len(ps):
        return []
    cuts = np.r_[0, np.flatnonzero(np.diff(ps) > 2) + 1, len(ps)]
    keys = [ref[k] for k in ("prev_poc", "prev_vah", "prev_val") if ref.get(k) is not None]
    out = []
    for a, b in zip(cuts[:-1], cuts[1:]):
        peak = int(ps[a:b][np.argmax(vv[a:b])])
        if keys and min(abs(peak - k) for k in keys) <= conf_ticks:
            out.append((int(ps[a]), int(ps[b - 1]), peak))
    return out


def hvf(s, ref, thr, p=None, prof=None):
    p = p or PARAMS["HVF"]
    if not ref or not thr:
        return []
    zones = hvn_zones(prof, ref, p["hvn_pct"], p["conf_ticks"])
    if not zones:
        return []
    i, j = s.idx_sec(NY_OPEN), s.idx_sec(NY_OPEN + 2 * 3600 + 15 * 60)
    buy, sell, hi, lo, first, last = V1._bins(s, i, j)
    nb = len(buy); W = 60 // BIN
    if nb < 2 * W:
        return []
    k = np.ones(W)
    bw = np.convolve(buy, k, "valid"); sw = np.convolve(sell, k, "valid")
    cmax = np.maximum.accumulate(hi); cmin = np.minimum.accumulate(lo)
    used = set(); out = []
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
            hit = None
            for zl, zh, pk in zones:
                if (zl, zh) in used:
                    continue
                if max(zl - ext, ext - zh, 0) > p["near_ticks"]:
                    continue
                hit = (zl, zh, pk); break
            if hit is None:
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
            used.add((hit[0], hit[1]))
            t_conf = NY_OPEN + (conf + 1) * BIN
            entry_est = int(last[conf])
            dist = abs(ext + side * p["stop_beyond"] - entry_est)
            stop = int(min(max(dist, p["stop_min"]), p["stop_max"]))
            out.append(Signal(sec=t_conf, side=-side, stop_ticks=stop, target_ticks=None, max_sec=p["max_min"] * 60,
                              kind="HVF", level=f"hvn_{hit[2] / 4}", meta={"absorbed_vol": float(volw), "extreme": ext / 4, "side_absorbed": side}))
    out.sort(key=lambda x: x.sec)
    return out


REGISTRY = {"HVF": hvf}
