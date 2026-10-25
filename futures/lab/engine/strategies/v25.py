"""Estrategias v25 (tanda 26), congeladas en futures/strategies/v27.json.
  ABE v1 : ABSORCIÓN CONFIRMADA POR ES — el mismo detector de ABU v1 (v17.py), pero solo se opera si ES también se detuvo: en los 120 s que
           terminan en la confirmación, ES no avanzó más de 2 ticks en la dirección del flujo agresivo absorbido (con al menos 20 operaciones de ES
           en la ventana). Si ES sí avanzó (NQ aguanta solo), no hay operación. ES es solo dato auxiliar; se opera NQ.
           Entrada, stop 12–32, objetivo 2R, salida a 15 min, 1 contrato, 09:30–15:30: idénticos a ABU v1.
           Motivo: ABU gana en días de balance pero pierde el 60% con el stop; una absorción que se ve en los dos índices es de todo el mercado
           (pasivos grandes) y no de un hueco local de NQ. Investigación y definición fijada antes de correr: docs/investigacion/absorcion_es.md.
"""
import os
import numpy as np
import polars as pl
from .. import config
from ..sim import Signal
from .v17 import PARAMS as P17, absorption_unified

PARAMS = {"ABE": {**P17["ABU"], "es_window_s": 120, "es_adv_max": 2, "es_min_prints": 20}}


def _es_day(date):
    """ES de la sesión 09:30–15:45 ET, contrato dominante. (sec ET absolutos, px en ticks de 0.25)."""
    p = os.path.join(config.DATA, "canonical", "ES", f"{date}.parquet")
    if not os.path.exists(p):
        return None
    df = pl.read_parquet(p, columns=["ts", "price_t", "volume", "contract"])
    et = df["ts"].dt.convert_time_zone(config.TZ)
    mins = et.dt.hour().cast(pl.Int32) * 60 + et.dt.minute().cast(pl.Int32)
    df = df.with_columns(mins.alias("m")).filter((pl.col("m") >= 570) & (pl.col("m") < 945))
    if not df.height:
        return None
    top = df.group_by("contract").agg(pl.col("volume").sum().alias("v")).sort("v", descending=True)["contract"][0]
    df = df.filter(pl.col("contract") == top)
    et = df["ts"].dt.convert_time_zone(config.TZ)
    sec = (et.dt.hour().cast(pl.Float64) * 3600 + et.dt.minute().cast(pl.Float64) * 60 + et.dt.second().cast(pl.Float64)
           + et.dt.nanosecond().cast(pl.Float64) / 1e9).to_numpy()
    return sec, df["price_t"].to_numpy().astype(np.int64)


def absorption_es(s, ref, thr, p=None):
    p = p or PARAMS["ABE"]
    base = absorption_unified(s, ref, thr, p)
    if not base:
        return []
    es = _es_day(s.date)
    if es is None:
        return []                      # sin ES no se puede confirmar: no se opera
    es_sec, es_px = es
    out = []
    for g in base:
        a = int(np.searchsorted(es_sec, g.sec - p["es_window_s"], side="left")); b = int(np.searchsorted(es_sec, g.sec, side="right"))
        if b - a < p["es_min_prints"]:
            continue
        sa = g.meta["side_absorbed"]
        adv = int((sa * (es_px[a:b] - es_px[a])).max())
        if adv > p["es_adv_max"]:
            continue                   # ES avanzó: la absorción es solo de NQ
        out.append(Signal(sec=g.sec, side=g.side, stop_ticks=g.stop_ticks, target_ticks=g.target_ticks, max_sec=g.max_sec, kind="ABE",
                          level=g.level, meta={**g.meta, "es_adv": adv}))
    return out


REGISTRY = {"ABE": absorption_es}
