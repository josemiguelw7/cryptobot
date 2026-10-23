"""Carga de una sesión canónica como arreglos numpy, en hora de Nueva York.

Session.t      : int64, nanosegundos UTC
Session.sec    : float64, segundos desde la medianoche ET (09:30 = 34200)
Session.px     : int32, precio en ticks (precio*4)
Session.vol    : int32, contratos de la operación
Session.side   : int8, +1 compra agresiva, -1 venta agresiva
Session.bid/ask: int32, mejor compra/venta en ticks DESPUÉS de la operación
Session.bsz/asz: int32, tamaño del libro en mejor compra/venta después de la operación
Session.tid    : int64, trade_id (orden agresiva; una orden puede partirse en varios llenados)
"""
import os
from functools import lru_cache
import numpy as np
import polars as pl
from . import config

NY_OPEN, NY_CLOSE = 34200.0, 57600.0   # 09:30 y 16:00 ET en segundos


class Session:
    __slots__ = ("date", "contract", "t", "sec", "px", "vol", "side", "bid", "ask", "bsz", "asz", "tid", "n")

    def __init__(self, date, df):
        self.date = date
        self.contract = str(df["contract"][0]) if df.height else "?"
        et = df["ts"].dt.convert_time_zone(config.TZ)
        self.t = df["ts"].cast(pl.Int64).to_numpy()
        self.sec = (et.dt.hour().cast(pl.Float64) * 3600 + et.dt.minute().cast(pl.Float64) * 60
                    + et.dt.second().cast(pl.Float64) + et.dt.nanosecond().cast(pl.Float64) / 1e9).to_numpy()
        self.px = df["price_t"].to_numpy()
        self.vol = df["volume"].to_numpy()
        self.side = df["side"].to_numpy()
        self.bid = df["bid_after_t"].to_numpy()
        self.ask = df["ask_after_t"].to_numpy()
        self.bsz = df["bid_size_after"].to_numpy()
        self.asz = df["ask_size_after"].to_numpy()
        self.tid = df["trade_id"].to_numpy()
        self.n = len(self.px)

    def idx_sec(self, s):
        """Primer índice con sec >= s (la sesión no cruza medianoche en la ventana NY)."""
        return int(np.searchsorted(self.sec, s, side="left"))

    def idx_t(self, t_ns):
        return int(np.searchsorted(self.t, t_ns, side="left"))

    def window(self, s0, s1):
        i, j = self.idx_sec(s0), self.idx_sec(s1)
        return i, j

    def price_at(self, s):
        """Último precio operado en o antes del segundo s (None si no hay)."""
        i = int(np.searchsorted(self.sec, s, side="right")) - 1
        return int(self.px[i]) if i >= 0 else None


@lru_cache(maxsize=640)   # ~20 MB por sesión NY; la VM tiene 32 GB: se carga cada sesión una sola vez
def load(date, ny_only=False):
    p = os.path.join(config.CAN, f"{date}.parquet")
    df = pl.read_parquet(p)
    if ny_only:
        et = df["ts"].dt.convert_time_zone(config.TZ)
        mins = et.dt.hour().cast(pl.Int32) * 60 + et.dt.minute().cast(pl.Int32)
        df = df.filter((mins >= 570) & (mins < 960))
    return Session(date, df)


def ny_slice(s):
    """Índices [i, j) de la ventana 09:30-16:00 ET."""
    return s.idx_sec(NY_OPEN), s.idx_sec(NY_CLOSE)
