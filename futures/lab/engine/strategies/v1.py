"""Estrategias v1 (BIG, ABS, POC) tal como quedaron congeladas en futures/strategies/v1.json.

Cada función recibe la sesión completa, los niveles de referencia y los umbrales del pasado,
y devuelve señales (sim.Signal). No decide llenados ni costos: eso lo hace el simulador.
Los parámetros numéricos viven en PARAMS para que la superficie de sensibilidad pueda moverlos
sin tocar la lógica (cada cambio cuenta como intento).
"""
import numpy as np
from ..sim import Signal
from ..data import NY_OPEN

PARAMS = {
    "BIG": {"min_levels": 2, "near_ticks": 4, "confirm_s": 30, "stop": 24, "target": 48, "max_min": 15, "cooldown_s": 120},
    "ABS": {"near_ticks": 4, "max_advance": 2, "confirm_s": 60, "away_ticks": 4, "stop_beyond": 4, "stop_min": 12, "stop_max": 32, "rr": 2.0, "max_min": 15},
    "POC": {"touch_ticks": 2, "confirm_s": 120, "back_ticks": 4, "stop_beyond": 4, "stop_min": 12, "max_min": 30},
}
BIN = 10  # segundos por celda


def _bins(s, i, j):
    """Celdas de BIN s en la ventana [i, j): compra, venta, máximo, mínimo, primer y último precio."""
    sec = s.sec[i:j]; px = s.px[i:j]; vol = s.vol[i:j]; sd = s.side[i:j]
    b = ((sec - NY_OPEN) // BIN).astype(int)
    nb = int(b.max()) + 1 if len(b) else 0
    buy = np.bincount(b, weights=np.where(sd > 0, vol, 0), minlength=nb)
    sell = np.bincount(b, weights=np.where(sd < 0, vol, 0), minlength=nb)
    hi = np.full(nb, -1); lo = np.full(nb, 10**9); first = np.full(nb, -1); last = np.full(nb, -1)
    np.maximum.at(hi, b, px); np.minimum.at(lo, b, px)
    first_idx = np.unique(b, return_index=True)[1]
    first[np.unique(b)] = px[first_idx]
    last_idx = len(b) - 1 - np.unique(b[::-1], return_index=True)[1]
    last[np.unique(b)] = px[last_idx]
    # celdas vacías heredan el último precio
    for k in range(nb):
        if first[k] < 0:
            first[k] = last[k] = last[k - 1] if k else px[0]
            hi[k] = lo[k] = first[k]
    return buy, sell, hi, lo, first, last


def _ref_levels(ref):
    return {k: v for k, v in (ref or {}).items() if v is not None}


def _near(px, levels, near, vwap=None):
    best, name = None, None
    for k, v in levels.items():
        d = abs(px - v)
        if d <= near and (best is None or d < best):
            best, name = d, k
    if vwap is not None and abs(px - vwap) <= near and (best is None or abs(px - vwap) < best):
        best, name = abs(px - vwap), "vwap"
    return name


def big(s, ref, thr, p=None):
    p = p or PARAMS["BIG"]
    if not ref or not thr:
        return []
    i, j = s.idx_sec(NY_OPEN), s.idx_sec(NY_OPEN + 2 * 3600 + 15 * 60)
    tid = s.tid[i:j]; px = s.px[i:j]; vol = s.vol[i:j]; sd = s.side[i:j]; sec = s.sec[i:j]
    if len(tid) == 0:
        return []
    starts = np.r_[0, np.flatnonzero(np.diff(tid)) + 1]
    size = np.add.reduceat(vol, starts)
    hi = np.maximum.reduceat(px, starts); lo = np.minimum.reduceat(px, starts)
    levels = hi - lo + 1
    pv = np.cumsum(px.astype(float) * vol); cv = np.cumsum(vol)
    ends = np.r_[starts[1:], len(tid)] - 1
    cand = np.flatnonzero((size >= thr["order_p99"]) & (levels >= p["min_levels"]))
    lv = _ref_levels(ref); out = []; last_sig = -1e9
    for c in cand:
        a, e = starts[c], ends[c]
        t0, first_px, side = sec[e], int(px[a]), int(sd[a])
        if side == 0 or t0 - last_sig < p["cooldown_s"]:
            continue
        vwap = pv[e] / cv[e] if cv[e] else None
        name = _near(first_px, lv, p["near_ticks"], vwap)
        if not name:
            continue
        k0, k1 = e + 1, int(np.searchsorted(sec, t0 + p["confirm_s"], side="right"))
        if k1 <= k0:
            continue
        seg = px[k0:k1]
        ok = seg.min() >= first_px if side > 0 else seg.max() <= first_px
        if not ok:
            continue
        last_sig = t0
        out.append(Signal(sec=t0 + p["confirm_s"] + 1e-6, side=side, stop_ticks=p["stop"], target_ticks=p["target"],
                          max_sec=p["max_min"] * 60, kind="BIG", level=name,
                          meta={"order_size": int(size[c]), "levels": int(levels[c]), "order_px": first_px / 4, "p99": thr["order_p99"]}))
    return out


def absorption(s, ref, thr, p=None):
    p = p or PARAMS["ABS"]
    if not ref or not thr:
        return []
    i, j = s.idx_sec(NY_OPEN), s.idx_sec(NY_OPEN + 2 * 3600 + 15 * 60)
    buy, sell, hi, lo, first, last = _bins(s, i, j)
    nb = len(buy); W = 60 // BIN
    if nb < 2 * W:
        return []
    k = np.ones(W)
    bw = np.convolve(buy, k, "valid"); sw = np.convolve(sell, k, "valid")  # ventana que termina en e = idx+W-1
    lv = _ref_levels(ref); used = set(); out = []
    for e in range(W - 1, nb - W):
        w0 = e - W + 1
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
            name = _near(ext, lv, p["near_ticks"])
            if not name or name in used:
                continue
            # confirmación en los 60 s siguientes
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
                              max_sec=p["max_min"] * 60, kind="ABS", level=name,
                              meta={"absorbed_vol": float(volw), "extreme": ext / 4, "side_absorbed": side}))
    return out


