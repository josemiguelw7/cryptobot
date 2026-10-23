"""
Auditoría de sesiones del laboratorio NQ -> lista congelada de sesiones válidas.

Por cada sesión canónica mide, SOLO en la ventana de Nueva York 09:30-16:00 ET:
  - hueco máximo entre operaciones (segundos) y cuántos huecos >= 30 s
  - hora UTC de la primera operación >= 09:30 ET (prueba de horario de verano)
  - contrato, día de rollo (rolled_from en el manifiesto), operaciones y volumen
Clasifica:
  ok            entra a las pruebas
  aviso         entra, pero con hueco de 60-120 s en NY (se publica)
  excluida      hueco >= 120 s en NY, o día de rollo sin el segundo contrato
Salida: futures/sessions_manifest.json (se congela con SHA-256 + OTS)
Uso (en la VM): /srv/lab/.venv/bin/python sessions_audit.py > sessions_manifest.json
"""
import csv, json, os, sys, hashlib
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timezone
import polars as pl

CAN = "/srv/lab/data/canonical/NQ"
MAN = "/srv/lab/data/raw/NQ/_manifest.csv"
TZ = "America/New_York"
DESIGN_END = "2026-04-21"
GAP_WARN, GAP_EXCL = 60.0, 120.0
ROLL_DAYS = ["2024-03-11", "2024-06-17", "2024-09-16", "2024-12-16", "2025-03-17",
             "2025-06-16", "2025-09-15", "2025-12-15", "2026-03-16", "2026-06-15", "2026-09-14"]


def one(d):
    df = pl.read_parquet(os.path.join(CAN, f"{d}.parquet"), columns=["ts", "volume", "contract", "price_t"])
    et = df["ts"].dt.convert_time_zone(TZ)
    mins = et.dt.hour().cast(pl.Int32) * 60 + et.dt.minute().cast(pl.Int32)
    ny = df.filter((mins >= 570) & (mins < 960))
    if ny.height < 100:
        return {"date": d, "ny_trades": ny.height, "ny_gap_max_s": None, "ny_gaps_30s": None,
                "clase": "excluida", "motivo": "sin datos en la ventana de Nueva York"}
    gaps = ny["ts"].diff().dt.total_milliseconds().drop_nulls() / 1000.0
    first_utc = ny["ts"][0]
    # DST: 09:30 ET = 13:30 UTC en verano, 14:30 UTC en invierno
    utc_min = first_utc.hour * 60 + first_utc.minute
    dst_ok = utc_min in (810, 811, 870, 871)  # 13:30/13:31 o 14:30/14:31
    rec = {"date": d, "contract": str(df["contract"][0]), "ny_trades": ny.height,
           "ny_volume": int(ny["volume"].sum()), "ny_gap_max_s": round(float(gaps.max()), 1),
           "ny_gaps_30s": int((gaps >= 30).sum()), "ny_first_utc": str(first_utc)[:19],
           "dst_ok": dst_ok,
           "ny_high": float(ny["price_t"].max()) / 4, "ny_low": float(ny["price_t"].min()) / 4}
    return rec


def main():
    man = {r["trade_date"]: r for r in csv.DictReader(open(MAN)) if r["status"] == "OK"}
    days = sorted(f[:-8] for f in os.listdir(CAN) if f.endswith(".parquet"))
    out = []
    with ProcessPoolExecutor(max_workers=6) as ex:
        for rec in ex.map(one, days):
            d = rec["date"]; m = man.get(d, {})
            rec["rollo"] = d in ROLL_DAYS or bool(m.get("rolled_from"))
            rec["rolled_from"] = m.get("rolled_from") or None
            rec["sha256_raw"] = m.get("sha256")
            rec["diseno"] = d <= DESIGN_END
            if rec.get("clase") == "excluida":
                pass
            elif rec["rollo"]:
                rec["clase"], rec["motivo"] = "excluida", "día de rollo: falta el segundo contrato (se reincorpora cuando se baje)"
            elif not rec.get("dst_ok", True):
                rec["clase"], rec["motivo"] = "excluida", f"primera operación NY a las {rec['ny_first_utc']} UTC: no cuadra con 09:30 ET"
            elif rec["ny_gap_max_s"] >= GAP_EXCL:
                rec["clase"], rec["motivo"] = "excluida", f"hueco de {rec['ny_gap_max_s']} s en Nueva York"
            elif rec["ny_gap_max_s"] >= GAP_WARN:
                rec["clase"], rec["motivo"] = "aviso", f"hueco de {rec['ny_gap_max_s']} s en Nueva York (entra, se publica)"
            else:
                rec["clase"], rec["motivo"] = "ok", ""
            out.append(rec)
    ok = [r for r in out if r["clase"] != "excluida"]
    design_ok = [r["date"] for r in ok if r["diseno"]]
    manifest = {
        "titulo": "Lista congelada de sesiones válidas del laboratorio NQ",
        "generado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "regla": "Solo entran a las pruebas las sesiones 'ok' y 'aviso'. Las excluidas se publican con su motivo. No se cambia después de ver resultados; una lista nueva es versión nueva.",
        "criterios": {"hueco_aviso_s": GAP_WARN, "hueco_excluye_s": GAP_EXCL, "ventana": "09:30-16:00 ET",
                       "rollos": "excluidos hasta tener el segundo contrato", "dst": "primera operación NY debe caer a las 13:30 o 14:30 UTC"},
        "resumen": {"total": len(out), "ok": sum(r["clase"] == "ok" for r in out), "aviso": sum(r["clase"] == "aviso" for r in out),
                     "excluidas": sum(r["clase"] == "excluida" for r in out), "diseno_validas": len(design_ok),
                     "dst_fallos": sum(not r.get("dst_ok", True) for r in out)},
        "sesiones_diseno_validas": design_ok,
        "sesiones_diseno_sha256": hashlib.sha256("\n".join(design_ok).encode()).hexdigest(),
        "detalle": out,
    }
    json.dump(manifest, sys.stdout, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
