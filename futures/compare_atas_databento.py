"""Compara una sesion tick de ATAS (ticks_gz/NQ/<fecha>.csv.gz) con el TBBO de
Databento del mismo dia, solo sobre la ventana que ambos cubren (00:00-21:00 UTC).
Uso: python compare_atas_databento.py <fecha> <contrato> <atas.csv.gz> <databento.csv.zst>
"""
import sys, io, gzip, zstandard
import polars as pl

day, contract, atas_path, db_path = sys.argv[1:5]
t0 = f"{day} 00:00:00"
t1 = f"{day} 21:00:00"

# --- ATAS ---------------------------------------------------------------
a = pl.read_csv(gzip.open(atas_path), infer_schema_length=0)
a = a.with_columns([
    pl.col("time_utc").str.slice(0, 26).str.strptime(pl.Datetime("us"), "%Y-%m-%d %H:%M:%S%.f").alias("ts"),
    pl.col("price").cast(pl.Float64), pl.col("volume").cast(pl.Int64),
    pl.col("ticks_in_order").cast(pl.Int64), pl.col("ticks_swept").cast(pl.Int64),
    pl.col("bid_before").cast(pl.Float64), pl.col("ask_before").cast(pl.Float64),
])
a = a.filter((pl.col("ts") >= pl.lit(t0).str.strptime(pl.Datetime("us"))) &
             (pl.col("ts") < pl.lit(t1).str.strptime(pl.Datetime("us"))))

# --- Databento ----------------------------------------------------------
raw = zstandard.ZstdDecompressor().stream_reader(open(db_path, "rb")).read()
d = pl.read_csv(io.BytesIO(raw), infer_schema_length=0)
d = d.with_columns([
    pl.col("ts_event").str.slice(0, 26).str.strptime(pl.Datetime("us"), "%Y-%m-%dT%H:%M:%S%.f").alias("ts"),
    pl.col("price").cast(pl.Float64), pl.col("size").cast(pl.Int64),
    pl.col("bid_px_00").cast(pl.Float64), pl.col("ask_px_00").cast(pl.Float64),
])
d_all = d.filter((pl.col("ts") >= pl.lit(t0).str.strptime(pl.Datetime("us"))) &
                 (pl.col("ts") < pl.lit(t1).str.strptime(pl.Datetime("us"))))
print("Databento volumen por simbolo en la ventana:",
      d_all.group_by("symbol").agg(pl.col("size").sum()).sort("size", descending=True).to_dicts())
d = d_all.filter(pl.col("symbol") == contract)

def summ(name, df, vol, buy):
    print(f"{name:10s} filas={df.height:>8,}  volumen={vol:>9,}  compra={buy:>9,}  "
          f"venta={vol-buy:>9,}  min={df['price'].min():.2f} max={df['price'].max():.2f}")

va = a["volume"].sum(); ba = a.filter(pl.col("side") == "Buy")["volume"].sum()
vd = d["size"].sum();  bd = d.filter(pl.col("side") == "B")["size"].sum()
print(f"\n== {day} {contract}  ventana {t0} -> {t1} UTC")
summ("ATAS", a, va, ba)
print(f"           ticks_in_order sum={a['ticks_in_order'].sum():,}")
summ("Databento", d, vd, bd)
print(f"\nDiferencia de volumen: {va-vd:+,} ({100*(va-vd)/vd:+.3f}%)   compra: {ba-bd:+,}   venta: {(va-ba)-(vd-bd):+,}")

# --- por minuto ---------------------------------------------------------
ma = a.group_by(pl.col("ts").dt.truncate("1m").alias("m")).agg([pl.col("volume").sum().alias("va"),
        pl.when(pl.col("side") == "Buy").then(pl.col("volume")).otherwise(0).sum().alias("ba")])
md = d.group_by(pl.col("ts").dt.truncate("1m").alias("m")).agg([pl.col("size").sum().alias("vd"),
        pl.when(pl.col("side") == "B").then(pl.col("size")).otherwise(0).sum().alias("bd")])
j = ma.join(md, on="m", how="full", coalesce=True).fill_null(0).sort("m")
j = j.with_columns([(pl.col("va") - pl.col("vd")).alias("dv"), (pl.col("ba") - pl.col("bd")).alias("db")])
exact = (j["dv"] == 0).sum(); exact_b = (j["db"] == 0).sum()
print(f"\nMinutos comparados: {j.height}  | volumen identico: {exact} ({100*exact/j.height:.1f}%)"
      f"  | compra identica: {exact_b} ({100*exact_b/j.height:.1f}%)")
print("Correlacion volumen/minuto:", round(float(__import__("numpy").corrcoef(j["va"].to_numpy(), j["vd"].to_numpy())[0,1]), 5))
worst = j.with_columns(pl.col("dv").abs().alias("adv")).sort("adv", descending=True).head(8)
print("Peores minutos (ATAS - Databento):")
print(worst.select(["m", "va", "vd", "dv", "ba", "bd", "db"]))

# --- libro antes de la operacion: comparar por segundo el primer registro --
sa = a.group_by(pl.col("ts").dt.truncate("1s").alias("s")).agg([pl.col("bid_before").first(), pl.col("ask_before").first()])
sd = d.group_by(pl.col("ts").dt.truncate("1s").alias("s")).agg([pl.col("bid_px_00").first(), pl.col("ask_px_00").first()])
k = sa.join(sd, on="s", how="inner")
okb = (k["bid_before"] == k["bid_px_00"]).mean(); oka = (k["ask_before"] == k["ask_px_00"]).mean()
print(f"\nLibro (primer trade de cada segundo, {k.height} segundos): bid igual {100*okb:.1f}%  ask igual {100*oka:.1f}%")
