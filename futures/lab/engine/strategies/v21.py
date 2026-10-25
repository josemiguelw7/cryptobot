"""Estrategias v21 (tanda 22), congeladas en futures/strategies/v23.json.
  DVG v1 : DIVERGENCIA DE DELTA EN EL EXTREMO DEL DÍA — el precio marca un nuevo máximo (mínimo) de la sesión, pero el delta acumulado de la
           sesión en ese punto es menor (mayor) que en el máximo (mínimo) anterior, después de un retroceso de al menos 10 ticks y 2 minutos.
           Es agotamiento: el empuje nuevo llegó con menos flujo agresivo que el anterior. Confirmación: en los 30 s siguientes el precio vuelve
           3 ticks bajo (sobre) el extremo sin hacer otro extremo. Entrada a mercado en contra del extremo; stop 3 ticks más allá (entre 8 y 24);
           objetivo 2R; salida a 5 min. No depende de ningún nivel de ayer ni de que el día abra dentro del valor: usa solo el extremo del propio día.
           Investigación y definición fijada antes de correr: docs/investigacion/divergencia_delta.md.
"""
import numpy as np
from ..sim import Signal
from ..data import NY_OPEN
from . import v1 as V1

PARAMS = {
    "DVG": {"pullback_ticks": 10, "away_ticks": 3, "rr": 2.0, "min_gap_s": 120, "confirm_s": 30, "stop_beyond": 3, "stop_min": 8,
            "stop_max": 24, "max_min": 5, "min_elapsed_s": 600, "last_sec": 55800.0, "data_end_sec": 56700.0},
}
BIN = V1.BIN


def delta_divergence(s, ref, thr, p=None):
    p = p or PARAMS["DVG"]
    i, j = s.idx_sec(NY_OPEN), s.idx_sec(p["data_end_sec"])
    if j - i < 50:
        return []
    buy, sell, hi, lo, first, last = V1._bins(s, i, j)
    nb = len(buy)
    cd = np.cumsum(buy - sell)
    gap_bins = int(p["min_gap_s"] // BIN); conf_bins = int(p["confirm_s"] // BIN)
    out = []
    # estado de cada lado: extremo de la sesión, celda donde se marcó, delta acumulado ahí y el retroceso desde entonces
    H = int(hi[0]); Hb = 0; Hcd = cd[0]; back_h = int(lo[0])
    L = int(lo[0]); Lb = 0; Lcd = cd[0]; back_l = int(hi[0])
    for e in range(1, nb):
        if NY_OPEN + (e + 1) * BIN > p["last_sec"]:
            break
        t_e = e * BIN
        for side in (1, -1):
            if side > 0:
                if hi[e] > H:
                    prev_cd = Hcd
                    ok = (t_e >= p["min_elapsed_s"] and e - Hb >= gap_bins and H - back_h >= p["pullback_ticks"] and cd[e] < Hcd)
                    ext = int(hi[e]); H, Hb, Hcd, back_h = ext, e, cd[e], int(lo[e])
                else:
                    back_h = min(back_h, int(lo[e])); ok = False; ext = None
            else:
                if lo[e] < L:
                    prev_cd = Lcd
                    ok = (t_e >= p["min_elapsed_s"] and e - Lb >= gap_bins and back_l - L >= p["pullback_ticks"] and cd[e] > Lcd)
                    ext = int(lo[e]); L, Lb, Lcd, back_l = ext, e, cd[e], int(hi[e])
                else:
                    back_l = max(back_l, int(hi[e])); ok = False; ext = None
            if not ok:
                continue
            conf = None
            for f in range(e + 1, min(nb, e + 1 + conf_bins)):
                if side > 0:
                    if hi[f] > ext:
                        break                        # hizo otro máximo: la divergencia se reevalúa en ese extremo
                    if lo[f] <= ext - p["away_ticks"]:
                        conf = f; break
                else:
                    if lo[f] < ext:
                        break
                    if hi[f] >= ext + p["away_ticks"]:
                        conf = f; break
            if conf is None:
                continue
            entry_est = int(last[conf])
            dist = abs(ext + side * p["stop_beyond"] - entry_est)
            stop = int(min(max(dist, p["stop_min"]), p["stop_max"]))
            out.append(Signal(sec=NY_OPEN + (conf + 1) * BIN, side=-side, stop_ticks=stop, target_ticks=int(round(p["rr"] * stop)),
                              max_sec=p["max_min"] * 60, kind="DVG", level="extremo_dia",
                              meta={"extreme": ext / 4, "side_exhausted": side, "cd_now": float(cd[e]), "cd_prev": float(prev_cd)}))
    out.sort(key=lambda x: x.sec)
    return out


REGISTRY = {"DVG": delta_divergence}
