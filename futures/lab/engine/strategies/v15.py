"""Estrategias v15 (tanda 16), congeladas en futures/strategies/v17.json.
  VBR v1 : REVERSIÓN A LA VWAP DESDE LA BANDA DE 2σ, SOLO EN DÍAS QUE ABREN DENTRO DEL VALOR DE AYER.
           VWAP y σ (desviación estándar ponderada por volumen) acumuladas desde las 09:30, solo con datos ya ocurridos.
           Extensión: el precio toca VWAP ± k·σ (k = 2; σ con piso de 10 ticks). Agotamiento: en los 60 s siguientes al toque el delta
           agresivo de la ventana cambia de signo y el precio se aleja 4 ticks del extremo. Entrada a mercado hacia la VWAP.
           Stop 4 ticks más allá del extremo (12–32), objetivo = distancia a la VWAP al entrar (16–80 ticks), salida por tiempo a 20 min.
           Entradas 10:00–15:30 ET. Investigación: docs/investigacion/vwap_bandas.md.
"""
import numpy as np
from ..sim import Signal
from ..data import NY_OPEN
from . import v1 as V1

PARAMS = {
    "VBR": {"k_sigma": 2.0, "sigma_floor": 10, "confirm_s": 60, "away_ticks": 4, "stop_beyond": 4, "stop_min": 12, "stop_max": 32,
            "target_min": 16, "target_max": 80, "max_min": 20, "first_sec": 36000.0, "last_sec": 55800.0, "data_end_sec": 56700.0,
            "cooldown_s": 300},
}
BIN = V1.BIN


def vwap_band_reversion(s, ref, thr, p=None):
    p = p or PARAMS["VBR"]
    if not ref or not thr or ref.get("prev_vah") is None or ref.get("prev_val") is None:
        return []
    i, j = s.idx_sec(NY_OPEN), s.idx_sec(p["data_end_sec"])
    if j - i < 50:
        return []
    if not (ref["prev_val"] <= s.px[i] <= ref["prev_vah"]):
        return []                      # abre fuera del valor de ayer: el día no entra (dato de las 09:30)
    buy, sell, hi, lo, first, last = V1._bins(s, i, j)
    nb = len(buy); W = 60 // BIN
    if nb < 2 * W:
        return []
    sec = s.sec[i:j]; px = s.px[i:j].astype(float); vol = s.vol[i:j].astype(float)
    b = ((sec - NY_OPEN) // BIN).astype(int)
    sv = np.bincount(b, weights=vol, minlength=nb)
    spv = np.bincount(b, weights=vol * px, minlength=nb)
    spv2 = np.bincount(b, weights=vol * px * px, minlength=nb)
    cv, cpv, cpv2 = np.cumsum(sv), np.cumsum(spv), np.cumsum(spv2)       # acumulado hasta el final de cada celda
    k = np.ones(W)
    bw = np.convolve(buy, k, "valid"); sw = np.convolve(sell, k, "valid")
    out = []; last_sig = {1: -1e9, -1: -1e9}
    for e in range(W - 1, nb - 1):
        t_e = NY_OPEN + (e + 1) * BIN
        if t_e < p["first_sec"]:
            continue
        if t_e > p["last_sec"]:
            break
        if cv[e] <= 0:
            continue
        vwap = cpv[e] / cv[e]
        sig = max(np.sqrt(max(cpv2[e] / cv[e] - vwap * vwap, 0.0)), p["sigma_floor"])
        band = p["k_sigma"] * sig
        w0 = e - W + 1
        for side in (1, -1):                  # side = +1: extremo superior (se vende hacia la VWAP)
            if t_e - last_sig[side] < p["cooldown_s"]:
                continue
            if side > 0:
                ext = int(hi[w0:e + 1].max())
                if ext < vwap + band:
                    continue
            else:
                ext = int(lo[w0:e + 1].min())
                if ext > vwap - band:
                    continue
            # confirmación: en los 60 s siguientes el delta cambia de signo y el precio se aleja away_ticks del extremo
            conf = None
            for f in range(e + 1, min(nb, e + 1 + p["confirm_s"] // BIN)):
                dw = bw[f - W + 1] - sw[f - W + 1]
                if side > 0 and dw < 0 and lo[f] <= ext - p["away_ticks"]:
                    conf = f; break
                if side < 0 and dw > 0 and hi[f] >= ext + p["away_ticks"]:
                    conf = f; break
            if conf is None:
                continue
            t_conf = NY_OPEN + (conf + 1) * BIN
            if t_conf > p["last_sec"]:
                continue
            entry_est = int(last[conf])
            vw_c = cpv[conf] / cv[conf]
            dist_vwap = (entry_est - vw_c) if side > 0 else (vw_c - entry_est)
            if dist_vwap <= 0:
                continue                   # ya volvió a la VWAP
            stop = int(min(max(abs(ext + side * p["stop_beyond"] - entry_est), p["stop_min"]), p["stop_max"]))
            target = int(min(max(round(dist_vwap), p["target_min"]), p["target_max"]))
            last_sig[side] = t_conf
            out.append(Signal(sec=t_conf, side=-side, stop_ticks=stop, target_ticks=target, max_sec=p["max_min"] * 60,
                              kind="VBR", level="vwap_band",
                              meta={"vwap": float(vw_c) / 4, "sigma": float(sig), "extreme": ext / 4}))
    out.sort(key=lambda x: x.sec)
    return out


REGISTRY = {"VBR": vwap_band_reversion}
