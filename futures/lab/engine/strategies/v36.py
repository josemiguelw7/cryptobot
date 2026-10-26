"""Estrategias v36 (tanda 37), congeladas en futures/strategies/v38.json.
  ATR v1 : TRADERS ATRAPADOS (G6, pedido de Jose 26/10/2026). Misma ráfaga, niveles y filtro de día que ABU v2 (v17.py), pero la entrada se
           decide desde el lado del perdedor: fracción del volumen agresivo de la ráfaga (a nivel de operación) ejecutado a un precio peor
           que el actual >= trap_frac, con delta de los últimos delta_s contrario a los atrapados, dentro de wait_s tras la ráfaga y sin que el
           precio supere el extremo en más de ext_ticks. Entrada a mercado contra los atrapados; stop 12–32; objetivo 2R; salida a 15 min.
           Investigación y definición fijada antes de correr: docs/investigacion/atrapados.md.
"""
import numpy as np
from ..sim import Signal
from ..data import NY_OPEN
from . import v1 as V1
from .v8 import _developing_profile
from .v17 import PARAMS as P17

PARAMS = {"ATR": dict(P17["ABU"], trap_frac=0.70, wait_s=180, delta_s=30, ext_ticks=4)}
BIN = V1.BIN
CONTRACTS = 2


def trapped(s, ref, thr, p=None):
    p = p or PARAMS["ATR"]
    if not ref or not thr or ref.get("prev_vah") is None or ref.get("prev_val") is None:
        return []
    i, j = s.idx_sec(NY_OPEN), s.idx_sec(p["data_end_sec"])
    if j - i < 50:
        return []
    if not (ref["prev_val"] <= s.px[i] <= ref["prev_vah"]):
        return []
    buy, sell, hi, lo, first, last = V1._bins(s, i, j)
    nb = len(buy); W = 60 // BIN; D = max(1, int(p["delta_s"] // BIN)); Wt = int(p["wait_s"] // BIN)
    if nb < 2 * W:
        return []
    k = np.ones(W)
    bw = np.convolve(buy, k, "valid"); sw = np.convolve(sell, k, "valid")
    cb = np.concatenate([[0.0], np.cumsum(buy)]); cs = np.concatenate([[0.0], np.cumsum(sell)])
    px = s.px[i:j].astype(float); vol = s.vol[i:j].astype(float); sec = s.sec[i:j]; sd = s.side[i:j]
    b = ((sec - NY_OPEN) // BIN).astype(int)
    d_poc, d_vah, d_val = _developing_profile(px, vol, b, nb)
    lv = V1._ref_levels(ref); used = set(); last_dev = {}; out = []
    for e in range(W - 1, nb - W):
        w0 = e - W + 1
        if NY_OPEN + (e + 1) * BIN > p["last_sec"]:
            break
        for side, volw, thr_key in ((1, bw[w0], "buy60_p95"), (-1, sw[w0], "sell60_p95")):
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
                    continue
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
            # operaciones agresivas de la ráfaga, a nivel de operación (solo pasado)
            t0 = int(np.searchsorted(b, w0, "left")); t1 = int(np.searchsorted(b, e + 1, "left"))
            m = sd[i + t0:i + t1] == side
            pw = px[t0:t1][m]; vw = vol[t0:t1][m]
            tot = float(vw.sum())
            if tot <= 0:
                continue
            conf = None
            for f in range(e + 1, min(nb, e + 1 + Wt)):
                if (hi[f] > ext + p["ext_ticks"]) if side > 0 else (lo[f] < ext - p["ext_ticks"]):
                    break                              # los agresores ganaron: no están atrapados
                P = int(last[f])
                under = float(vw[pw > P].sum() if side > 0 else vw[pw < P].sum()) / tot
                g0 = max(0, f - D + 1)
                dl = (cb[f + 1] - cb[g0]) - (cs[f + 1] - cs[g0])
                if under >= p["trap_frac"] and dl * side < 0:
                    conf = f; break
            if conf is None:
                continue
            t_conf = NY_OPEN + (conf + 1) * BIN
            if dev:
                last_dev[name] = t_conf
            else:
                used.add(name)
            entry_est = int(last[conf])
            stop = int(min(max(abs(ext + side * p["stop_beyond"] - entry_est), p["stop_min"]), p["stop_max"]))
            out.append(Signal(sec=t_conf, side=-side, stop_ticks=stop, target_ticks=int(round(p["rr"] * stop)),
                              max_sec=p["max_min"] * 60, kind="ATR", level=name,
                              meta={"burst_vol": float(volw), "extreme": ext / 4, "side_trapped": side}))
    out.sort(key=lambda x: x.sec)
    return out


REGISTRY = {"ATR": trapped}
