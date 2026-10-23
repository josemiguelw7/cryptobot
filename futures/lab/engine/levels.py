"""Niveles de referencia y umbrales en percentiles. Todo viene SOLO del pasado.

Por sesión d (en orden de la lista congelada):
  prev   : POC, VAH, VAL, máximo y mínimo del perfil de Nueva York del día válido anterior
  night  : máximo y mínimo de la noche (18:00 del día anterior a 09:30 ET) = tramos asia+londres de d
  umbrales(d): percentiles de órdenes y de ventanas de 60 s sobre las 20 sesiones válidas anteriores

Estadísticas por sesión (precompute_stats) se guardan en FEAT/lab_stats_NQ.jsonl:
  n_orders, top_orders: órdenes agresivas NY de 10+ contratos (agrupadas por trade_id); se guardan las 600 mayores
  n_all: cuántas órdenes de cualquier tamaño hubo (solo informativo)
  n_win, top_buy60, top_sell60: 500 mayores volúmenes agresivos por lado en ventanas de 60 s (paso 10 s)
Población de los percentiles de órdenes: órdenes de 10+ contratos (aclaración registrada en strategies/v1_aclaraciones.json).
El percentil agrupado es exacto mientras el rango pedido quede dentro de lo guardado; pooled_quantile avisa si no.
"""
import json, os
from concurrent.futures import ProcessPoolExecutor
import numpy as np
import polars as pl
from . import config

STATS = os.path.join(config.FEAT, "lab_stats_NQ.jsonl")
SUMMARY = os.path.join(config.FEAT, "summary_NQ.jsonl")
LOOKBACK = 20


def _session_stats(d):
    df = pl.read_parquet(os.path.join(config.CAN, f"{d}.parquet"), columns=["ts", "trade_id", "price_t", "volume", "side"])
    et = df["ts"].dt.convert_time_zone(config.TZ)
    mins = et.dt.hour().cast(pl.Int32) * 60 + et.dt.minute().cast(pl.Int32)
    ny = df.filter((mins >= 570) & (mins < 960))
    orders = ny.group_by("trade_id").agg(pl.col("volume").sum().alias("size"), pl.col("price_t").n_unique().alias("levels"))
    all_sizes = orders["size"].to_numpy()
    sizes = np.sort(all_sizes[all_sizes >= 10])[::-1]
    sec = (ny["ts"].cast(pl.Int64).to_numpy() // 1_000_000_000).astype(np.int64)
    sec = sec - sec.min() if len(sec) else sec
    buy = np.where(ny["side"].to_numpy() > 0, ny["volume"].to_numpy(), 0)
    sell = np.where(ny["side"].to_numpy() < 0, ny["volume"].to_numpy(), 0)
    nb = int(sec.max() // 10) + 1 if len(sec) else 0
    b10 = np.bincount((sec // 10).astype(int), weights=buy, minlength=nb)
    s10 = np.bincount((sec // 10).astype(int), weights=sell, minlength=nb)
    k = np.ones(6)
    b60 = np.convolve(b10, k, mode="valid") if nb >= 6 else b10
    s60 = np.convolve(s10, k, mode="valid") if nb >= 6 else s10
    return {"date": d, "n_orders": int(len(sizes)), "n_all": int(len(all_sizes)), "top_orders": sizes[:600].tolist(),
            "n_win": int(len(b60)), "top_buy60": np.sort(b60)[::-1][:500].tolist(),
            "top_sell60": np.sort(s60)[::-1][:500].tolist()}


def precompute_stats(dates, workers=6):
    done = set()
    if os.path.exists(STATS):
        done = {json.loads(l)["date"] for l in open(STATS)}
    todo = [d for d in dates if d not in done]
    import multiprocessing
    with ProcessPoolExecutor(max_workers=workers, mp_context=multiprocessing.get_context("spawn")) as ex, open(STATS, "a") as f:
        for rec in ex.map(_session_stats, todo):
            f.write(json.dumps(rec) + "\n")
    return len(todo)


def pooled_quantile(tops, ns, q):
    """Percentil q (0-1) de la unión de varias distribuciones de las que solo se guardaron
    los mayores valores. Exacto mientras el rango pedido quede dentro de lo guardado."""
    allv = np.sort(np.concatenate([np.asarray(t, dtype=float) for t in tops]))[::-1]
    N = int(sum(ns))
    rank = int(np.floor((1 - q) * N))
    if rank >= len(allv):
        raise ValueError(f"percentil {q} fuera de lo guardado: rango {rank} >= {len(allv)}; hay que guardar más valores por sesión")
    return float(allv[rank])


class Levels:
    def __init__(self, dates):
        """dates: lista congelada (orden cronológico). Solo se usan como 'anteriores' las de la lista."""
        self.dates = list(dates)
        self.pos = {d: i for i, d in enumerate(self.dates)}
        self.summ = {}
        for l in open(SUMMARY):
            r = json.loads(l)
            self.summ.setdefault(r["date"], {})[r["seg"]] = r
        self.stats = {}
        if os.path.exists(STATS):
            for l in open(STATS):
                r = json.loads(l); self.stats[r["date"]] = r

    def prev_date(self, d):
        i = self.pos.get(d)
        return self.dates[i - 1] if i else None

    def reference(self, d):
        """Niveles en ticks. None si falta el día anterior."""
        p = self.prev_date(d)
        if p is None or "ny" not in self.summ.get(p, {}):
            return None
        ny = self.summ[p]["ny"]
        cur = self.summ.get(d, {})
        night = [cur[k] for k in ("asia", "londres") if k in cur]
        out = {"prev_poc": ny["poc_t"], "prev_vah": ny["vah_t"], "prev_val": ny["val_t"],
               "prev_high": ny["high_t"], "prev_low": ny["low_t"]}
        if night:
            out["night_high"] = max(x["high_t"] for x in night)
            out["night_low"] = min(x["low_t"] for x in night)
        return out

    def thresholds(self, d, lookback=LOOKBACK):
        i = self.pos.get(d)
        if i is None or i < lookback:
            return None
        prev = [self.stats.get(x) for x in self.dates[i - lookback:i]]
        if any(p is None for p in prev):
            return None
        return {
            "order_p99": pooled_quantile([p["top_orders"] for p in prev], [p["n_orders"] for p in prev], 0.99),
            "order_p95": pooled_quantile([p["top_orders"] for p in prev], [p["n_orders"] for p in prev], 0.95),
            "buy60_p95": pooled_quantile([p["top_buy60"] for p in prev], [p["n_win"] for p in prev], 0.95),
            "sell60_p95": pooled_quantile([p["top_sell60"] for p in prev], [p["n_win"] for p in prev], 0.95),
            "buy60_p99": pooled_quantile([p["top_buy60"] for p in prev], [p["n_win"] for p in prev], 0.99),
            "sell60_p99": pooled_quantile([p["top_sell60"] for p in prev], [p["n_win"] for p in prev], 0.99),
        }

    def open_in_value(self, d):
        """¿La apertura de las 09:30 cae dentro del área de valor del día anterior?"""
        r = self.reference(d); cur = self.summ.get(d, {}).get("ny")
        if not r or not cur:
            return None
        return r["prev_val"] <= cur["open_t"] <= r["prev_vah"]