def poc(s, ref, thr, p=None, open_in_value=None):
    p = p or PARAMS["POC"]
    if not ref or not open_in_value:
        return []
    i, j = s.idx_sec(NY_OPEN), s.idx_sec(NY_OPEN + 2 * 3600 + 15 * 60)
    buy, sell, hi, lo, first, last = _bins(s, i, j)
    nb = len(buy); W = 60 // BIN
    if nb < 2 * W:
        return []
    k = np.ones(W)
    bw = np.convolve(buy, k, "valid"); sw = np.convolve(sell, k, "valid")
    target_px = ref["prev_poc"]; out = []; used = set()
    for edge, lvl, side_in in (("prev_vah", ref["prev_vah"], -1), ("prev_val", ref["prev_val"], 1)):
        if edge in used:
            continue
        touch = None
        for b in range(nb):
            if side_in < 0 and hi[b] >= lvl - p["touch_ticks"]:
                touch = b; break
            if side_in > 0 and lo[b] <= lvl + p["touch_ticks"]:
                touch = b; break
        if touch is None:
            continue
        ext = int(hi[touch]) if side_in < 0 else int(lo[touch])
        conf = None
        for f in range(touch, min(nb, touch + p["confirm_s"] // BIN)):
            ext = max(ext, int(hi[f])) if side_in < 0 else min(ext, int(lo[f]))
            dw = (bw[f - W + 1] - sw[f - W + 1]) if f - W + 1 >= 0 else 0
            if side_in < 0 and dw < 0 and lo[f] <= ext - p["back_ticks"]:
                conf = f; break
            if side_in > 0 and dw > 0 and hi[f] >= ext + p["back_ticks"]:
                conf = f; break
        used.add(edge)
        if conf is None:
            continue
        entry_est = int(last[conf])
        stop = max(abs(ext - side_in * p["stop_beyond"] - entry_est), p["stop_min"])
        tgt = abs(target_px - entry_est)
        if tgt < stop:
            continue
        out.append(Signal(sec=NY_OPEN + (conf + 1) * BIN, side=side_in, stop_ticks=int(stop), target_ticks=int(tgt),
                          max_sec=p["max_min"] * 60, kind="POC", level=edge,
                          meta={"edge_px": lvl / 4, "extreme": ext / 4, "poc_px": target_px / 4}))
    return out


REGISTRY = {"BIG": big, "ABS": absorption, "POC": poc}
