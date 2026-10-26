"""Estrategias v28 (tanda 29), congeladas en futures/strategies/v30.json.
  ABB v1 : ABSORCIÓN TRAS RE-ENTRADA ACEPTADA — el detector de ABU (v17.py) en los días que ABU NO opera: los que abren FUERA del valor de ayer.
           El día se habilita solo después de que el precio vuelve al valor de ayer (VAL–VAH) y se queda adentro `accept_s` seguidos
           (600 s = 10 min, un tercio del período de 30 min de Dalton; elegido por conteo de señales, no por ganancias). Antes de esa aceptación no hay señales; toda la ventana de absorción debe
           empezar después de ella. Mismos niveles (ayer, noche, POC/VAH/VAL del día), confirmación a 60 s, umbral relativo, stop 12–32,
           objetivo 2R, salida a 15 min, 2 contratos y parada tras 2 pérdidas que ABU v3.
           Motivo: ABU solo funciona en días de balance conocidos a las 09:30 y llega a ~170 operaciones; los días que abren fuera del valor
           y luego lo aceptan son balance que ABU no ve. Investigación y justificación: docs/investigacion/absorcion_reentrada.md.
"""
import numpy as np
from ..sim import Signal
from ..data import NY_OPEN
from . import v1 as V1
from .v8 import _developing_profile
from .v17 import PARAMS as P17

PARAMS = {"ABB": dict(P17["ABU"], accept_s=600)}
BIN = V1.BIN
CONTRACTS = 2


def acceptance_time(sec, px, lo, hi, hold_s):
    """Primer instante en que el precio lleva `hold_s` segundos seguidos dentro de [lo, hi] (solo pasado: se conoce en ese instante).
    Devuelve None si nunca ocurre."""
    inside = (px >= lo) & (px <= hi)
    n = len(inside); k = 0
    while k < n:
        if not inside[k]:
            k += 1; continue
        m = k
        while m + 1 < n and inside[m + 1]:
            m += 1
        t0 = sec[k]
        if sec[m] - t0 >= hold_s:
            e = int(np.searchsorted(sec, t0 + hold_s, side="left"))
            return float(sec[min(e, n - 1)])
        if m + 1 >= n:
            return None
        k = m + 1
    return None


def absorption_reentry(s, ref, thr, p=None):
    p = p or PARAMS["ABB"]
    if not ref or not thr or ref.get("prev_vah") is None or ref.get("prev_val") is None:
        return []
    i, j = s.idx_sec(NY_OPEN), s.idx_sec(p["data_end_sec"])
    if j - i < 50:
        return []
    if ref["prev_val"] <= s.px[i] <= ref["prev_vah"]:
        return []                      # abre dentro del valor de ayer: es territorio de ABU
    t_acc = acceptance_time(s.sec[i:j], s.px[i:j], ref["prev_val"], ref["prev_vah"], p["accept_s"])
    if t_acc is None:
        return []
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
        if NY_OPEN + w0 * BIN < t_acc:
            continue                   # la ventana de absorción entera debe empezar después de la aceptación
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
            entry_est = int(last[conf])
            dist = abs(ext + side * p["stop_beyond"] - entry_est)
            stop = int(min(max(dist, p["stop_min"]), p["stop_max"]))
            out.append(Signal(sec=t_conf, side=-side, stop_ticks=stop, target_ticks=int(round(p["rr"] * stop)),
                              max_sec=p["max_min"] * 60, kind="ABB", level=name,
                              meta={"absorbed_vol": float(volw), "extreme": ext / 4, "side_absorbed": side, "t_accept": t_acc}))
    out.sort(key=lambda x: x.sec)
    return out


REGISTRY = {"ABB": absorption_reentry}
