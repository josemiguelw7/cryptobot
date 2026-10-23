"""
Exporta un día (tramo Nueva York por defecto) a JSON liviano para el explorador web.
  precio: último precio cada 5 s, VWAP acumulado del tramo, delta acumulado
  perfil: volumen compra/venta por nivel del tramo, POC/VAH/VAL
  big: órdenes agresivas agrupadas de 70+ contratos (hora, lado, precio, tamaño, niveles)
Uso: python export_day.py 2025-02-27 [seg] > salida.json
"""
import json, sys
import polars as pl
sys.path.insert(0, "/srv/lab/repo/lab")
from features import segment, value_area

d = sys.argv[1]
seg = sys.argv[2] if len(sys.argv) > 2 else "ny"
df = pl.read_parquet(f"/srv/lab/data/canonical/NQ/{d}.parquet")
df = df.with_columns(pl.col("ts").dt.convert_time_zone("America/New_York").alias("et"))
df = df.with_columns(segment(pl.col("et")).alias("seg")).filter(pl.col("seg") == seg)
df = df.with_columns(
    (pl.col("price_t").cast(pl.Float64) * pl.col("volume")).cum_sum().alias("pv"),
    pl.col("volume").cast(pl.Int64).cum_sum().alias("cv"),
    (pl.col("volume").cast(pl.Int64) * pl.col("side").cast(pl.Int64)).cum_sum().alias("cd"),
)
bars = (df.group_by_dynamic("et", every="5s").agg(
    pl.col("price_t").last().alias("p"), pl.col("pv").last(), pl.col("cv").last(),
    pl.col("cd").last().alias("cd"))
    .with_columns((pl.col("pv") / pl.col("cv") / 4).round(2).alias("vwap")))
prof = (df.group_by("price_t").agg(
    pl.col("volume").filter(pl.col("side") == 1).sum().alias("buy"),
    pl.col("volume").filter(pl.col("side") == -1).sum().alias("sell"),
    pl.col("volume").sum().alias("vol")).sort("price_t"))
poc, vah, val = value_area(prof)
orders = (df.group_by("trade_id").agg(
    pl.col("et").first(), pl.col("side").first(), pl.col("price_t").first().alias("px"),
    pl.col("volume").sum().alias("size"), pl.col("price_t").n_unique().alias("lv"))
    .filter(pl.col("size") >= 70).sort("et"))
out = {
    "date": d, "seg": seg, "contract": str(df["contract"][0]),
    "t": bars["et"].dt.strftime("%H:%M:%S").to_list(),
    "p": [x / 4 for x in bars["p"].to_list()],
    "vwap": bars["vwap"].to_list(), "cd": bars["cd"].to_list(),
    "prof": {"px": [x / 4 for x in prof["price_t"].to_list()], "buy": prof["buy"].to_list(),
             "sell": prof["sell"].to_list()},
    "poc": poc / 4, "vah": vah / 4, "val": val / 4,
    "big": {"t": orders["et"].dt.strftime("%H:%M:%S").to_list(), "side": orders["side"].to_list(),
            "px": [x / 4 for x in orders["px"].to_list()], "size": orders["size"].to_list(),
            "lv": orders["lv"].to_list()},
    "stats": {"volume": int(df["volume"].sum()), "delta": int(df["cd"][-1]),
              "open": df["price_t"][0] / 4, "high": df["price_t"].max() / 4,
              "low": df["price_t"].min() / 4, "close": df["price_t"][-1] / 4,
              "vwap": round(float(df["pv"][-1] / df["cv"][-1] / 4), 2)},
}
print(json.dumps(out, separators=(",", ":")))
