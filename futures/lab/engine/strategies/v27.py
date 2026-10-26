"""Estrategias v27 (tanda 28), congeladas en futures/strategies/v29.json.
  ABM v1 : ABSORCIÓN EN EL VALOR MULTI-DÍA — el detector, la confirmación a 60 s, el umbral relativo, el stop 12–32, el objetivo 2R y la salida a 15 min
           son los de ABU (v17.py). Cambian los NIVELES y el filtro del día: perfil compuesto de los últimos 5 días válidos (POC, VAH, VAL, máximo y
           mínimo) y POC "desnudos" (POC de esos días que el precio no volvió a cruzar). Solo días que abren dentro del valor compuesto.
           Los niveles a ≤ 8 ticks de un nivel de ayer o de la noche se descartan: ABM solo opera donde ABU no mira.
           2 contratos, se detiene tras 2 pérdidas seguidas (el cálculo de riesgo de docs/investigacion/riesgo_diario.md).
           Investigación y justificación: docs/investigacion/absorcion_multidia.md.
"""
import numpy as np
from ..sim import Signal
from ..data import NY_OPEN
from . import v1 as V1
from .v17 import PARAMS as P17

PARAMS = {"ABM": dict(P17["ABU"], comp_days=5, overlap_ticks=8)}
BIN = V1.BIN
CONTRACTS = 2


def _value_area(prices, vols, frac=0.70):
    """Mismo cálculo que features.value_area (POC, VAH, VAL), sobre un perfil sumado."""
    o = np.argsort(prices); px = prices[o]; v = vols[o]
    i = int(np.argmax(v)); lo = hi = i; acc = v[i]; tot = v.sum()
    while acc < frac * tot and (lo > 0 or hi < len(v) - 1):
        up = v[hi + 1] if hi < len(v) - 1 else -1
        dn = v[lo - 1] if lo > 0 else -1
        if up >= dn:
            hi += 1; acc += up
        else:
            lo -= 1; acc += dn
    return int(px[i]), int(px[hi]), int(px[lo])


def composite_levels(days, n):
    """days: lista (vieja→nueva) de dicts {px, vol, poc, hi, lo} de días ANTERIORES. Usa los últimos n."""
    d = days[-n:]
    if len(d) < n:
        return None
    px = np.concatenate([x["px"] for x in d]); vv = np.concatenate([x["vol"] for x in d]).astype(float)
    u, inv = np.unique(px, return_inverse=True)
    tot = np.bincount(inv, weights=vv)
    poc, vah, val = _value_area(u, tot)
    lv = {"comp_poc": poc, "comp_vah": vah, "comp_val": val,
          "comp_high": int(max(x["hi"] for x in d)), "comp_low": int(min(x["lo"] for x in d))}
    for k, x in enumerate(d):                      # POC desnudo: ningún día posterior (hasta ayer) lo cruzó
        if not any(y["lo"] <= x["poc"] <= y["hi"] for y in d[k + 1:]):
            lv[f"npoc_{k}"] = int(x["poc"])
    return lv


def absorption_multiday(s, ref, thr, p=None, days=None):
    p = p or PARAMS["ABM"]
    if not ref or not thr or not days:
        return []
    cl = composite_levels(days, int(p["comp_days"]))
    if cl is None:
        return []
    i, j = s.idx_sec(NY_OPEN), s.idx_sec(p["data_end_sec"])
    if j - i < 50:
        return []
    if not (cl["comp_val"] <= s.px[i] <= cl["comp_vah"]):
        return []                      # abre fuera del valor compuesto: el día queda fuera (dato de las 09:30)
    abu = [v for v in V1._ref_levels(ref).values() if v]
    lv = {k: v for k, v in cl.items() if all(abs(v - a) > p["overlap_ticks"] for a in abu)}
    if not lv:
        return []
    buy, sell, hi, lo, first, last = V1._bins(s, i, j)
    nb = len(buy); W = 60 // BIN
    if nb < 2 * W:
        return []
    k = np.ones(W)
    bw = np.convolve(buy, k, "valid"); sw = np.convolve(sell, k, "valid")
    used = set(); out = []
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
            name = None; best = None
            for nm, lvl in lv.items():
                d = abs(ext - lvl)
                if d <= p["near_ticks"] and nm not in used and (best is None or d < best):
                    best, name = d, nm
            if not name:
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
                              max_sec=p["max_min"] * 60, kind="ABM", level=name.split("_")[0] + "_" + name.split("_")[1] if name.startswith("comp") else "npoc",
                              meta={"absorbed_vol": float(volw), "extreme": ext / 4, "side_absorbed": side}))
    out.sort(key=lambda x: x.sec)
    return out


REGISTRY = {"ABM": absorption_multiday}
