"""Hoja de resultados de una prueba (estilo informe de backtest):
curva vs RAND, histograma por operación, ganancia diaria, 5 peores drawdowns, estadísticas móviles,
calor por hora y día de la semana, duraciones, MAE/MFE, por año, concentración, CPCV, Red Team, Topstep.
Escribe futures/lab/results/<id>/ {trades.csv, trades.json, report.json} y devuelve la ficha para tests.json.
"""
import csv, json, os
from datetime import date as _date
import numpy as np
from . import config, stats, regime
from .sim import sec_to_hms

DIAS = ["lun", "mar", "mié", "jue", "vie"]


def heat(trades):
    horas = list(range(9, 12)); z = [[0.0] * len(horas) for _ in DIAS]; n = [[0] * len(horas) for _ in DIAS]
    for t in trades:
        wd = _date.fromisoformat(t["date"]).weekday(); h = int(t["entry_sec"] // 3600)
        if wd < 5 and h in horas:
            z[wd][horas.index(h)] += t["net_usd"]; n[wd][horas.index(h)] += 1
    return {"horas": [f"{h}:00" for h in horas], "dias": DIAS, "neto": [[round(v, 0) for v in r] for r in z], "operaciones": n}


def hist(values, bins):
    c, e = np.histogram(values, bins=bins)
    return {"bins": np.round(e, 1).tolist(), "counts": c.tolist()}


def build(test_id, meta, trades, sessions, daily, rand_sum, topstep_sum, redteam, extra):
    out_dir = os.path.join(config.RESULTS, test_id); os.makedirs(out_dir, exist_ok=True)
    tr = sorted(trades, key=lambda t: (t["date"], t["entry_sec"]))
    cols = ["date", "kind", "level", "side", "entry_hms", "entry_px", "exit_hms", "exit_px", "reason", "pnl_ticks",
            "gross_usd", "commission_usd", "net_usd", "mae_ticks", "mfe_ticks", "duration_s", "stop_ticks", "target_ticks"]
    rows = []
    for t in tr:
        r = dict(t); r["entry_hms"] = sec_to_hms(t["entry_sec"]); r["exit_hms"] = sec_to_hms(t["exit_sec"]); rows.append(r)
    with open(os.path.join(out_dir, "trades.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore"); w.writeheader(); w.writerows(rows)
    json.dump([{k: r[k] for k in cols + ["meta"]} for r in rows], open(os.path.join(out_dir, "trades.json"), "w"), ensure_ascii=False)
    sm = stats.summary(tr, daily, sessions)
    net = [t["net_usd"] for t in tr]
    hoja = {
        "hist_operacion": hist(net, 24) if net else None,
        "diario": {"x": sessions, "y": np.round(daily, 2).tolist()},
        "drawdowns": sm["drawdowns"], "drawdown_max": sm["drawdown_max"],
        "movil_20": stats.rolling(daily, 20),
        "calor": heat(tr),
        "duracion": hist([t["duration_s"] / 60 for t in tr], [0, 1, 2, 3, 5, 8, 10, 15, 20, 30]) if tr else None,
        "mae_mfe": {"mae_prom": round(float(np.mean([t["mae_ticks"] for t in tr])), 1) if tr else None,
                    "mfe_prom": round(float(np.mean([t["mfe_ticks"] for t in tr])), 1) if tr else None,
                    "puntos": [[t["mae_ticks"], t["mfe_ticks"], t["net_usd"]] for t in tr[:2000]]},
        "salidas": {k: sum(1 for t in tr if t["reason"] == k) for k in ("objetivo", "stop", "tiempo", "cierre")},
        "por_anio": sm["por_anio"], "concentracion": sm["concentracion"], "cpcv": sm["cpcv"],
        "por_nivel": _by(tr, "level"), "por_lado": _by(tr, "side"), "por_regimen": regime.by_regime(tr),
        "red_team": redteam, "topstep": topstep_sum, "rand": {k: v for k, v in rand_sum.items() if not k.startswith("rand_p")},
        **extra,
    }
    cum = np.cumsum(daily)
    ficha = {
        "id": test_id, **meta,
        "resultados": {"operaciones": sm["operaciones"], "ganancia_neta": sm["ganancia_neta"], "aciertos": sm["aciertos_pct"],
                       "factor": sm["factor"], "vs_rand": rand_sum.get("p_valor"), "topstep": topstep_sum.get("pct_pasan"),
                       "sharpe_anual": sm["sharpe_anual"], "psr": sm["psr"], "drawdown_max": sm["drawdown_max"],
                       "promedio_op": sm["promedio_op"], "sesiones_con_operacion": sm["sesiones_con_operacion"]},
        "curva": {"x": sessions, "y": np.round(cum, 2).tolist(), "rand_p5": rand_sum.get("rand_p5"), "rand_p95": rand_sum.get("rand_p95")},
        "hoja": hoja,
        "archivos": {"trades_csv": f"data/tests/{test_id}/trades.csv", "trades_json": f"data/tests/{test_id}/trades.json",
                     "report_json": f"data/tests/{test_id}/report.json"},
    }
    json.dump(ficha, open(os.path.join(out_dir, "report.json"), "w"), ensure_ascii=False)
    return ficha


def _by(tr, key):
    out = {}
    for t in tr:
        k = str(t.get(key)); o = out.setdefault(k, {"operaciones": 0, "neto": 0.0})
        o["operaciones"] += 1; o["neto"] += t["net_usd"]
    for o in out.values():
        o["neto"] = round(o["neto"], 2)
    return out


def publish(ficha):
    """Agrega (o reemplaza por id) la ficha en futures/tests.json. La hoja completa queda en results/."""
    p = os.path.join(config.FUT, "tests.json")
    d = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {"pruebas": []}
    light = {k: v for k, v in ficha.items() if k != "hoja"}
    light["hoja_resumen"] = {k: ficha["hoja"].get(k) for k in ("salidas", "por_anio", "concentracion", "cpcv", "topstep", "rand", "drawdown_max", "por_regimen", "ojos_de_oscar")}
    d["pruebas"] = [t for t in d["pruebas"] if t["id"] != ficha["id"]] + [light]
    json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
