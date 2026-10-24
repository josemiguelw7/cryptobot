"""Cifras para el Formato Estándar de Reportes — Trading Floor (Oscar Lab).
Lee una prueba ya corrida (results/<ID>) y calcula las secciones 5-8, incluido Topstep $50K
con DLL $1,000 y sin DLL. No modifica el motor: el escenario sin DLL se obtiene subiendo
el DLL a infinito en una copia en memoria del módulo topstep.
Uso: .venv/bin/python futures/lab/reporte_floor.py P012
"""
import csv, json, os, sys, copy
from collections import defaultdict
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from engine import topstep  # noqa: E402


def load(tid):
    base = os.path.join(HERE, "results", tid)
    rep = json.load(open(os.path.join(base, "report.json"), encoding="utf-8"))
    rows = list(csv.DictReader(open(os.path.join(base, "trades.csv"), encoding="utf-8")))
    trades = []
    for r in rows:
        h, m, s = r["entry_hms"].split(":")
        trades.append({"date": r["date"], "entry_sec": int(h) * 3600 + int(m) * 60 + float(s),
                       "net_usd": float(r["net_usd"]), "mae_ticks": float(r["mae_ticks"]),
                       "commission_usd": float(r["commission_usd"]), "contracts": 1,
                       "stop_ticks": float(r["stop_ticks"]), "target_ticks": float(r["target_ticks"]),
                       "reason": r["reason"]})
    return rep, trades


def extremes(trades):
    day, week, month = defaultdict(float), defaultdict(float), defaultdict(float)
    for t in trades:
        d = date.fromisoformat(t["date"]); iso = d.isocalendar()
        day[t["date"]] += t["net_usd"]
        week[f"{iso[0]}-W{iso[1]:02d}"] += t["net_usd"]
        month[t["date"][:7]] += t["net_usd"]
    pick = lambda g: {"mejor": max(g.items(), key=lambda kv: kv[1]), "peor": min(g.items(), key=lambda kv: kv[1])}
    return {"mes": pick(month), "semana": pick(week), "dia": pick(day)}


def topstep_eval(trades, sessions, consistency, with_dll):
    old = topstep.DLL
    topstep.DLL = old if with_dll else float("inf")
    try:
        accts = topstep.run_all(trades, sessions, consistency=consistency)
        first = topstep.run_account(sessions, topstep._daily_paths(trades), consistency, max_days=10**6)
    finally:
        topstep.DLL = old
    s = topstep.summarize(accts)
    s["primera_cuenta"] = first
    return s


def main(tid):
    rep, trades = load(tid)
    sessions = rep["hoja"]["diario"]["x"]
    eq, peak, mdd = 0.0, 0.0, 0.0
    for t in sorted(trades, key=lambda x: (x["date"], x["entry_sec"])):
        eq += t["net_usd"]; peak = max(peak, eq); mdd = min(mdd, eq - peak)
    wins = sum(1 for t in trades if t["net_usd"] > 0)
    out = {
        "id": tid, "estrategia": rep["estrategia"], "version": rep["version"], "periodo": rep["periodo"],
        "costos": rep["receta"]["costos"], "parametros": rep["receta"]["parametros"],
        "desde": sessions[0], "hasta": sessions[-1], "sesiones": len(sessions),
        "trades": len(trades), "win_rate": round(100 * wins / len(trades), 1),
        "neto": round(eq, 2), "max_dd": round(mdd, 2), "trades_dia": round(len(trades) / len(sessions), 2),
        "razones_salida": {k: sum(1 for t in trades if t["reason"] == k) for k in sorted({t["reason"] for t in trades})},
        "extremos": extremes(trades),
        "topstep": {f"{'con' if dll else 'sin'}_dll_{int(c*100)}": topstep_eval(trades, sessions, c, dll)
                    for dll in (True, False) for c in (0.50, 0.55)},
        "veredicto_lab": rep["veredicto"], "motivos_lab": rep.get("muerte"), "intentos_totales": rep.get("intentos_totales"),
        "dsr": rep.get("dsr"), "vs_rand": rep["resultados"].get("vs_rand"), "estres": rep.get("estres"),
    }
    print(json.dumps(out, ensure_ascii=False, indent=1, default=str))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "P012")
