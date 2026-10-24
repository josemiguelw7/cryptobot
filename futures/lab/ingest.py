"""
Lector canónico del laboratorio NQ.
raw/NQ/<fecha>.csv.gz (ATAS, una fila por llenado) -> canonical/NQ/<fecha>.parquet

Cada sesión se valida contra el manifiesto (filas, volumen, compra y venta)
antes de escribirse. Si algo no cuadra, la sesión no se escribe y queda en el log.
Precios en ticks enteros (precio * 4) para evitar errores de coma flotante.
"""
import csv, json, os, sys, time
from concurrent.futures import ProcessPoolExecutor
import polars as pl

import os
ROOT = os.environ.get("LAB_ROOT", "NQ")                 # NQ | ES | YM
RAW = f"/srv/lab/data/raw/{ROOT}"
OUT = f"/srv/lab/data/canonical/{ROOT}"
TICKS_PER_POINT = {"NQ": 4, "ES": 4, "YM": 1}            # NQ/ES: tick 0.25; YM: tick 1.0
LOG = "/srv/lab/logs/ingest.jsonl"
TICK = TICKS_PER_POINT[ROOT]  # precios en ticks enteros

PX = ["price", "bid_before", "ask_before", "bid_after", "ask_after"]
SZ = ["volume", "trade_volume", "ticks_swept", "ticks_in_order",
      "bid_size_before", "ask_size_before", "bid_size_after", "ask_size_after"]


def manifest():
    with open(os.path.join(RAW, "_manifest.csv")) as f:
        return {r["trade_date"]: r for r in csv.DictReader(f) if r["status"] == "OK"}


def one(args):
    d, m = args
    t0 = time.time()
    src = os.path.join(RAW, f"{d}.csv.gz")
    dst = os.path.join(OUT, f"{d}.parquet")
    df = pl.read_csv(src, infer_schema_length=0)  # todo como texto, casteo explícito
    types = df["data_type"].unique().to_list()
    sides = df["side"].unique().to_list()
    df = df.filter(pl.col("data_type") == "Trade")
    out = df.select(
        pl.col("time_utc").str.to_datetime("%Y-%m-%d %H:%M:%S%.f", time_unit="ns",
                                            time_zone="UTC").alias("ts"),
        pl.col("trade_id").cast(pl.Int64),
        *[(pl.col(c).cast(pl.Float64) * TICK).round(0).cast(pl.Int32).alias(c + "_t") for c in PX],
        *[pl.col(c).cast(pl.Int32) for c in SZ],
        pl.when(pl.col("side") == "Buy").then(1).when(pl.col("side") == "Sell").then(-1)
          .otherwise(0).cast(pl.Int8).alias("side"),
        pl.col("contract").cast(pl.Categorical),
    )
    vol = int(out["volume"].sum())
    buy = int(out.filter(pl.col("side") == 1)["volume"].sum())
    sell = int(out.filter(pl.col("side") == -1)["volume"].sum())
    chk = {
        "rows": (out.height, int(m["ticks"])),
        "volume": (vol, int(m["volume"])),
        "buy": (buy, int(m["buy_volume"])),
        "sell": (sell, int(m["sell_volume"])),
    }
    ok = all(a == b for a, b in chk.values()) and out["ts"].is_sorted()
    rec = {"date": d, "ok": ok, "checks": chk, "types": types, "sides": sides,
           "contract": m["contract"], "sec": round(time.time() - t0, 1)}
    if ok:
        tmp = dst + ".tmp"
        out.write_parquet(tmp, compression="zstd", statistics=True)
        os.replace(tmp, dst)
    return rec


def main():
    os.makedirs(OUT, exist_ok=True)
    m = manifest()
    only = sys.argv[1:]
    todo = [(d, m[d]) for d in sorted(m) if (not only or d in only)
            and not os.path.exists(os.path.join(OUT, f"{d}.parquet"))]
    n_ok = n_bad = 0
    with ProcessPoolExecutor(max_workers=6) as ex, open(LOG, "a") as log:
        for rec in ex.map(one, todo):
            log.write(json.dumps(rec) + "\n"); log.flush()
            n_ok += rec["ok"]; n_bad += not rec["ok"]
            if not rec["ok"]:
                print("NO CUADRA", rec["date"], rec["checks"], flush=True)
    print(f"INGEST_DONE ok={n_ok} fallidas={n_bad} de {len(todo)}", flush=True)


if __name__ == "__main__":
    main()
