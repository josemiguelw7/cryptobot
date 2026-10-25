"""Estrategias v23 (tanda 24), congeladas en futures/strategies/v25.json.
  ABF v1 : ABSORCIÓN FALLIDA — el mismo detector de absorción de ABU v1 (v17.py: flujo agresivo ≥ umbral relativo sin avanzar, en un nivel de ayer,
           de la noche o del valor en desarrollo, confirmado a 60 s con delta contrario y alejamiento de 4 ticks), pero NO se opera la absorción:
           se espera a que FALLE. Si en 300 s el precio rompe el extremo absorbido por ≥ 4 ticks con delta de 30 s a favor del lado que agredía,
           los pasivos perdieron: se entra a mercado EN LA DIRECCIÓN de la ruptura (a favor del lado absorbido), stop 16 ticks, objetivo 2R, salida a 15 min.
           Todos los días (sin filtro de apertura). Guarda de calidad de datos: no se entra si la cotización (mid antes de la operación) se aleja
           > 20 ticks del último precio (cotización congelada: 2025-04-07, 2026-01-29, etc.).
           Investigación y definición fijada antes de correr: docs/investigacion/absorcion_fallida.md.
"""
import numpy as np
from ..sim import Signal
from ..data import NY_OPEN
from . import v1 as V1
from .v8 import _developing_profile

PARAMS = {
    "ABF": {"near_ticks": 4, "max_advance": 2, "confirm_s": 60, "away_ticks": 4, "rel_pct": 90, "rel_lookback_s": 3600, "floor_frac": 0.5,
            "min_elapsed_s": 0, "dev_min_elapsed_s": 600, "dev_cooldown_s": 600,
            "brk_ticks": 4, "break_s": 300, "delta_s": 30, "stop": 16, "rr": 2.0, "max_min": 15,
            "quote_max_dev": 20, "last_sec": 55800.0, "data_end_sec": 56700.0},
}
BIN = V1.BIN


def absorption_failed(s, ref, thr, p=None):
    p = p or PARAMS["ABF"]
    if not ref or not thr:
        return []
    i, j = s.idx_sec(NY_OPEN), s.idx_sec(p["data_end_sec"])
    if j - i < 50:
        return []
    buy, sell, hi, lo, first, last = V1._bins(s, i, j)
    nb = len(buy); W = 60 // BIN; D = max(1, int(p["delta_s"] // BIN)); B = int(p["break_s"] // BIN)
    if nb < 2 * W:
        return []
    k = np.ones(W)
    bw = np.convolve(buy, k, "valid"); sw = np.convolve(sell, k, "valid")
    cb = np.concatenate([[0.0], np.cumsum(buy)]); cs = np.concatenate([[0.0], np.cumsum(sell)])
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
            # fallo de la absorción: ruptura del extremo con delta a favor del lado absorbido
            for f in range(conf + 1, min(nb, conf + 1 + B)):
                if NY_OPEN + (f + 1) * BIN > p["last_sec"]:
                    break
                broke = hi[f] >= ext + p["brk_ticks"] if side > 0 else lo[f] <= ext - p["brk_ticks"]
                if not broke:
                    continue
                a = max(0, f + 1 - D)
                dl = (cb[f + 1] - cb[a]) - (cs[f + 1] - cs[a])
                if (side > 0 and dl > 0) or (side < 0 and dl < 0):
                    t_ent = NY_OPEN + (f + 1) * BIN
                    q = s.idx_sec(t_ent)
                    if q < s.n and abs((int(s.bidb[q]) + int(s.askb[q])) / 2.0 - int(s.px[q])) > p["quote_max_dev"]:
                        break          # cotización congelada: no se opera
                    out.append(Signal(sec=t_ent, side=side, stop_ticks=int(p["stop"]), target_ticks=int(round(p["rr"] * p["stop"])),
                                      max_sec=p["max_min"] * 60, kind="ABF", level=name,
                                      meta={"absorbed_vol": float(volw), "extreme": ext / 4, "side_absorbed": side}))
                break                  # la ruptura se evalúa una sola vez por absorción
    out.sort(key=lambda x: x.sec)
    return out


REGISTRY = {"ABF": absorption_failed}
