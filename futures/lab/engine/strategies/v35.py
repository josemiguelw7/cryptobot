"""Estrategias v35 (tanda 36), congeladas en futures/strategies/v37.json.
  CLX v1 : CLÍMAX DE VOLUMEN Y DELTA EN EL EXTREMO DEL DÍA (G5, pedido de Jose 26/10/2026). Subasta terminada (Wyckoff, Dalton): el precio
           marca un nuevo máximo (mínimo) de la sesión en una ventana de 60 s con volumen >= vol_mult veces el volumen medio por 60 s de los
           30 minutos previos, delta agresivo >= delta_min del volumen a favor del empuje y un avance >= rise_ticks. Es el clímax. Se confirma
           como "terminado" si en los 60 s siguientes el precio no supera el extremo del clímax, cae away_ticks bajo él y el delta de los
           últimos 30 s es contrario. Entrada a mercado en contra; stop stop_beyond ticks más allá del extremo (12–32); objetivo rr x stop;
           salida a max_min minutos. Distinta de DVG (divergencia de delta acumulado, sin volumen) y de FAF/ABF (niveles de ayer).
           Investigación y definición fijada antes de correr: docs/investigacion/climax.md.
"""
import numpy as np
from ..sim import Signal
from ..data import NY_OPEN
from . import v1 as V1

PARAMS = {
    "CLX": {"win_s": 60, "hist_s": 1800, "vol_mult": 3.0, "delta_min": 0.20, "rise_ticks": 12, "confirm_s": 60, "away_ticks": 4,
            "flip_s": 30, "stop_beyond": 3, "stop_min": 12, "stop_max": 32, "rr": 1.5, "max_min": 10, "min_gap_s": 300,
            "min_elapsed_s": 1800, "last_sec": 55800.0, "data_end_sec": 56700.0},
}
BIN = V1.BIN
CONTRACTS = 1


def climax(s, ref, thr, p=None):
    p = p or PARAMS["CLX"]
    i, j = s.idx_sec(NY_OPEN), s.idx_sec(p["data_end_sec"])
    if j - i < 50:
        return []
    buy, sell, hi, lo, first, last = V1._bins(s, i, j)
    nb = len(buy); W = int(p["win_s"] // BIN); Hn = int(p["hist_s"] // BIN); C = int(p["confirm_s"] // BIN); F = int(p["flip_s"] // BIN)
    tot = buy + sell
    cv = np.cumsum(np.r_[0.0, tot]); cb = np.cumsum(np.r_[0.0, buy]); cs = np.cumsum(np.r_[0.0, sell])
    pmax = np.maximum.accumulate(hi); pmin = np.minimum.accumulate(lo)
    out = []; last_sig = {1: -10**9, -1: -10**9}
    for e in range(max(W, Hn), nb):
        if NY_OPEN + (e + 1) * BIN > p["last_sec"]:
            break
        if e * BIN < p["min_elapsed_s"]:
            continue
        w0 = e - W + 1
        vol = cv[e + 1] - cv[w0]
        # volumen medio por ventana de 60 s en los 30 minutos previos a la ventana (solo pasado)
        base = (cv[w0] - cv[w0 - Hn]) / Hn * W
        if base <= 0 or vol < p["vol_mult"] * base:
            continue
        dl = ((cb[e + 1] - cb[w0]) - (cs[e + 1] - cs[w0])) / vol
        for side in (1, -1):
            if dl * side < p["delta_min"] or e - last_sig[side] < int(p["min_gap_s"] // BIN):
                continue
            if side > 0:
                ext = int(hi[w0:e + 1].max())
                if ext <= pmax[w0 - 1] or ext - int(lo[w0:e + 1].min()) < p["rise_ticks"]:
                    continue
            else:
                ext = int(lo[w0:e + 1].min())
                if ext >= pmin[w0 - 1] or int(hi[w0:e + 1].max()) - ext < p["rise_ticks"]:
                    continue
            conf = None
            for f in range(e + 1, min(nb, e + 1 + C)):
                if (hi[f] > ext) if side > 0 else (lo[f] < ext):
                    break                          # hizo otro extremo: no estaba terminada
                if ((ext - lo[f]) if side > 0 else (hi[f] - ext)) >= p["away_ticks"]:
                    g0 = max(e + 1, f - F + 1)
                    d30 = ((cb[f + 1] - cb[g0]) - (cs[f + 1] - cs[g0]))
                    if d30 * side < 0:
                        conf = f
                    break
            if conf is None:
                continue
            last_sig[side] = conf
            entry_est = int(last[conf])
            stop = int(min(max(abs(ext + side * p["stop_beyond"] - entry_est), p["stop_min"]), p["stop_max"]))
            out.append(Signal(sec=NY_OPEN + (conf + 1) * BIN, side=-side, stop_ticks=stop, target_ticks=int(round(p["rr"] * stop)),
                              max_sec=p["max_min"] * 60, kind="CLX", level="extremo_dia",
                              meta={"extreme": ext / 4, "side_exhausted": side, "vol_ratio": float(vol / base), "delta_share": float(dl)}))
    out.sort(key=lambda x: x.sec)
    return out


REGISTRY = {"CLX": climax}
