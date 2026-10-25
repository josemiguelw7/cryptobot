"""Estrategias v5 (tanda 6), congeladas en futures/strategies/v7.json.
  SMT v1 : DIVERGENCIA NQ vs ES (SMT) en el máximo/mínimo de la sesión → el barrido fallido se revierte.
           Datos de ES: /srv/lab/data/canonical/ES (solo como dato auxiliar; se opera NQ).
           Investigación y definición: docs/investigacion/smt.md.
"""
import os
import numpy as np
import polars as pl
from .. import config
from ..sim import Signal
from ..data import NY_OPEN

PARAMS = {
    "SMT": {"lookback_s": 120, "fail_s": 120, "stop_beyond": 4, "max_min": 15, "start_s": 900, "cooldown_s": 300, "stop_min": 12, "stop_max": 32},
}
HORIZON = 2 * 3600          # 09:30 → 11:30
_NEG = -10 ** 9


def _es_ny(date):
    """ES de la sesión, solo 09:30–11:45 ET, contrato dominante. (sec desde 09:30, px en ticks)."""
    p = os.path.join(config.DATA, "canonical", "ES", f"{date}.parquet")
    if not os.path.exists(p):
        return None
    df = pl.read_parquet(p, columns=["ts", "price_t", "volume", "contract"])
    et = df["ts"].dt.convert_time_zone(config.TZ)
    mins = et.dt.hour().cast(pl.Int32) * 60 + et.dt.minute().cast(pl.Int32)
    df = df.with_columns(mins.alias("m")).filter((pl.col("m") >= 570) & (pl.col("m") < 705))
    if not df.height:
        return None
    top = df.group_by("contract").agg(pl.col("volume").sum().alias("v")).sort("v", descending=True)["contract"][0]
    df = df.filter(pl.col("contract") == top)
    et = df["ts"].dt.convert_time_zone(config.TZ)
    sec = (et.dt.hour().cast(pl.Float64) * 3600 + et.dt.minute().cast(pl.Float64) * 60 + et.dt.second().cast(pl.Float64)
           + et.dt.nanosecond().cast(pl.Float64) / 1e9).to_numpy()
    return sec - NY_OPEN, df["price_t"].to_numpy()


def _bins(sec, px, sign, n):
    """Máximo (sign=+1) o mínimo en espejo (sign=-1) por segundo; bins vacíos = muy bajo."""
    out = np.full(n, _NEG, dtype=np.int64)
    b = np.floor(sec).astype(np.int64)
    ok = (b >= 0) & (b < n)
    np.maximum.at(out, b[ok], sign * px[ok].astype(np.int64))
    return out


def smt_divergence(s, ref, thr, p=None):
    """SMT: NQ hace un nuevo máximo (mínimo) de la sesión desde las 09:30 y ES, en la misma ventana de `lookback_s` segundos,
    NO supera su propio máximo (mínimo) previo. Divergencia que persiste. Luego el barrido falla: NQ vuelve a operar en o dentro
    del máximo (mínimo) previo en menos de `fail_s` segundos y el delta agresivo de NQ desde el barrido hasta el regreso es contrario
    al barrido (delta ≤ 0 tras un máximo; ≥ 0 tras un mínimo). Entra a mercado EN CONTRA del barrido al regreso; stop `stop_beyond`
    ticks más allá del extremo del barrido (12–32 ticks); sin objetivo; sale por tiempo (`max_min`). Solo después de `start_s`
    (09:45) para que haya un máximo/mínimo con historia. Tras una señal espera `cooldown_s` en ese lado."""
    p = p or PARAMS["SMT"]
    es = _es_ny(s.date)
    if es is None:
        return []
    es_sec, es_px = es
    i, j = s.idx_sec(NY_OPEN), s.idx_sec(NY_OPEN + HORIZON + p["fail_s"] + 5)
    sec = s.sec[i:j] - NY_OPEN; px = s.px[i:j].astype(np.int64); vol = s.vol[i:j].astype(np.float64); sd = s.side[i:j]
    n = HORIZON + p["fail_s"] + 5
    if len(px) < 50 or len(es_px) < 50:
        return []
    L = p["lookback_s"]; out = []
    for side in (1, -1):                                    # +1: barrido de máximo (→ venta); -1: barrido de mínimo (→ compra)
        nq_b = _bins(sec, px, side, n)
        nq_cum = np.maximum.accumulate(nq_b)
        es_s = side * es_px.astype(np.int64); es_cm = np.maximum.accumulate(es_s)
        last_sig = -1e9
        for b in range(max(int(p["start_s"]), L + 1), HORIZON):
            if nq_b[b] <= nq_cum[b - 1] or b - last_sig < p["cooldown_s"]:
                continue                                     # no es un nuevo extremo de la sesión de NQ
            prior = nq_cum[b - 1]                            # extremo previo de NQ (en unidades con signo)
            t0 = int(np.searchsorted(sec, b, side="left"))
            t1 = int(np.searchsorted(sec, b + 1, side="left"))
            k = t0 + int(np.flatnonzero(side * px[t0:t1] > prior)[0])      # llenado exacto del barrido
            t_sw = float(sec[k])
            e0 = int(np.searchsorted(es_sec, t_sw - L, side="left"))        # ES: lo anterior a la ventana
            es_prior = es_cm[e0 - 1] if e0 > 0 else _NEG
            def es_confirmed(t_end):
                e1 = int(np.searchsorted(es_sec, t_end, side="right"))      # solo llenados de ES hasta t_end
                return e1 > e0 and es_s[e0:e1].max() > es_prior
            if es_confirmed(t_sw):
                continue                                     # ES sí confirmó: no hay divergencia
            m = int(np.searchsorted(sec, t_sw + p["fail_s"], side="right"))
            back = np.flatnonzero(side * px[k + 1:m] <= prior)
            if not len(back):
                continue
            r = k + 1 + int(back[0]); t_ret = float(sec[r])
            if t_ret > HORIZON or es_confirmed(t_ret):
                continue                                     # ES confirmó antes del regreso
            ext = int((side * px[k:r + 1]).max())            # extremo del barrido (con signo)
            dl = float((vol[k:r + 1] * sd[k:r + 1]).sum())
            if side * dl > 0:
                continue                                     # el flujo agresivo sigue a favor del barrido: no hay fallo
            entry_est = int(px[r])
            dist = abs(entry_est - side * (ext + p["stop_beyond"]))
            stop = int(min(max(dist, p["stop_min"]), p["stop_max"]))
            out.append(Signal(sec=NY_OPEN + t_ret + 1e-6, side=-side, stop_ticks=stop, target_ticks=None, max_sec=p["max_min"] * 60,
                              kind="SMT", level="session_high" if side > 0 else "session_low",
                              meta={"sweep_ticks": int(ext - prior), "delta": round(dl, 1), "t_back_s": round(t_ret - t_sw, 1)}))
            last_sig = t_ret
    out.sort(key=lambda x: x.sec)
    return out


REGISTRY = {"SMT": smt_divergence}
