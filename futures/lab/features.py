"""
Medidas básicas por sesión del laboratorio NQ (solo lectura del canónico).

Por sesión y por tramo (asia, londres, ny, post; horario de Nueva York):
  - perfil de volumen por nivel: compra, venta, total y delta
  - POC, VAH, VAL (área de valor del 70%, expansión contigua desde el POC)
  - VWAP del tramo, máximo, mínimo, volumen y delta
  - órdenes agresivas agrupadas por trade_id (las "big trades" candidatas)
Salidas:
  features/profile/NQ/<fecha>.parquet   perfil por tramo y nivel
  features/orders/NQ/<fecha>.parquet    órdenes agrupadas de 10+ contratos
  features/summary_NQ.jsonl             resumen por sesión y tramo
Precios en ticks enteros (precio * 4).
"""
import os, json, sys
from concurrent.futures import ProcessPoolExecutor
import polars as pl

ROOT = os.environ.get("LAB_ROOT", "NQ")
CAN = f"/srv/lab/data/canonical/{ROOT}"
TICK = {"NQ": 4, "ES": 4, "YM": 1}[ROOT]
F = "/srv/lab/data/features"
TZ = "America/New_York"
THRESH = [20, 30, 50, 70, 80, 100, 150, 200]


def segment(col):
    t = col.dt.hour().cast(pl.Int32) * 60 + col.dt.minute().cast(pl.Int32)
    return (pl.when((t >= 570) & (t < 960)).then(pl.lit("ny"))
            .when((t >= 120) & (t < 570)).then(pl.lit("londres"))
            .when((t >= 960) & (t < 1020)).then(pl.lit("post"))
            .otherwise(pl.lit("asia")))


def value_area(prof, frac=0.70):
    p = prof.sort("price_t")
    px, v = p["price_t"].to_list(), p["vol"].to_list()
    if not v:
        return None, None, None
    i = max(range(len(v)), key=lambda k: v[k])
    lo = hi = i
    acc, tot = v[i], sum(v)
    while acc < frac * tot and (lo > 0 or hi < len(v) - 1):
        up = v[hi + 1] if hi < len(v) - 1 else -1
        dn = v[lo - 1] if lo > 0 else -1
        if up >= dn:
            hi += 1; acc += up
        else:
            lo -= 1; acc += dn
    return px[i], px[hi], px[lo]


def one(d):
    df = pl.read_parquet(os.path.join(CAN, f"{d}.parquet"))
    df = df.with_columns(pl.col("ts").dt.convert_time_zone(TZ).alias("et"))
    df = df.with_columns(segment(pl.col("et")).alias("seg"))
    prof = (df.group_by(["seg", "price_t"]).agg(
        pl.col("volume").filter(pl.col("side") == 1).sum().alias("buy"),
        pl.col("volume").filter(pl.col("side") == -1).sum().alias("sell"),
        pl.col("volume").sum().alias("vol"))
        .with_columns((pl.col("buy") - pl.col("sell")).alias("delta"))
        .sort(["seg", "price_t"]))
    prof.write_parquet(os.path.join(F, "profile", ROOT, f"{d}.parquet"), compression="zstd")
    orders = (df.group_by("trade_id").agg(
        pl.col("ts").first(), pl.col("et").first(), pl.col("seg").first(),
        pl.col("side").first(), pl.col("price_t").first().alias("px_first"),
        pl.col("price_t").last().alias("px_last"), pl.col("volume").sum().alias("size"),
        pl.col("price_t").n_unique().alias("levels"))
        .sort("ts"))
    orders.filter(pl.col("size") >= 10).drop("et").write_parquet(
        os.path.join(F, "orders", ROOT, f"{d}.parquet"), compression="zstd")
    recs = []
    for seg in ["asia", "londres", "ny", "post"]:
        s = df.filter(pl.col("seg") == seg)
        if s.height == 0:
            continue
        p = prof.filter(pl.col("seg") == seg)
        poc, vah, val = value_area(p)
        o = orders.filter(pl.col("seg") == seg)
        recs.append({
            "date": d, "seg": seg, "contract": str(s["contract"][0]),
            "start_et": str(s["et"][0])[:19], "end_et": str(s["et"][-1])[:19],
            "volume": int(s["volume"].sum()),
            "delta": int((s["volume"].cast(pl.Int64) * s["side"].cast(pl.Int64)).sum()),
            "high_t": int(s["price_t"].max()), "low_t": int(s["price_t"].min()),
            "open_t": int(s["price_t"][0]), "close_t": int(s["price_t"][-1]),
            "vwap": float((s["price_t"].cast(pl.Float64) * s["volume"].cast(pl.Float64)).sum() / s["volume"].sum() / TICK),
            "poc_t": poc, "vah_t": vah, "val_t": val,
            "orders": o.height,
            "big": {str(k): int((o["size"] >= k).sum()) for k in THRESH},
            "max_order": int(o["size"].max()),
        })
    return recs


def main():
    for sub in [f"profile/{ROOT}", f"orders/{ROOT}"]:
        os.makedirs(os.path.join(F, sub), exist_ok=True)
    days = sys.argv[1:] or sorted(f[:-8] for f in os.listdir(CAN) if f.endswith(".parquet"))
    out = os.path.join(F, f"summary_{ROOT}.jsonl" if not sys.argv[1:] else "summary_test.jsonl")
    n = 0
    with ProcessPoolExecutor(max_workers=6) as ex, open(out, "w") as f:
        for recs in ex.map(one, days):
            for r in recs:
                f.write(json.dumps(r) + "\n")
            n += 1
    print(f"FEATURES_DONE {n} sesiones -> {out}", flush=True)


if __name__ == "__main__":
    main()
