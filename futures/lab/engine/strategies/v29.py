"""Estrategias v29 (tanda 30), congeladas en futures/strategies/v31.json.
  VPT v1 : PULLBACK A LA VWAP A FAVOR DE LA TENDENCIA, SOLO EN DÍAS QUE ABREN FUERA DEL VALOR DE AYER Y NO LO REGRESAN.
           Complemento de ABU (balance): el día abre sobre el VAH (bajo el VAL) de ayer; mientras el precio no vuelva al valor de ayer, el día
           se trata como de tendencia. Se requiere una extensión previa >= ext_min ticks lejos de la VWAP (VWAP acumulada desde las 09:30, solo pasado).
           Pullback: en una ventana de 60 s el precio toca la VWAP (a <= touch_ticks). Confirmación en los 60 s siguientes: el delta agresivo de la
           ventana va a favor de la tendencia (>= delta_pct del volumen) y el precio se aleja away_ticks del extremo del pullback.
           Entrada a mercado a favor; stop 4 ticks más allá del extremo del pullback (12–32), objetivo 2R, salida a 15 min, 2 contratos.
           Investigación: docs/investigacion/vwap_tendencia.md.
"""
import numpy as np
from ..sim import Signal
from ..data import NY_OPEN
from . import v1 as V1

PARAMS = {
    "VPT": {"touch_ticks": 4, "ext_min": 24, "delta_pct": 5, "confirm_s": 60, "away_ticks": 4, "stop_beyond": 4, "stop_min": 12,
            "stop_max": 32, "rr": 2.0, "max_min": 15, "cooldown_s": 600, "first_sec": 36000.0, "last_sec": 55800.0, "data_end_sec": 56700.0},
}
BIN = V1.BIN
CONTRACTS = 2


def vwap_pullback_trend(s, ref, thr, p=None):
    p = p or PARAMS["VPT"]
    if not ref or ref.get("prev_vah") is None or ref.get("prev_val") is None:
        return []
    i, j = s.idx_sec(NY_OPEN), s.idx_sec(p["data_end_sec"])
    if j - i < 50:
        return []
    o = s.px[i]
    if ref["prev_val"] <= o <= ref["prev_vah"]:
        return []                      # abre dentro del valor: territorio de ABU
    trend = 1 if o > ref["prev_vah"] else -1
    edge = ref["prev_vah"] if trend > 0 else ref["prev_val"]
    buy, sell, hi, lo, first, last = V1._bins(s, i, j)
    nb = len(buy); W = 60 // BIN
    if nb < 2 * W:
        return []
    sec = s.sec[i:j]; px = s.px[i:j].astype(float); vol = s.vol[i:j].astype(float)
    b = ((sec - NY_OPEN) // BIN).astype(int)
    cv = np.cumsum(np.bincount(b, weights=vol, minlength=nb))
    cpv = np.cumsum(np.bincount(b, weights=vol * px, minlength=nb))
    k = np.ones(W)
    bw = np.convolve(buy, k, "valid"); sw = np.convolve(sell, k, "valid")
    run_hi = np.maximum.accumulate(hi); run_lo = np.minimum.accumulate(lo)
    out = []; last_sig = -1e9
    for e in range(W - 1, nb - 1):
        t_e = NY_OPEN + (e + 1) * BIN
        if t_e < p["first_sec"]:
            continue
        if t_e > p["last_sec"]:
            break
        if cv[e] <= 0 or t_e - last_sig < p["cooldown_s"]:
            continue
        # el día sigue siendo de tendencia solo si el precio nunca regresó al valor de ayer
        if (trend > 0 and run_lo[e] < edge) or (trend < 0 and run_hi[e] > edge):
            break
        w0 = e - W + 1
        vwap = cpv[e] / cv[e]
        vw0 = cpv[w0] / cv[w0] if cv[w0] > 0 else vwap
        if trend > 0:
            ext_ok = run_hi[w0] - vw0 >= p["ext_min"]
            pull = int(lo[w0:e + 1].min())
            if not ext_ok or pull > vwap + p["touch_ticks"]:
                continue
        else:
            ext_ok = vw0 - run_lo[w0] >= p["ext_min"]
            pull = int(hi[w0:e + 1].max())
            if not ext_ok or pull < vwap - p["touch_ticks"]:
                continue
        conf = None
        for f in range(e + 1, min(nb, e + 1 + p["confirm_s"] // BIN)):
            tot = bw[f - W + 1] + sw[f - W + 1]
            if tot <= 0:
                continue
            dw = (bw[f - W + 1] - sw[f - W + 1]) / tot * trend
            if dw >= p["delta_pct"] / 100.0 and ((trend > 0 and hi[f] >= pull + p["away_ticks"]) or (trend < 0 and lo[f] <= pull - p["away_ticks"])):
                conf = f; break
        if conf is None:
            continue
        t_conf = NY_OPEN + (conf + 1) * BIN
        if t_conf > p["last_sec"]:
            continue
        entry_est = int(last[conf])
        stop = int(min(max(abs(pull - trend * p["stop_beyond"] - entry_est), p["stop_min"]), p["stop_max"]))
        last_sig = t_conf
        out.append(Signal(sec=t_conf, side=trend, stop_ticks=stop, target_ticks=int(round(p["rr"] * stop)), max_sec=p["max_min"] * 60,
                          kind="VPT", level="vwap", meta={"vwap": float(vwap) / 4, "pullback": pull / 4, "trend": trend}))
    out.sort(key=lambda x: x.sec)
    return out


REGISTRY = {"VPT": vwap_pullback_trend}
